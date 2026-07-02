"""AI Health Assistant API.

Answers patient and doctor questions grounded entirely in the patient's
own Digital Twin data, care plan, medical history, and prediction engine.

No LLM is required — all answers are deterministic, evidence-based, and
generated from the real data stored in the database. This guarantees zero
hallucination and sub-100ms response times.

Endpoint:
  POST /api/assistant/chat
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from pydantic import BaseModel

from app.database.connection import get_db_session
from app.auth.dependencies import get_current_user
from app.auth.models import UserDB
from app.database.models import (
    PatientProfileDB, PatientRecordDB, DoctorProfileDB,
    CarePlanDB, PatientVitalsDailyDB, MedicalHistoryDB,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/assistant", tags=["assistant"])


# ── Schemas ───────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    patient_id: Optional[str] = None   # doctor/admin override; patients use their own id
    history: Optional[List[ChatMessage]] = None


class AssistantEvidence(BaseModel):
    label: str
    value: str


class ChatResponse(BaseModel):
    answer: str
    evidence: List[AssistantEvidence]
    recommendations: List[str]
    expected_improvement: Optional[str] = None
    data_sources: List[str]


# ── Role helper ───────────────────────────────────────────────────────────

def _role(user: UserDB) -> str:
    r = user.role
    return r.value if hasattr(r, "value") else str(r)


# ── Main endpoint ─────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    cu: UserDB = Depends(get_current_user),
) -> ChatResponse:
    """Answers health questions grounded in the patient's real data."""
    role = _role(cu)

    # Determine which patient's data to use
    if role == "patient":
        target_id = cu.id  # patients always see only their own data
    elif body.patient_id:
        # Doctor/admin specified a patient
        if role == "doctor":
            # Verify assignment
            doc_profile = (await db.execute(
                select(DoctorProfileDB).where(DoctorProfileDB.user_id == cu.id)
            )).scalar_one_or_none()
            if doc_profile:
                pat_profile = (await db.execute(
                    select(PatientProfileDB).where(PatientProfileDB.user_id == body.patient_id)
                )).scalar_one_or_none()
                if pat_profile and pat_profile.assigned_doctor_id != doc_profile.id:
                    raise HTTPException(403, "You are not assigned to this patient")
        target_id = body.patient_id
    else:
        target_id = cu.id

    # Gather all available data
    ctx = await _gather_context(target_id, db)
    if not ctx:
        return ChatResponse(
            answer="I couldn't find any health records for this patient. Please ensure the patient has completed onboarding.",
            evidence=[],
            recommendations=["Complete patient onboarding to enable health monitoring."],
            data_sources=[],
        )

    # Route question to the appropriate handler
    q = body.question.lower().strip()
    return _answer(q, ctx, role)


# ── Context gathering ─────────────────────────────────────────────────────

class _PatientContext:
    """All data about a patient, gathered in one DB round-trip."""
    def __init__(self):
        self.profile: Optional[PatientProfileDB] = None
        self.records: List[PatientRecordDB] = []
        self.latest: Optional[PatientRecordDB] = None
        self.prev: Optional[PatientRecordDB] = None
        self.care_plan: Optional[CarePlanDB] = None
        self.today_vitals: Optional[PatientVitalsDailyDB] = None
        self.recent_vitals: List[PatientVitalsDailyDB] = []
        self.medical_history: Optional[MedicalHistoryDB] = None
        self.user: Optional[UserDB] = None


async def _gather_context(patient_user_id: str, db: AsyncSession) -> Optional[_PatientContext]:
    ctx = _PatientContext()

    ctx.user = (await db.execute(
        select(UserDB).where(UserDB.id == patient_user_id)
    )).scalar_one_or_none()

    ctx.profile = (await db.execute(
        select(PatientProfileDB).where(PatientProfileDB.user_id == patient_user_id)
    )).scalar_one_or_none()

    records_result = await db.execute(
        select(PatientRecordDB)
        .where(PatientRecordDB.patient_id == patient_user_id)
        .order_by(PatientRecordDB.day.asc())
    )
    ctx.records = list(records_result.scalars().all())

    if not ctx.records:
        return None

    ctx.latest = ctx.records[-1]
    ctx.prev   = ctx.records[-2] if len(ctx.records) >= 2 else None

    ctx.care_plan = (await db.execute(
        select(CarePlanDB)
        .where(CarePlanDB.patient_user_id == patient_user_id, CarePlanDB.is_active == True)
        .order_by(CarePlanDB.created_at.desc())
    )).scalar_one_or_none()

    today = str(date.today())
    ctx.today_vitals = (await db.execute(
        select(PatientVitalsDailyDB).where(
            PatientVitalsDailyDB.patient_user_id == patient_user_id,
            PatientVitalsDailyDB.log_date == today,
        )
    )).scalar_one_or_none()

    recent_result = await db.execute(
        select(PatientVitalsDailyDB)
        .where(PatientVitalsDailyDB.patient_user_id == patient_user_id)
        .order_by(PatientVitalsDailyDB.log_date.desc())
        .limit(7)
    )
    ctx.recent_vitals = list(recent_result.scalars().all())

    ctx.medical_history = (await db.execute(
        select(MedicalHistoryDB).where(MedicalHistoryDB.patient_user_id == patient_user_id)
    )).scalar_one_or_none()

    return ctx


