from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException
from backend.config import settings
from backend.db.sqlite import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


def calculate_health_score(vitals: Dict[str, Any]) -> int:
    """Calculate overall health score (0-100) based on vital signs."""
    if not vitals:
        return 85  # Default score when no vitals available
    
    score = 100
    deductions = 0
    
    # Blood Pressure scoring
    systolic = vitals.get("systolic_bp")
    diastolic = vitals.get("diastolic_bp")
    
    if systolic:
        if systolic >= settings.systolic_bp_crit_max:  # >= 180
            deductions += 30
        elif systolic >= settings.systolic_bp_warn_max:  # >= 160
            deductions += 15
        elif systolic < 90:  # Too low
            deductions += 20
    
    if diastolic:
        if diastolic >= settings.diastolic_bp_crit_max:  # >= 120
            deductions += 25
        elif diastolic >= settings.diastolic_bp_warn_max:  # >= 100
            deductions += 10
        elif diastolic < 60:  # Too low
            deductions += 15
    
    # Heart Rate scoring
    heart_rate = vitals.get("heart_rate")
    if heart_rate:
        if heart_rate <= settings.heart_rate_crit_min or heart_rate >= settings.heart_rate_crit_max:  # <= 40 or >= 140
            deductions += 25
        elif heart_rate <= settings.heart_rate_warn_min or heart_rate >= settings.heart_rate_warn_max:  # <= 50 or >= 110
            deductions += 10
    
    # Oxygen Saturation scoring
    sp_o2 = vitals.get("sp_o2")
    if sp_o2:
        if sp_o2 <= settings.sp_o2_crit_min:  # <= 90
            deductions += 35
        elif sp_o2 <= settings.sp_o2_warn_min:  # <= 94
            deductions += 15
    
    # Temperature scoring
    temperature = vitals.get("temperature")
    if temperature:
        if temperature >= settings.temperature_crit_max:  # >= 39.5
            deductions += 20
        elif temperature >= settings.temperature_warn_max:  # >= 38.0
            deductions += 8
        elif temperature < 35.0:  # Too low
            deductions += 25
    
    final_score = max(0, score - deductions)
    return final_score


def get_vital_status(vital_name: str, value: float | None) -> str:
    """Get status for a specific vital sign."""
    if value is None:
        return "unknown"
    
    if vital_name == "systolic_bp":
        if value >= settings.systolic_bp_crit_max:
            return "critical"
        elif value >= settings.systolic_bp_warn_max:
            return "warning"
        elif value < 90:
            return "warning"
        return "normal"
    
    elif vital_name == "diastolic_bp":
        if value >= settings.diastolic_bp_crit_max:
            return "critical"
        elif value >= settings.diastolic_bp_warn_max:
            return "warning"
        elif value < 60:
            return "warning"
        return "normal"
    
    elif vital_name == "heart_rate":
        if value <= settings.heart_rate_crit_min or value >= settings.heart_rate_crit_max:
            return "critical"
        elif value <= settings.heart_rate_warn_min or value >= settings.heart_rate_warn_max:
            return "warning"
        return "normal"
    
    elif vital_name == "sp_o2":
        if value <= settings.sp_o2_crit_min:
            return "critical"
        elif value <= settings.sp_o2_warn_min:
            return "warning"
        return "normal"
    
    elif vital_name == "temperature":
        if value >= settings.temperature_crit_max:
            return "critical"
        elif value >= settings.temperature_warn_max:
            return "warning"
        elif value < 35.0:
            return "warning"
        return "normal"
    
    return "normal"


def get_recommendations(health_score: int, vital_statuses: Dict[str, str]) -> List[str]:
    """Generate health recommendations based on score and vital signs."""
    recommendations = []
    
    # Critical conditions
    critical_vitals = [k for k, v in vital_statuses.items() if v == "critical"]
    if critical_vitals:
        recommendations.append("🚨 Seek immediate medical attention - critical vital signs detected")
        return recommendations
    
    # Warning conditions
    warning_vitals = [k for k, v in vital_statuses.items() if v == "warning"]
    if warning_vitals:
        recommendations.append("⚠️ Contact your doctor within 24 hours - elevated vital signs")
        recommendations.append("📊 Monitor and recheck vital signs in 2-4 hours")
    
    # Score-based recommendations
    if health_score >= 90:
        recommendations.append("✅ Excellent recovery progress - keep up the great work!")
        recommendations.append("🏃‍♂️ Continue with light activities as tolerated")
    elif health_score >= 75:
        recommendations.append("👍 Good recovery progress - stay consistent with care plan")
        recommendations.append("💧 Stay hydrated and get adequate rest")
    elif health_score >= 60:
        recommendations.append("📈 Recovery is progressing - focus on gradual improvement")
        recommendations.append("🩺 Consider scheduling a follow-up appointment")
    else:
        recommendations.append("🔍 Close monitoring needed - discuss concerns with your care team")
        recommendations.append("📞 Contact your healthcare provider for guidance")
    
    # General recommendations
    if not recommendations:
        recommendations.extend([
            "💊 Take medications as prescribed",
            "🍎 Maintain a balanced diet",
            "😴 Ensure adequate rest and sleep"
        ])
    
    return recommendations


