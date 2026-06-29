"""
Unit tests for Pydantic schemas validation.

Tests Requirements 17.1, 17.2, 17.3, 17.4
"""

import pytest
from pydantic import ValidationError
from app.models.schemas import PatientRecord


class TestPatientRecordValidation:
    """Test suite for PatientRecord validation rules."""
    
    def test_valid_patient_record(self):
        """Test that a valid patient record is accepted."""
        valid_data = {
            "patient_id": "P001",
            "patient_name": "John Doe",
            "age": 65,
            "gender": "Male",
            "bmi": 28.5,
            "smoking_status": "Former",
            "alcohol_consumption": "Moderate",
            "disease_type": "Heart Failure",
            "heart_rate": 78,
            "systolic_bp": 130,
            "diastolic_bp": 85,
            "spo2": 96.5,
            "respiratory_rate": 16,
            "body_temperature": 36.8,
            "expected_steps": 5000,
            "expected_sleep_hours": 8.0,
            "water_intake_goal": 2000,
            "actual_steps": 4200,
            "actual_sleep_hours": 7.5,
            "water_intake": 1800,
            "medication_taken": "Yes",
            "exercise_completed": "Yes",
            "diet_compliance": 85.0,
            "day": 1
        }
        
        record = PatientRecord(**valid_data)
        assert record.patient_id == "P001"
        assert record.age == 65
        assert record.bmi == 28.5
    
    def test_age_validation_lower_bound(self):
        """Test that age < 0 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["age"] = -1
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("age" in str(error["loc"]) for error in errors)
    
    def test_age_validation_upper_bound(self):
        """Test that age > 120 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["age"] = 121
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("age" in str(error["loc"]) for error in errors)
    
    def test_bmi_validation_lower_bound(self):
        """Test that BMI < 10 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["bmi"] = 9.5
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("bmi" in str(error["loc"]) for error in errors)
    
    def test_bmi_validation_upper_bound(self):
        """Test that BMI > 60 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["bmi"] = 61.0
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("bmi" in str(error["loc"]) for error in errors)
    
    def test_heart_rate_validation_lower_bound(self):
        """Test that heart_rate < 30 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["heart_rate"] = 29
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("heart_rate" in str(error["loc"]) for error in errors)
    
    def test_heart_rate_validation_upper_bound(self):
        """Test that heart_rate > 220 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["heart_rate"] = 221
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("heart_rate" in str(error["loc"]) for error in errors)
    
    def test_blood_pressure_validation_systolic_lower_bound(self):
        """Test that systolic_bp < 60 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["systolic_bp"] = 59
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("systolic_bp" in str(error["loc"]) for error in errors)
    
    def test_blood_pressure_validation_systolic_upper_bound(self):
        """Test that systolic_bp > 250 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["systolic_bp"] = 251
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("systolic_bp" in str(error["loc"]) for error in errors)
    
    def test_blood_pressure_validation_diastolic_lower_bound(self):
        """Test that diastolic_bp < 40 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["diastolic_bp"] = 39
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("diastolic_bp" in str(error["loc"]) for error in errors)
    
    def test_blood_pressure_validation_diastolic_upper_bound(self):
        """Test that diastolic_bp > 150 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["diastolic_bp"] = 151
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("diastolic_bp" in str(error["loc"]) for error in errors)
    
    def test_diastolic_less_than_systolic_validation(self):
        """Test that diastolic_bp >= systolic_bp is rejected (Requirement 17.3)."""
        invalid_data = self._get_base_data()
        invalid_data["systolic_bp"] = 120
        invalid_data["diastolic_bp"] = 120  # Equal to systolic
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("diastolic_bp" in str(error["loc"]) and "Diastolic BP must be less than Systolic BP" in error["msg"] for error in errors)
    
    def test_diastolic_greater_than_systolic_validation(self):
        """Test that diastolic_bp > systolic_bp is rejected (Requirement 17.3)."""
        invalid_data = self._get_base_data()
        invalid_data["systolic_bp"] = 120
        invalid_data["diastolic_bp"] = 125  # Greater than systolic
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("diastolic_bp" in str(error["loc"]) and "Diastolic BP must be less than Systolic BP" in error["msg"] for error in errors)
    
    def test_spo2_validation_lower_bound(self):
        """Test that SpO2 < 70 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["spo2"] = 69.5
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("spo2" in str(error["loc"]) for error in errors)
    
    def test_spo2_validation_upper_bound(self):
        """Test that SpO2 > 100 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["spo2"] = 100.5
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("spo2" in str(error["loc"]) for error in errors)
    
    def test_respiratory_rate_validation_lower_bound(self):
        """Test that respiratory_rate < 8 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["respiratory_rate"] = 7
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("respiratory_rate" in str(error["loc"]) for error in errors)
    
    def test_respiratory_rate_validation_upper_bound(self):
        """Test that respiratory_rate > 40 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["respiratory_rate"] = 41
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("respiratory_rate" in str(error["loc"]) for error in errors)
    
    def test_body_temperature_validation_lower_bound(self):
        """Test that body_temperature < 35.0 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["body_temperature"] = 34.9
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("body_temperature" in str(error["loc"]) for error in errors)
    
    def test_body_temperature_validation_upper_bound(self):
        """Test that body_temperature > 42.0 is rejected (Requirement 17.2)."""
        invalid_data = self._get_base_data()
        invalid_data["body_temperature"] = 42.1
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("body_temperature" in str(error["loc"]) for error in errors)
    
    def test_gender_enum_validation(self):
        """Test that invalid gender is rejected (Requirement 17.3)."""
        invalid_data = self._get_base_data()
        invalid_data["gender"] = "Unknown"
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("gender" in str(error["loc"]) for error in errors)
    
    def test_smoking_status_enum_validation(self):
        """Test that invalid smoking_status is rejected (Requirement 17.3)."""
        invalid_data = self._get_base_data()
        invalid_data["smoking_status"] = "Sometimes"
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("smoking_status" in str(error["loc"]) for error in errors)
    
    def test_medication_taken_enum_validation(self):
        """Test that invalid medication_taken is rejected (Requirement 17.3)."""
        invalid_data = self._get_base_data()
        invalid_data["medication_taken"] = "Maybe"
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("medication_taken" in str(error["loc"]) for error in errors)
    
    def test_missing_required_field(self):
        """Test that missing required field is rejected (Requirement 17.1)."""
        invalid_data = self._get_base_data()
        del invalid_data["patient_id"]
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("patient_id" in str(error["loc"]) for error in errors)
    
    def test_compliance_score_range_validation(self):
        """Test that compliance_score outside [0, 100] is rejected (Requirement 17.4)."""
        invalid_data = self._get_base_data()
        invalid_data["compliance_score"] = 101.0
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("compliance_score" in str(error["loc"]) for error in errors)
    
    def test_readmission_probability_range_validation(self):
        """Test that readmission_probability outside [0, 1] is rejected (Requirement 17.5)."""
        invalid_data = self._get_base_data()
        invalid_data["readmission_probability"] = 1.5
        
        with pytest.raises(ValidationError) as exc_info:
            PatientRecord(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any("readmission_probability" in str(error["loc"]) for error in errors)
    
    def _get_base_data(self):
        """Helper method to get valid base patient data."""
        return {
            "patient_id": "P001",
            "patient_name": "John Doe",
            "age": 65,
            "gender": "Male",
            "bmi": 28.5,
            "smoking_status": "Former",
            "alcohol_consumption": "Moderate",
            "disease_type": "Heart Failure",
            "heart_rate": 78,
            "systolic_bp": 130,
            "diastolic_bp": 85,
            "spo2": 96.5,
            "respiratory_rate": 16,
            "body_temperature": 36.8,
            "expected_steps": 5000,
            "expected_sleep_hours": 8.0,
            "water_intake_goal": 2000,
            "actual_steps": 4200,
            "actual_sleep_hours": 7.5,
            "water_intake": 1800,
            "medication_taken": "Yes",
            "exercise_completed": "Yes",
            "diet_compliance": 85.0,
            "day": 1
        }