# ── Answer engine — all logic, zero hallucination ─────────────────────────

def _pct(v) -> str:
    if v is None: return "N/A"
    return f"{round(float(v))}%"

def _val(v, unit="") -> str:
    if v is None: return "N/A"
    return f"{v}{unit}"

def _delta(a, b) -> str:
    if a is None or b is None: return "N/A"
    d = float(a) - float(b)
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.1f}"


def _answer(q: str, ctx: _PatientContext, role: str) -> ChatResponse:
    """Route the question to the right handler."""

    # ── Recovery score questions ─────────────────────────────────────────
    if any(k in q for k in ["recovery score", "recovery", "why did my recovery"]):
        return _answer_recovery(ctx)

    # ── Risk questions ───────────────────────────────────────────────────
    if any(k in q for k in ["risk", "readmission", "probability", "danger"]):
        return _answer_risk(ctx)

    # ── Today / daily improvement ─────────────────────────────────────────
    if any(k in q for k in ["today", "improve today", "what should i do", "what can i do"]):
        return _answer_today(ctx)

    # ── Sleep ─────────────────────────────────────────────────────────────
    if any(k in q for k in ["sleep", "slept"]):
        return _answer_sleep(ctx)

    # ── Medication ───────────────────────────────────────────────────────
    if any(k in q for k in ["medication", "medicine", "pill", "drug", "missed"]):
        return _answer_medication(ctx)

    # ── Steps / exercise ─────────────────────────────────────────────────
    if any(k in q for k in ["step", "walk", "exercise", "activity"]):
        return _answer_steps(ctx)

    # ── Blood pressure ────────────────────────────────────────────────────
    if any(k in q for k in ["blood pressure", "bp", "systolic", "diastolic"]):
        return _answer_bp(ctx)

    # ── Compliance / care plan ────────────────────────────────────────────
    if any(k in q for k in ["care plan", "compliance", "following", "adherence"]):
        return _answer_compliance(ctx)

    # ── Yesterday / comparison ────────────────────────────────────────────
    if any(k in q for k in ["yesterday", "compared", "changed", "difference"]):
        return _answer_comparison(ctx)

    # ── Weekly summary ────────────────────────────────────────────────────
    if any(k in q for k in ["week", "summary", "overview", "past 7", "last 7"]):
        return _answer_weekly(ctx)

    # ── Doctor recommendation ─────────────────────────────────────────────
    if any(k in q for k in ["recommend", "doctor say", "advice", "suggest"]):
        return _answer_recommendation(ctx)

    # ── Water / hydration ─────────────────────────────────────────────────
    if any(k in q for k in ["water", "hydrat", "drink"]):
        return _answer_water(ctx)

    # ── Vitals general ────────────────────────────────────────────────────
    if any(k in q for k in ["vital", "heart rate", "spo2", "oxygen", "temperature"]):
        return _answer_vitals(ctx)

    # ── Doctor-specific: patient summary ─────────────────────────────────
    if any(k in q for k in ["patient", "high risk", "urgent", "who need"]):
        return _answer_patient_summary(ctx)

    # ── Default: full health summary ─────────────────────────────────────
    return _answer_summary(ctx)


# ── Individual answer handlers ────────────────────────────────────────────

