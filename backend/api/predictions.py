from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from fastapi import APIRouter
from backend.config import settings
from backend.db.sqlite import get_db

router = APIRouter(prefix="/predictions", tags=["predictions"])


def calculate_risk_factors(profile_data: Dict[str, Any], chat_history: List[Dict]) -> Dict[str, float]:
    """Calculate various health risk factors from patient data."""
    risks = {
        "cardiovascular": 0.0,
        "respiratory": 0.0,
        "infection": 0.0,
        "medication_adherence": 0.0,
        "mental_health": 0.0
    }
    
    vitals = profile_data.get("vitals", {})
    symptoms = profile_data.get("symptoms", [])
    medications = profile_data.get("medications", [])
    
    # Cardiovascular risk
    if vitals.get("systolic_bp", 0) > 140:
        risks["cardiovascular"] += 0.3
    if vitals.get("heart_rate", 0) > 100 or vitals.get("heart_rate", 0) < 60:
        risks["cardiovascular"] += 0.2
    
    # Check for cardiovascular symptoms
    cv_keywords = ["chest pain", "shortness of breath", "palpitations", "dizziness"]
    for symptom in symptoms:
        desc = symptom.get("description", "").lower()
        if any(keyword in desc for keyword in cv_keywords):
            risks["cardiovascular"] += 0.25
    
    # Respiratory risk
    if vitals.get("sp_o2", 100) < 95:
        risks["respiratory"] += 0.4
    if vitals.get("respiratory_rate", 16) > 22:
        risks["respiratory"] += 0.2
    
    resp_keywords = ["cough", "breathing", "wheeze", "shortness"]
    for symptom in symptoms:
        desc = symptom.get("description", "").lower()
        if any(keyword in desc for keyword in resp_keywords):
            risks["respiratory"] += 0.3
    
    # Infection risk
    if vitals.get("temperature", 37) > 38.0:
        risks["infection"] += 0.5
    
    infection_keywords = ["fever", "chills", "pain", "swelling", "discharge"]
    for symptom in symptoms:
        desc = symptom.get("description", "").lower()
        if any(keyword in desc for keyword in infection_keywords):
            risks["infection"] += 0.2
    
    # Medication adherence risk (based on mentions in chat)
    recent_messages = [msg["content"] for msg in chat_history[-10:] if msg["role"] == "user"]
    adherence_keywords = ["forgot", "missed", "skipped", "ran out", "stopped taking"]
    
    for message in recent_messages:
        if any(keyword in message.lower() for keyword in adherence_keywords):
            risks["medication_adherence"] += 0.3
    
    # Mental health risk
    mental_keywords = ["anxious", "depressed", "worried", "scared", "overwhelmed", "sad"]
    for message in recent_messages:
        if any(keyword in message.lower() for keyword in mental_keywords):
            risks["mental_health"] += 0.2
    
    # Normalize risks to 0-1 scale
    for risk_type in risks:
        risks[risk_type] = min(1.0, risks[risk_type])
    
    return risks


def predict_health_trajectory(risk_factors: Dict[str, float], current_score: int) -> Tuple[List[int], List[str]]:
    """Predict health score trajectory for next 7 days based on risk factors."""
    predictions = []
    insights = []
    
    # Calculate overall risk
    overall_risk = sum(risk_factors.values()) / len(risk_factors)
    
    # Base trajectory
    base_trend = -2 if overall_risk > 0.5 else 1 if overall_risk < 0.2 else 0
    
    current = current_score
    for day in range(7):
        # Add some realistic variation
        daily_change = base_trend + (math.sin(day * 0.5) * 2) + ((-1) ** day * 1)
        current = max(50, min(100, current + daily_change))
        predictions.append(int(current))
    
    # Generate insights
    if overall_risk > 0.6:
        insights.append("⚠️ High risk detected - close monitoring recommended")
        insights.append("📞 Consider scheduling a follow-up appointment")
    elif overall_risk > 0.4:
        insights.append("⚡ Moderate risk - stay vigilant with symptoms")
        insights.append("📊 Track vitals more frequently")
    else:
        insights.append("✅ Low risk - continue current care plan")
        insights.append("🎯 Focus on maintaining healthy habits")
    
    # Specific risk insights
    if risk_factors["cardiovascular"] > 0.4:
        insights.append("❤️ Cardiovascular concerns - monitor BP and heart rate")
    if risk_factors["respiratory"] > 0.4:
        insights.append("🫁 Respiratory attention needed - watch breathing patterns")
    if risk_factors["medication_adherence"] > 0.3:
        insights.append("💊 Medication reminder: Stay consistent with prescribed drugs")
    
    return predictions, insights


def generate_personalized_recommendations(risk_factors: Dict[str, float], profile_data: Dict) -> List[str]:
    """Generate AI-powered personalized care recommendations."""
    recommendations = []
    
    # Risk-based recommendations
    if risk_factors["cardiovascular"] > 0.3:
        recommendations.extend([
            "🚶‍♂️ Take short, gentle walks as tolerated",
            "🧘 Practice deep breathing exercises 5 minutes daily",
            "🧂 Limit sodium intake to reduce blood pressure"
        ])
    
    if risk_factors["respiratory"] > 0.3:
        recommendations.extend([
            "🌬️ Use incentive spirometer if prescribed",
            "💨 Avoid smoke and air pollutants",
            "🛏️ Sleep with head elevated"
        ])
    
    if risk_factors["infection"] > 0.3:
        recommendations.extend([
            "🧼 Wash hands frequently",
            "🌡️ Monitor temperature twice daily",
            "💧 Stay well hydrated"
        ])
    
    # General wellness
    recommendations.extend([
        "😴 Aim for 7-9 hours of quality sleep",
        "🥗 Eat nutrient-rich foods for healing",
        "📱 Use CareAnchor daily for continuous monitoring"
    ])
    
    return recommendations[:6]  # Limit to 6 recommendations


