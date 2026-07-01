import logging
from typing import List, Optional
from app.models.schemas import PatientRecord

logger = logging.getLogger(__name__)

class DeviationEngine:
    @staticmethod
    def calculate_deviations(record: PatientRecord) -> dict:
        """
        Calculate individual and overall deviations between Ideal Twin and Real Twin.
        """
        # 1. Medication deviation: 100.0 if "No" else 0.0
        medication_deviation = 0.0 if record.medication_taken == "Yes" else 100.0

        # 2. Exercise deviation: 100.0 if "No" else 0.0
        exercise_deviation = 0.0 if record.exercise_completed == "Yes" else 100.0

        # 3. Sleep deviation: absolute difference between actual and expected
        sleep_deviation = float(abs(record.expected_sleep_hours - record.actual_sleep_hours))

        # 4. Water deviation: absolute difference
        water_deviation = float(abs(record.water_intake_goal - record.water_intake))

        # 5. Heart Rate deviation: from optimal midpoint of 80 bpm (normal 60-100)
        heart_rate_deviation = float(abs(record.heart_rate - 80.0))

        # 6. Blood pressure deviation:
        # Systolic midpoint is 105 (normal 90-120)
        # Diastolic midpoint is 70 (normal 60-80)
        sys_dev = abs(record.systolic_bp - 105.0)
        dia_dev = abs(record.diastolic_bp - 70.0)
        bp_deviation = float(sys_dev + dia_dev)

        # 7. Weight deviation: actual weight vs expected weight
        actual_weight = record.weight_kg if record.weight_kg is not None else 70.0
        expected_weight = record.expected_weight if record.expected_weight is not None else 70.0
        weight_deviation = float(abs(actual_weight - expected_weight))

        # 8. SpO2 deviation: from optimal midpoint of 97.5% (normal 95-100)
        spo2_deviation = float(abs(record.spo2 - 97.5))

        # 9. Temperature deviation: from optimal midpoint of 36.65 (normal 36.1-37.2)
        temp_deviation = float(abs(record.body_temperature - 36.65))

        return {
            "medication_deviation": medication_deviation,
            "exercise_deviation": exercise_deviation,
            "sleep_deviation": sleep_deviation,
            "water_deviation": water_deviation,
            "heart_rate_deviation": heart_rate_deviation,
            "bp_deviation": bp_deviation,
            "weight_deviation": weight_deviation,
            "spo2_deviation": spo2_deviation,
            "temp_deviation": temp_deviation,
        }

    @staticmethod
    def generate_recommendations(record: PatientRecord) -> List[str]:
        """
        Generate personalized patient recommendations based on deviations and prediction results.
        """
        recs = []
        # Medication
        if record.medication_taken == "No":
            recs.append("Medication missed: Please take your prescribed medicines today.")
        
        # Exercise
        if record.exercise_completed == "No":
            recs.append(f"Exercise routine missed: Complete your physical plan or walk to meet your daily goal of {record.expected_steps} steps.")
        elif record.actual_steps < record.expected_steps - 1500:
            recs.append(f"Activity below target: Increase walking to achieve your goal of {record.expected_steps} steps (actual: {record.actual_steps}).")
            
        # Sleep
        if record.actual_sleep_hours < record.expected_sleep_hours - 1.0:
            recs.append(f"Low Sleep recorded: Target is {record.expected_sleep_hours}h. Consider taking adequate rest (actual: {record.actual_sleep_hours}h).")
        
        # Water
        if record.water_intake < record.water_intake_goal - 500:
            recs.append(f"Hydration below target: Drink more water to achieve your hydration target of {record.water_intake_goal}ml (actual: {record.water_intake}ml).")

        # Blood pressure
        if record.systolic_bp > 130 or record.diastolic_bp > 85:
            recs.append(f"High Blood Pressure Alert (BP: {record.systolic_bp}/{record.diastolic_bp} mmHg). Contact your doctor if you experience dizziness.")
        elif record.systolic_bp < 90 or record.diastolic_bp < 60:
            recs.append(f"Low Blood Pressure Alert (BP: {record.systolic_bp}/{record.diastolic_bp} mmHg). Ensure sufficient hydration.")

        # Heart rate
        if record.heart_rate > 100:
            recs.append(f"High Heart Rate Alert (HR: {record.heart_rate} bpm). Rest and monitor. Contact doctor if persistent.")
        elif record.heart_rate < 55:
            recs.append(f"Low Heart Rate Alert (HR: {record.heart_rate} bpm). Please seek rest.")

        # SpO2
        if record.spo2 < 95.0:
            recs.append(f"Low Blood Oxygen Level (SpO2: {record.spo2}%). Seek immediate rest or oxygen monitoring support.")

        # Weight
        if record.weight_kg is not None and record.expected_weight is not None:
            if record.weight_kg > record.expected_weight + 1.5:
                recs.append(f"Weight increased significantly ({record.weight_kg} kg vs baseline {record.expected_weight} kg). Consider adjusting diet compliance.")

        # Risk level recommendations
        if record.risk_level == "Critical":
            recs.append("CRITICAL RISK LEVEL: Doctor has been notified. Avoid strenuous activity.")
        elif record.risk_level == "High":
            recs.append("High readmission risk detected. Stick strictly to your Care Plan and schedule doctor follow-up.")

        # Defaults
        if not recs:
            recs.append("Great job! You are perfectly on track with your Care Plan targets. Keep it up!")

        return recs

    @staticmethod
    def generate_shap_reasons(record: PatientRecord) -> List[str]:
        """
        Explain the prediction by highlighting the main risk factors contributing to readmission risk.
        """
        reasons = []
        if record.medication_taken == "No":
            reasons.append("Medication missed")
        if record.exercise_completed == "No" or record.actual_steps < record.expected_steps - 2000:
            reasons.append("Reduced Activity")
        if record.actual_sleep_hours < record.expected_sleep_hours - 1.0:
            reasons.append("Low Sleep")
        if record.systolic_bp > 130 or record.diastolic_bp > 85:
            reasons.append("High Blood Pressure")
        if record.heart_rate > 90:
            reasons.append("Elevated Heart Rate")
        if record.spo2 < 95.0:
            reasons.append("Low SpO2 Level")
        if record.weight_kg is not None and record.expected_weight is not None and record.weight_kg > record.expected_weight + 1.5:
            reasons.append("Weight increased")
        
        # If no specific risk factors found but risk is moderate/high:
        if not reasons:
            if record.risk_level in ["High", "Critical"]:
                reasons.append("Demographic / Disease Baseline Risk Factors")
            else:
                reasons.append("Overall recovery is on track")
                
        return reasons