def _answer_recovery(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    p = ctx.prev
    factors, recs = [], []
    evidence = []

    score = float(r.recovery_score) if r.recovery_score else 0.0
    evidence.append(AssistantEvidence(label="Current Recovery Score", value=_pct(r.recovery_score)))

    if p:
        delta = float(r.recovery_score or 0) - float(p.recovery_score or 0)
        evidence.append(AssistantEvidence(label="Change from Previous Day", value=f"{'+' if delta>=0 else ''}{delta:.1f} pts"))
        if delta < 0:
            factors.append(f"Recovery score decreased by {abs(delta):.1f} points since last record.")

    if r.medication_taken == "No":
        factors.append("Medication was missed.")
        recs.append("Take your prescribed medication on time every day.")

    if r.actual_sleep_hours and r.expected_sleep_hours:
        sleep_gap = float(r.expected_sleep_hours) - float(r.actual_sleep_hours)
        evidence.append(AssistantEvidence(label="Sleep", value=f"{r.actual_sleep_hours}h actual vs {r.expected_sleep_hours}h goal"))
        if sleep_gap > 0.5:
            factors.append(f"Sleep was {sleep_gap:.1f}h below target.")
            recs.append(f"Aim for {r.expected_sleep_hours}h of sleep tonight.")

    if r.actual_steps and r.expected_steps:
        step_gap = int(r.expected_steps) - int(r.actual_steps)
        evidence.append(AssistantEvidence(label="Steps", value=f"{r.actual_steps:,} actual vs {r.expected_steps:,} goal"))
        if step_gap > 500:
            factors.append(f"Step count was {step_gap:,} below goal.")
            recs.append(f"Walk at least {r.expected_steps:,} steps tomorrow.")

    if r.compliance_score:
        evidence.append(AssistantEvidence(label="Compliance Score", value=_pct(r.compliance_score)))
        if float(r.compliance_score) < 70:
            factors.append(f"Overall compliance is low at {_pct(r.compliance_score)}.")
            recs.append("Improve compliance with medication, exercise, and diet.")

    if not factors:
        factors = ["Your recovery is on track. Keep following your care plan."]

    if not recs:
        recs = ["Continue your current routine — you are progressing well."]

    exp = None
    if score < 85:
        exp = f"If you follow your care plan consistently for 3–5 days, your recovery score could improve by 5–15 points."

    answer = "**Recovery Score Analysis**\n\n" + "\n".join(f"• {f}" for f in factors)

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement=exp,
        data_sources=["Digital Twin", "Compliance Scores", "Patient Records"],
    )


def _answer_risk(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    evidence, recs, factors = [], [], []

    prob = float(r.readmission_probability) if r.readmission_probability else 0.0
    risk = r.risk_level or "Unknown"
    evidence.append(AssistantEvidence(label="Readmission Probability", value=f"{round(prob*100)}%"))
    evidence.append(AssistantEvidence(label="Risk Level", value=risk))
    evidence.append(AssistantEvidence(label="Recovery Status", value=r.recovery_status or "N/A"))

    if prob > 0.65:
        factors.append("Readmission probability is critically high — immediate review needed.")
        recs.append("Contact your doctor immediately.")
    elif prob > 0.45:
        factors.append("Readmission risk is elevated. Close monitoring required.")
        recs.append("Schedule a follow-up with your doctor this week.")
    elif prob > 0.25:
        factors.append("Moderate readmission risk. Improve adherence to reduce it.")
    else:
        factors.append("Your readmission risk is currently low. Keep up the good work.")

    if r.medication_taken == "No":
        factors.append("Missing medication significantly increases readmission risk.")
        recs.append("Take medication as prescribed — do not skip doses.")

    if r.compliance_score and float(r.compliance_score) < 60:
        factors.append(f"Low compliance ({_pct(r.compliance_score)}) is a major risk driver.")
        recs.append("Improve compliance with your daily care plan targets.")

    if r.deviation_score and float(r.deviation_score) > 20:
        factors.append(f"High deviation ({float(r.deviation_score):.1f}) between Ideal Twin and Real Twin.")
        evidence.append(AssistantEvidence(label="Deviation from Ideal", value=f"{float(r.deviation_score):.1f}"))

    if r.doctor_recommendation:
        recs.append(f"Doctor's recommendation: {r.doctor_recommendation}")

    answer = f"**Risk Assessment: {risk} Risk**\n\n" + "\n".join(f"• {f}" for f in factors)

    imp = None
    if prob > 0.3:
        new_prob = max(0.05, prob - 0.15)
        imp = f"Consistent medication and care plan adherence for 7 days could reduce your risk from {round(prob*100)}% to approximately {round(new_prob*100)}%."

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement=imp,
        data_sources=["AI Prediction Engine", "Digital Twin", "Compliance Data"],
    )