@router.get("/health-overview")
async def get_health_overview():
    """Get comprehensive health analytics for the dashboard."""
    db = await get_db()
    
    try:
        # Get latest clinical profile
        cursor = await db.execute("""
            SELECT profile, updated_at 
            FROM clinical_profiles 
            ORDER BY updated_at DESC 
            LIMIT 1
        """)
        profile_row = await cursor.fetchone()
        
        if not profile_row:
            return {
                "health_score": 85,
                "status": "no_data",
                "message": "Start your first check-in to begin health tracking",
                "vital_signs": {},
                "recommendations": [
                    "👋 Welcome to CareAnchor!",
                    "💬 Start a conversation to track your recovery",
                    "📊 Your health metrics will appear here"
                ],
                "last_updated": None,
                "trend": "stable"
            }
        
        profile_data = json.loads(profile_row[0])
        vitals = profile_data.get("vitals", {})
        
        # Calculate health score
        health_score = calculate_health_score(vitals)
        
        # Get vital statuses
        vital_statuses = {}
        for vital_name in ["systolic_bp", "diastolic_bp", "heart_rate", "sp_o2", "temperature"]:
            vital_statuses[vital_name] = get_vital_status(vital_name, vitals.get(vital_name))
        
        # Determine overall status
        if any(status == "critical" for status in vital_statuses.values()):
            overall_status = "critical"
        elif any(status == "warning" for status in vital_statuses.values()):
            overall_status = "warning"
        else:
            overall_status = "normal"
        
        # Generate recommendations
        recommendations = get_recommendations(health_score, vital_statuses)
        
        # Calculate trend (simplified - compare with 7 days ago)
        week_ago = datetime.now() - timedelta(days=7)
        cursor = await db.execute("""
            SELECT profile 
            FROM clinical_profiles 
            WHERE updated_at <= ?
            ORDER BY updated_at DESC 
            LIMIT 1
        """, (week_ago.isoformat(),))
        old_profile_row = await cursor.fetchone()
        
        trend = "stable"
        if old_profile_row:
            old_profile = json.loads(old_profile_row[0])
            old_score = calculate_health_score(old_profile.get("vitals", {}))
            
            if health_score > old_score + 5:
                trend = "improving"
            elif health_score < old_score - 5:
                trend = "declining"
        
        # Format vital signs for display
        formatted_vitals = {}
        if vitals.get("systolic_bp") and vitals.get("diastolic_bp"):
            formatted_vitals["blood_pressure"] = {
                "value": f"{vitals['systolic_bp']}/{vitals['diastolic_bp']} mmHg",
                "status": get_vital_status("systolic_bp", vitals["systolic_bp"])
            }
        
        if vitals.get("heart_rate"):
            formatted_vitals["heart_rate"] = {
                "value": f"{vitals['heart_rate']} bpm",
                "status": get_vital_status("heart_rate", vitals["heart_rate"])
            }
        
        if vitals.get("sp_o2"):
            formatted_vitals["oxygen_saturation"] = {
                "value": f"{vitals['sp_o2']}%",
                "status": get_vital_status("sp_o2", vitals["sp_o2"])
            }
        
        if vitals.get("temperature"):
            formatted_vitals["temperature"] = {
                "value": f"{vitals['temperature']}°C",
                "status": get_vital_status("temperature", vitals["temperature"])
            }
        
        return {
            "health_score": health_score,
            "status": overall_status,
            "message": get_status_message(overall_status, health_score),
            "vital_signs": formatted_vitals,
            "recommendations": recommendations,
            "last_updated": profile_row[1],
            "trend": trend,
            "symptoms_count": len(profile_data.get("symptoms", [])),
            "medications_count": len(profile_data.get("medications", []))
        }
    finally:
        await db.close()


def get_status_message(status: str, score: int) -> str:
    """Get user-friendly status message."""
    if status == "critical":
        return "Immediate medical attention recommended"
    elif status == "warning":
        return "Some vitals need monitoring - contact your doctor"
    elif score >= 90:
        return "Excellent recovery progress!"
    elif score >= 75:
        return "Good recovery progress"
    elif score >= 60:
        return "Recovery is progressing steadily"
    else:
        return "Close monitoring recommended"


@router.get("/safety-alerts")
async def get_recent_safety_alerts():
    """Get recent safety alerts and events."""
    db = await get_db()
    
    try:
        # Get recent safety events from the last 30 days
        week_ago = datetime.now() - timedelta(days=30)
        cursor = await db.execute("""
            SELECT severity, alerts, risk_score, created_at
            FROM safety_events 
            WHERE created_at >= ?
            ORDER BY created_at DESC 
            LIMIT 10
        """, (week_ago.isoformat(),))
        alerts = await cursor.fetchall()
        
        formatted_alerts = []
        for alert in alerts:
            alerts_list = json.loads(alert[1])  # alerts column
            formatted_alerts.append({
                "severity": alert[0],  # severity column
                "alerts": alerts_list,
                "risk_score": alert[2],  # risk_score column
                "timestamp": alert[3]   # created_at column
            })
        
        return {
            "recent_alerts": formatted_alerts,
            "total_alerts": len(formatted_alerts),
            "critical_count": len([a for a in formatted_alerts if a["severity"] == "critical"]),
            "warning_count": len([a for a in formatted_alerts if a["severity"] == "warn"])
        }
    finally:
        await db.close()
