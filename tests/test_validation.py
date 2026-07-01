import pytest
from pydantic import ValidationError
from app.api.routes.hospital import PatientOnboardingRequest, DailyVitalsRequest

def test_onboarding_request_valid_data():
    # Correct enums/Literals
    data = {
        "age": 35,
        "gender": "Male",
        "disease_type": "Cardiac",
        "smoking_status": "Never",
        "alcohol_consumption": "Moderate"
    }
    req = PatientOnboardingRequest(**data)
    assert req.gender == "Male"
    assert req.smoking_status == "Never"
    assert req.alcohol_consumption == "Moderate"

def test_onboarding_request_invalid_gender():
    data = {
        "age": 35,
        "gender": "InvalidGender",
        "disease_type": "Cardiac"
    }
    with pytest.raises(ValidationError):
        PatientOnboardingRequest(**data)

def test_onboarding_request_invalid_smoking():
    data = {
        "age": 35,
        "gender": "Male",
        "disease_type": "Cardiac",
        "smoking_status": "Occasionally"  # Not in Never, Former, Current
    }
    with pytest.raises(ValidationError):
        PatientOnboardingRequest(**data)

def test_onboarding_request_invalid_alcohol():
    data = {
        "age": 35,
        "gender": "Male",
        "disease_type": "Cardiac",
        "alcohol_consumption": "Socially"  # Not in None, Moderate, Heavy, Occasional
    }
    with pytest.raises(ValidationError):
        PatientOnboardingRequest(**data)

def test_daily_vitals_request_valid_data():
    data = {
        "heart_rate": 72,
        "medication_taken": "Yes",
        "exercise_completed": "No"
    }
    req = DailyVitalsRequest(**data)
    assert req.medication_taken == "Yes"
    assert req.exercise_completed == "No"

def test_daily_vitals_request_invalid_medication():
    data = {
        "medication_taken": "Sometimes"  # Not in Yes, No
    }
    with pytest.raises(ValidationError):
        DailyVitalsRequest(**data)

def test_daily_vitals_request_invalid_exercise():
    data = {
        "exercise_completed": "Maybe"  # Not in Yes, No
    }
    with pytest.raises(ValidationError):
        DailyVitalsRequest(**data)


from app.services.deviation_engine import DeviationEngine
from app.models.schemas import PatientRecord

def test_deviation_engine_calculations():
    # Construct a PatientRecord
    data = {
        "patient_id": "P001",
        "age": 45,
        "gender": "Male",
        "bmi": 24.5,
        "smoking_status": "Never",
        "alcohol_consumption": "None",
        "disease_type": "Cardiac",
        "heart_rate": 85,
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "spo2": 96.0,
        "respiratory_rate": 16,
        "body_temperature": 36.8,
        "expected_steps": 8000,
        "expected_sleep_hours": 8.0,
        "water_intake_goal": 2000,
        "actual_steps": 6000,
        "actual_sleep_hours": 7.0,
        "water_intake": 1500,
        "medication_taken": "No",
        "exercise_completed": "No",
        "diet_compliance": 80.0,
        "weight_kg": 75.0,
        "expected_weight": 73.0,
    }
    record = PatientRecord(**data)
    devs = DeviationEngine.calculate_deviations(record)
    
    assert devs["medication_deviation"] == 100.0
    assert devs["exercise_deviation"] == 100.0
    assert devs["sleep_deviation"] == pytest.approx(1.0)
    assert devs["water_deviation"] == pytest.approx(500.0)
    assert devs["heart_rate_deviation"] == pytest.approx(5.0)
    assert devs["bp_deviation"] == pytest.approx(15.0 + 10.0) # |120-105| + |80-70|
    assert devs["weight_deviation"] == pytest.approx(2.0)
    assert devs["spo2_deviation"] == pytest.approx(1.5)
    assert devs["temp_deviation"] == pytest.approx(0.15) # |36.8 - 36.65|

def test_deviation_engine_recommendations():
    data = {
        "patient_id": "P001",
        "age": 45,
        "gender": "Male",
        "bmi": 24.5,
        "smoking_status": "Never",
        "alcohol_consumption": "None",
        "disease_type": "Cardiac",
        "heart_rate": 85,
        "systolic_bp": 140, # High BP
        "diastolic_bp": 80,
        "spo2": 96.0,
        "respiratory_rate": 16,
        "body_temperature": 36.8,
        "expected_steps": 8000,
        "expected_sleep_hours": 8.0,
        "water_intake_goal": 2000,
        "actual_steps": 6000,
        "actual_sleep_hours": 6.5, # Low sleep (< 8.0 - 1.0 = 7.0 → triggers recommendation)
        "water_intake": 1500,
        "medication_taken": "No", # Missed
        "exercise_completed": "No",
        "diet_compliance": 80.0,
    }
    record = PatientRecord(**data)
    recs = DeviationEngine.generate_recommendations(record)
    
    # Check that personalized recommendations are generated
    assert any("Medication missed" in r for r in recs)
    assert any("Low Sleep" in r for r in recs)
    assert any("High Blood Pressure" in r for r in recs)

def test_deviation_engine_shap_reasons():
    data = {
        "patient_id": "P001",
        "age": 45,
        "gender": "Male",
        "bmi": 24.5,
        "smoking_status": "Never",
        "alcohol_consumption": "None",
        "disease_type": "Cardiac",
        "heart_rate": 95, # High HR
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "spo2": 93.0, # Low SpO2
        "respiratory_rate": 16,
        "body_temperature": 36.8,
        "expected_steps": 8000,
        "expected_sleep_hours": 8.0,
        "water_intake_goal": 2000,
        "actual_steps": 6000,
        "actual_sleep_hours": 8.0,
        "water_intake": 2000,
        "medication_taken": "Yes",
        "exercise_completed": "Yes",
        "diet_compliance": 100.0,
    }
    record = PatientRecord(**data)
    reasons = DeviationEngine.generate_shap_reasons(record)
    
    assert "Elevated Heart Rate" in reasons
    assert "Low SpO2 Level" in reasons