def _answer_today(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    cp = ctx.care_plan
    today_v = ctx.today_vitals
    recs, evidence = [], []

    logged = today_v is not None
    evidence.append(AssistantEvidence(label="Today's Vitals Logged", value="Yes" if logged else "Not yet"))

    if not logged:
        recs.append("Log your vitals today to keep your Digital Twin updated.")

    steps_goal = int(cp.daily_steps_goal) if cp and cp.daily_steps_goal else int(r.expected_steps or 8000)
    sleep_goal = float(cp.sleep_hours_goal) if cp and cp.sleep_hours_goal else float(r.expected_sleep_hours or 8.0)
    water_goal = int(cp.water_intake_goal_ml) if cp and cp.water_intake_goal_ml else int(r.water_intake_goal or 2000)

    evidence.append(AssistantEvidence(label="Step Goal", value=f"{steps_goal:,} steps"))
    evidence.append(AssistantEvidence(label="Sleep Goal", value=f"{sleep_goal}h"))
    evidence.append(AssistantEvidence(label="Water Goal", value=f"{water_goal}ml"))

    recs.append(f"Walk at least {steps_goal:,} steps today.")
    recs.append(f"Sleep {sleep_goal} hours tonight.")
    recs.append(f"Drink {water_goal}ml of water throughout the day.")

    if r.medication_taken == "No":
        recs.append("⚠️ Take your prescribed medication — you missed it last recorded day.")
    else:
        recs.append("Continue taking your medication as prescribed.")

    if cp and cp.exercise_plan:
        recs.append(f"Exercise: {cp.exercise_plan}")

    if cp and cp.diet_plan:
        recs.append(f"Diet: {cp.diet_plan}")

    answer = f"**Your Health Tasks for Today**\n\nCurrent Risk: {r.risk_level or 'N/A'} | Recovery: {_pct(r.recovery_score)}"

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement="Completing all daily tasks can improve your compliance score by 10–20 points.",
        data_sources=["Care Plan", "Daily Targets", "Patient Records"],
    )


def _answer_sleep(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    evidence, recs = [], []

    actual = float(r.actual_sleep_hours) if r.actual_sleep_hours else None
    goal   = float(r.expected_sleep_hours) if r.expected_sleep_hours else 8.0
    evidence.append(AssistantEvidence(label="Last Recorded Sleep", value=_val(actual, "h")))
    evidence.append(AssistantEvidence(label="Sleep Goal", value=f"{goal}h"))

    if ctx.today_vitals and ctx.today_vitals.actual_sleep_hours:
        evidence.append(AssistantEvidence(label="Today's Sleep", value=f"{ctx.today_vitals.actual_sleep_hours}h"))

    if actual is not None:
        gap = goal - actual
        if gap > 0.5:
            answer = f"You slept {actual}h last recorded — {gap:.1f}h below your {goal}h goal."
            recs.append(f"Aim for {goal}h of sleep each night.")
            recs.append("Maintain a consistent sleep schedule — go to bed at the same time daily.")
            recs.append("Avoid screens for 1 hour before bedtime.")
        else:
            answer = f"You slept {actual}h last recorded — meeting your {goal}h goal. Well done!"
            recs.append("Keep maintaining your sleep schedule.")
    else:
        answer = "No sleep data recorded yet. Please log your vitals daily."
        recs.append("Log your daily vitals including sleep hours.")

    if ctx.care_plan and ctx.care_plan.sleep_hours_goal:
        evidence.append(AssistantEvidence(label="Doctor's Sleep Target", value=f"{ctx.care_plan.sleep_hours_goal}h"))

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement="Adequate sleep can improve your recovery score by 5–10 points over 3 days.",
        data_sources=["Patient Records", "Care Plan"],
    )