@router.get("/health-forecast")
async def get_health_forecast():
    """Generate AI-powered health predictions and insights."""
    db = await get_db()
    
    try:
        # Get latest profile and chat history
        cursor = await db.execute("""
            SELECT profile, updated_at 
            FROM clinical_profiles 
            ORDER BY updated_at DESC 
            LIMIT 1
        """)
        profile_row = await cursor.fetchone()
        
        if not profile_row:
            return {
                "status": "no_data",
                "message": "Start conversations to enable AI predictions",
                "predictions": [],
                "insights": [],
                "recommendations": []
            }
        
        profile_data = json.loads(profile_row[0])
        
        # Get recent chat history
        cursor = await db.execute("""
            SELECT role, content 
            FROM chat_logs 
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        chat_rows = await cursor.fetchall()
        chat_history = [{"role": row[0], "content": row[1]} for row in reversed(chat_rows)]
        
        # Calculate current health score (simplified)
        from backend.api.analytics import calculate_health_score
        current_score = calculate_health_score(profile_data.get("vitals", {}))
        
        # Calculate risk factors
        risk_factors = calculate_risk_factors(profile_data, chat_history)
        
        # Generate predictions
        predictions, insights = predict_health_trajectory(risk_factors, current_score)
        
        # Generate recommendations
        recommendations = generate_personalized_recommendations(risk_factors, profile_data)
        
        return {
            "status": "success",
            "current_score": current_score,
            "risk_factors": risk_factors,
            "predictions": predictions,
            "insights": insights,
            "recommendations": recommendations,
            "forecast_period": "7_days",
            "confidence": min(0.95, 0.6 + (len(chat_history) * 0.02))  # Higher confidence with more data
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Unable to generate predictions",
            "error": str(e),
            "predictions": [],
            "insights": [],
            "recommendations": []
        }
    finally:
        await db.close()


@router.get("/risk-assessment")
async def get_risk_assessment():
    """Get detailed risk assessment for various health conditions."""
    db = await get_db()
    
    try:
        # Get latest profile
        cursor = await db.execute("""
            SELECT profile 
            FROM clinical_profiles 
            ORDER BY updated_at DESC 
            LIMIT 1
        """)
        profile_row = await cursor.fetchone()
        
        if not profile_row:
            return {"risks": {}, "overall_risk": "unknown"}
        
        profile_data = json.loads(profile_row[0])
        
        # Get recent chat history
        cursor = await db.execute("""
            SELECT role, content 
            FROM chat_logs 
            ORDER BY created_at DESC 
            LIMIT 15
        """)
        chat_rows = await cursor.fetchall()
        chat_history = [{"role": row[0], "content": row[1]} for row in reversed(chat_rows)]
        
        # Calculate detailed risk factors
        risk_factors = calculate_risk_factors(profile_data, chat_history)
        
        # Determine overall risk level
        avg_risk = sum(risk_factors.values()) / len(risk_factors)
        
        if avg_risk > 0.6:
            overall_risk = "high"
        elif avg_risk > 0.3:
            overall_risk = "moderate"
        else:
            overall_risk = "low"
        
        # Format risk factors as percentages
        formatted_risks = {
            risk_type: {
                "percentage": round(value * 100),
                "level": "high" if value > 0.6 else "moderate" if value > 0.3 else "low",
                "description": get_risk_description(risk_type, value)
            }
            for risk_type, value in risk_factors.items()
        }
        
        return {
            "risks": formatted_risks,
            "overall_risk": overall_risk,
            "last_assessment": datetime.now().isoformat()
        }
        
    finally:
        await db.close()


def get_risk_description(risk_type: str, risk_value: float) -> str:
    """Get human-readable description for risk levels."""
    descriptions = {
        "cardiovascular": {
            "low": "Heart and circulation appear stable",
            "moderate": "Some cardiovascular indicators need monitoring",
            "high": "Cardiovascular system requires immediate attention"
        },
        "respiratory": {
            "low": "Breathing and oxygen levels are good",
            "moderate": "Respiratory function needs monitoring", 
            "high": "Respiratory concerns require medical evaluation"
        },
        "infection": {
            "low": "Low risk of infection complications",
            "moderate": "Watch for signs of infection",
            "high": "Possible infection - medical evaluation needed"
        },
        "medication_adherence": {
            "low": "Good medication compliance",
            "moderate": "Occasional missed medications noted",
            "high": "Poor medication adherence - review needed"
        },
        "mental_health": {
            "low": "Positive emotional well-being",
            "moderate": "Some stress or anxiety indicators",
            "high": "Mental health support may be beneficial"
        }
    }
    
    level = "high" if risk_value > 0.6 else "moderate" if risk_value > 0.3 else "low"
    return descriptions.get(risk_type, {}).get(level, "Assessment unavailable")