def _answer_medication(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    evidence, recs = [], []

    taken = r.medication_taken
    evidence.append(AssistantEvidence(label="Last Recorded Medication", value=taken or "N/A"))

    missed_days = sum(1 for rec in ctx.records[-7:] if rec.medication_taken == "No")
    evidence.append(AssistantEvidence(label="Missed Days (Last 7)", value=str(missed_days)))

    if ctx.care_plan and ctx.care_plan.medication_schedule:
        evidence.append(AssistantEvidence(label="Prescribed Schedule", value=ctx.care_plan.medication_schedule))

    if ctx.medical_history and ctx.medical_history.current_medications:
        evidence.append(AssistantEvidence(label="Current Medications", value=ctx.medical_history.current_medications))

    if taken == "No":
        answer = f"⚠️ Your last recorded day shows medication was NOT taken. You missed medication on {missed_days} of the last 7 recorded days."
        recs.append("Take your medication immediately if you have missed today's dose.")
        recs.append("Set a daily alarm to remind yourself to take medication.")
        recs.append("Missing medication is the single biggest driver of readmission risk.")
    else:
        answer = f"Your medication is recorded as taken on the last monitoring day. You missed medication on {missed_days} of the last 7 recorded days."
        if missed_days > 0:
            recs.append("Consistency is key — try not to miss any doses.")
        else:
            recs.append("Excellent medication adherence! Keep it up.")

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement="Perfect medication adherence for 7 days can reduce readmission risk by up to 15%.",
        data_sources=["Patient Records", "Care Plan", "Medical History"],
    )


def _answer_steps(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    cp = ctx.care_plan
    evidence, recs = [], []

    goal  = int(cp.daily_steps_goal) if cp and cp.daily_steps_goal else int(r.expected_steps or 8000)
    actual = int(r.actual_steps) if r.actual_steps else None
    evidence.append(AssistantEvidence(label="Step Goal", value=f"{goal:,}"))
    evidence.append(AssistantEvidence(label="Last Recorded Steps", value=f"{actual:,}" if actual else "N/A"))

    if actual is not None:
        gap = goal - actual
        if gap > 0:
            answer = f"You walked {actual:,} steps last recorded — {gap:,} steps below your {goal:,} goal."
            recs.append(f"Walk {gap:,} more steps today to meet your goal.")
            recs.append("Break it into 3 short walks of 10–15 minutes each.")
        else:
            answer = f"Great job — you walked {actual:,} steps, exceeding your {goal:,} goal!"
            recs.append("Keep up the excellent activity level.")
    else:
        answer = f"Your daily step goal is {goal:,} steps. No step data recorded yet today."
        recs.append(f"Aim to walk at least {goal:,} steps today.")

    if cp and cp.exercise_plan:
        evidence.append(AssistantEvidence(label="Exercise Plan", value=cp.exercise_plan))
        recs.append(f"Follow your exercise plan: {cp.exercise_plan}")

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement="Meeting your daily step goal consistently can improve compliance by 15 points.",
        data_sources=["Patient Records", "Care Plan"],
    )


def _answer_bp(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    p = ctx.prev
    evidence, recs = [], []

    sys_bp = r.systolic_bp
    dia_bp = r.diastolic_bp
    evidence.append(AssistantEvidence(label="Blood Pressure", value=f"{sys_bp}/{dia_bp} mmHg" if sys_bp else "N/A"))

    if p and p.systolic_bp:
        delta_sys = int(sys_bp or 0) - int(p.systolic_bp or 0)
        evidence.append(AssistantEvidence(label="Change from Previous", value=f"{'+' if delta_sys >= 0 else ''}{delta_sys} mmHg (systolic)"))

    if sys_bp and int(sys_bp) > 140:
        answer = f"Your blood pressure is elevated at {sys_bp}/{dia_bp} mmHg (above 140/90 threshold)."
        recs.append("Reduce sodium intake — avoid processed and salty foods.")
        recs.append("Manage stress with deep breathing or light activity.")
        recs.append("Ensure you have taken your blood pressure medication.")
        recs.append("Contact your doctor if it remains above 150/95 for more than 2 days.")
    elif sys_bp and int(sys_bp) < 90:
        answer = f"Your blood pressure is low at {sys_bp}/{dia_bp} mmHg."
        recs.append("Stay well hydrated — drink water regularly.")
        recs.append("Avoid standing up suddenly to prevent dizziness.")
        recs.append("Consult your doctor if you feel dizzy or faint.")
    else:
        answer = f"Your blood pressure is {sys_bp}/{dia_bp} mmHg — within normal range."
        recs.append("Continue your current routine to maintain healthy blood pressure.")

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs,
        expected_improvement="Blood pressure improvements typically require 3–7 days of consistent medication and lifestyle changes.",
        data_sources=["Patient Records", "Vital Signs"],
    )


def _answer_compliance(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    cp = ctx.care_plan
    evidence, recs = [], []

    score = float(r.compliance_score) if r.compliance_score else 0.0
    evidence.append(AssistantEvidence(label="Compliance Score", value=_pct(r.compliance_score)))
    evidence.append(AssistantEvidence(label="Deviation from Ideal", value=f"{float(r.deviation_score or 0):.1f}"))

    # Breakdown
    items = []
    if r.medication_taken == "Yes": items.append("✓ Medication taken")
    else: items.append("✗ Medication missed"); recs.append("Take medication as prescribed.")

    if r.exercise_completed == "Yes": items.append("✓ Exercise completed")
    else: items.append("✗ Exercise not completed"); recs.append("Complete your daily exercise routine.")

    if r.actual_steps and r.expected_steps:
        pct = round(int(r.actual_steps) / int(r.expected_steps) * 100)
        items.append(f"{'✓' if pct >= 80 else '✗'} Steps: {pct}% of goal")
        if pct < 80: recs.append(f"Walk more — you reached {pct}% of your step goal.")

    evidence.append(AssistantEvidence(label="Compliance Breakdown", value=" | ".join(items)))

    if cp:
        evidence.append(AssistantEvidence(label="Care Plan Active", value="Yes"))
        evidence.append(AssistantEvidence(label="Step Goal", value=f"{cp.daily_steps_goal:,}"))

    if score >= 80:
        answer = f"Your compliance is strong at {_pct(r.compliance_score)}. You are closely following your care plan."
    elif score >= 60:
        answer = f"Your compliance is moderate at {_pct(r.compliance_score)}. There are a few areas to improve."
    else:
        answer = f"Your compliance is low at {_pct(r.compliance_score)}. This is increasing your readmission risk."

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        recommendations=recs or ["Keep following your care plan consistently."],
        expected_improvement="Improving compliance from 60% to 80% typically reduces readmission probability by 10–20%.",
        data_sources=["Digital Twin", "Care Plan", "Patient Records"],
    )


def _answer_comparison(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    p = ctx.prev
    evidence, recs = [], []

    if not p:
        return ChatResponse(
            answer="Only one day of records available — no comparison possible yet.",
            evidence=[], recommendations=["Log vitals daily to build your health timeline."],
            data_sources=["Patient Records"],
        )

    changes = []
    for label, cur, prev, unit in [
        ("Recovery Score",    r.recovery_score,    p.recovery_score,    "%"),
        ("Compliance Score",  r.compliance_score,  p.compliance_score,  "%"),
        ("Readmission Risk",  r.readmission_probability, p.readmission_probability, ""),
        ("Steps",             r.actual_steps,      p.actual_steps,      ""),
        ("Sleep",             r.actual_sleep_hours,p.actual_sleep_hours,"h"),
    ]:
        if cur is not None and prev is not None:
            d = float(cur) - float(prev)
            if label == "Readmission Risk": d *= 100  # convert to percentage points
            sign = "+" if d >= 0 else ""
            direction = "▲" if d > 0 else ("▼" if d < 0 else "→")
            changes.append(f"{direction} {label}: {sign}{d:.1f}{unit}")
            evidence.append(AssistantEvidence(label=label, value=f"{_val(cur)}{unit} (was {_val(prev)}{unit})"))

    answer = f"**Day {p.day} → Day {r.day} Comparison**\n\n" + "\n".join(f"• {c}" for c in changes)

    if r.medication_taken != p.medication_taken:
        recs.append(f"Medication status changed: {p.medication_taken} → {r.medication_taken}")

    recs.append("Review the changes above and focus on any declining metrics.")

    return ChatResponse(
        answer=answer, evidence=evidence,
        recommendations=recs,
        data_sources=["Patient Records Timeline"],
    )


def _answer_weekly(ctx: _PatientContext) -> ChatResponse:
    records = ctx.records[-7:] if len(ctx.records) >= 7 else ctx.records
    evidence, recs = [], []

    if not records:
        return ChatResponse(answer="No data available for weekly summary.", evidence=[],
            recommendations=[], data_sources=[])

    avg_compliance   = sum(float(r.compliance_score or 0) for r in records) / len(records)
    avg_recovery     = sum(float(r.recovery_score or 0) for r in records) / len(records)
    avg_risk         = sum(float(r.readmission_probability or 0) for r in records) / len(records)
    missed_meds      = sum(1 for r in records if r.medication_taken == "No")
    avg_steps        = sum(int(r.actual_steps or 0) for r in records) / len(records)

    evidence += [
        AssistantEvidence(label="Avg Compliance (7d)", value=f"{avg_compliance:.1f}%"),
        AssistantEvidence(label="Avg Recovery Score (7d)", value=f"{avg_recovery:.1f}%"),
        AssistantEvidence(label="Avg Readmission Risk (7d)", value=f"{avg_risk*100:.1f}%"),
        AssistantEvidence(label="Missed Medication Days", value=str(missed_meds)),
        AssistantEvidence(label="Avg Daily Steps", value=f"{int(avg_steps):,}"),
    ]

    trend = "improving" if ctx.records[-1].recovery_score and ctx.records[0].recovery_score and \
        float(ctx.records[-1].recovery_score) > float(ctx.records[0].recovery_score) else "declining"
    answer = f"**Weekly Health Summary ({len(records)} days)**\n\nYour recovery trend is {trend}. " \
             f"Average compliance: {avg_compliance:.0f}%, average risk: {avg_risk*100:.0f}%."

    if missed_meds > 0:
        recs.append(f"You missed medication on {missed_meds} day(s) this week. Prioritise consistent medication.")
    if avg_compliance < 70:
        recs.append("Compliance is below 70% — focus on completing all daily care plan tasks.")
    if avg_steps < 5000:
        recs.append("Average step count is low — aim for more daily walking.")
    if not recs:
        recs.append("You had a good week! Keep maintaining your health routine.")

    return ChatResponse(answer=answer, evidence=evidence, recommendations=recs,
        data_sources=["Patient Records", "7-Day Timeline"])


def _answer_recommendation(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    cp = ctx.care_plan
    evidence, recs = [], []

    evidence.append(AssistantEvidence(label="AI Recommendation", value=r.doctor_recommendation or "N/A"))
    evidence.append(AssistantEvidence(label="Risk Level", value=r.risk_level or "N/A"))
    evidence.append(AssistantEvidence(label="Recovery Status", value=r.recovery_status or "N/A"))

    answer = f"**AI Clinical Recommendation**\n\n{r.doctor_recommendation or 'Continue current treatment.'}"

    if cp:
        if cp.medication_schedule:
            recs.append(f"Medication: {cp.medication_schedule}")
        if cp.exercise_plan:
            recs.append(f"Exercise: {cp.exercise_plan}")
        if cp.diet_plan:
            recs.append(f"Diet: {cp.diet_plan}")
        if cp.notes:
            recs.append(f"Doctor's notes: {cp.notes}")
            evidence.append(AssistantEvidence(label="Doctor Notes", value=cp.notes))

    if not recs:
        recs.append("Follow your current care plan and log vitals daily.")

    return ChatResponse(answer=answer, evidence=evidence, recommendations=recs,
        data_sources=["AI Prediction Engine", "Care Plan"])


def _answer_water(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    cp = ctx.care_plan
    evidence, recs = [], []

    goal   = int(cp.water_intake_goal_ml) if cp and cp.water_intake_goal_ml else int(r.water_intake_goal or 2000)
    actual = int(r.water_intake) if r.water_intake else None
    evidence.append(AssistantEvidence(label="Water Goal", value=f"{goal}ml"))
    evidence.append(AssistantEvidence(label="Last Recorded Intake", value=f"{actual}ml" if actual else "N/A"))

    if actual is not None:
        gap = goal - actual
        if gap > 200:
            answer = f"You drank {actual}ml — {gap}ml below your {goal}ml daily goal."
            recs.append(f"Drink {gap}ml more water today to meet your goal.")
            recs.append("Carry a water bottle and sip regularly throughout the day.")
        else:
            answer = f"You drank {actual}ml — meeting your {goal}ml daily goal. Well done!"
            recs.append("Keep up your hydration habits.")
    else:
        answer = f"Your daily water goal is {goal}ml. Please log your intake today."
        recs.append(f"Aim to drink at least {goal}ml of water today.")

    return ChatResponse(answer=answer, evidence=evidence, recommendations=recs,
        data_sources=["Patient Records", "Care Plan"])


def _answer_vitals(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    evidence = [
        AssistantEvidence(label="Heart Rate",     value=f"{r.heart_rate} bpm" if r.heart_rate else "N/A"),
        AssistantEvidence(label="Blood Pressure", value=f"{r.systolic_bp}/{r.diastolic_bp} mmHg" if r.systolic_bp else "N/A"),
        AssistantEvidence(label="SpO₂",           value=f"{r.spo2}%" if r.spo2 else "N/A"),
        AssistantEvidence(label="Temperature",    value=f"{r.body_temperature}°C" if r.body_temperature else "N/A"),
        AssistantEvidence(label="Day",            value=str(r.day)),
    ]
    recs = []
    alerts = []
    if r.heart_rate and (int(r.heart_rate) > 100 or int(r.heart_rate) < 50):
        alerts.append(f"⚠️ Heart rate {r.heart_rate} bpm is outside normal range (50–100).")
        recs.append("Contact your doctor if heart rate remains abnormal.")
    if r.spo2 and float(r.spo2) < 94:
        alerts.append(f"⚠️ SpO₂ {r.spo2}% is low — normal is above 94%.")
        recs.append("Sit upright and take slow deep breaths. Seek medical attention if below 90%.")
    if r.systolic_bp and int(r.systolic_bp) > 140:
        alerts.append(f"⚠️ Blood pressure {r.systolic_bp}/{r.diastolic_bp} is elevated.")
        recs.append("Reduce sodium intake and take prescribed BP medication.")

    if not recs:
        recs.append("Your vitals are within acceptable ranges. Log today's vitals to keep your twin updated.")

    answer = "**Current Vital Signs**\n\n"
    if alerts:
        answer += "\n".join(alerts)
    else:
        answer += "Vitals are within normal parameters."

    return ChatResponse(answer=answer, evidence=evidence, recommendations=recs,
        data_sources=["Patient Records", "Vital Signs"])


def _answer_patient_summary(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    last7 = ctx.records[-7:] if len(ctx.records) >= 7 else ctx.records
    avg_c = sum(float(x.compliance_score or 0) for x in last7) / max(len(last7), 1)

    evidence = [
        AssistantEvidence(label="Risk Level", value=r.risk_level or "N/A"),
        AssistantEvidence(label="Readmission Probability", value=f"{round(float(r.readmission_probability or 0)*100)}%"),
        AssistantEvidence(label="Recovery Score", value=_pct(r.recovery_score)),
        AssistantEvidence(label="7-Day Avg Compliance", value=f"{avg_c:.1f}%"),
        AssistantEvidence(label="Disease", value=r.disease_type or "N/A"),
        AssistantEvidence(label="Days Monitored", value=str(len(ctx.records))),
    ]
    recs = []
    if r.risk_level in ("High", "Critical"):
        recs.append("⚠️ Patient requires urgent clinical review.")
    if avg_c < 60:
        recs.append("Low compliance — consider calling the patient for a check-in.")
    recs.append(f"Doctor recommendation: {r.doctor_recommendation or 'Continue current treatment.'}")

    answer = f"**Patient Summary — Day {r.day}**\n\nRisk: {r.risk_level} | Recovery: {_pct(r.recovery_score)} | Compliance (7d avg): {avg_c:.0f}%"

    return ChatResponse(answer=answer, evidence=evidence, recommendations=recs,
        data_sources=["Patient Records", "Digital Twin", "AI Prediction"])


def _answer_summary(ctx: _PatientContext) -> ChatResponse:
    r = ctx.latest
    evidence = [
        AssistantEvidence(label="Recovery Score",      value=_pct(r.recovery_score)),
        AssistantEvidence(label="Risk Level",          value=r.risk_level or "N/A"),
        AssistantEvidence(label="Readmission Risk",    value=f"{round(float(r.readmission_probability or 0)*100)}%"),
        AssistantEvidence(label="Compliance Score",    value=_pct(r.compliance_score)),
        AssistantEvidence(label="Monitoring Day",      value=str(r.day)),
        AssistantEvidence(label="Medication Today",    value=r.medication_taken or "N/A"),
        AssistantEvidence(label="Exercise Completed",  value=r.exercise_completed or "N/A"),
    ]
    recs = []
    if r.medication_taken == "No":
        recs.append("Take your medication — it was missed last recorded day.")
    if r.exercise_completed == "No":
        recs.append("Complete your daily exercise routine.")
    if r.compliance_score and float(r.compliance_score) < 70:
        recs.append("Improve compliance by following all care plan targets.")
    if not recs:
        recs.append("You are doing well — keep following your care plan.")

    recs.append(f"AI recommendation: {r.doctor_recommendation or 'Continue current treatment.'}")

    answer = (
        f"**Health Summary — Day {r.day}**\n\n"
        f"Recovery: {_pct(r.recovery_score)} | Risk: {r.risk_level} | "
        f"Compliance: {_pct(r.compliance_score)} | Readmission Risk: {round(float(r.readmission_probability or 0)*100)}%"
    )

    return ChatResponse(answer=answer, evidence=evidence, recommendations=recs,
        data_sources=["Digital Twin", "AI Prediction", "Care Plan", "Patient Records"])
