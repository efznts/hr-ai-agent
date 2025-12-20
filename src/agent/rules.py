
"""
HR-specific rules and logic for the agent.
"""
from datetime import datetime, timedelta
from config.settings import HR_TOPICS, RISK_LEVELS, ANOMALY_THRESHOLD


class HRRules:
    """HR domain rules for agent decision-making."""
    
    # Keywords that indicate risk by topic
    RISK_KEYWORDS = {
        "layoffs": ["сокращение", "увольнение", "layoff", "downsizing", "restructuring", "job cuts"],
        "burnout": ["выгорание", "стресс", "burnout", "overwork", "mental health", "quit"],
        "salaries": ["снижение зарплат", "задержка", "salary cut", "wage freeze"],
    }
    
    # Keywords that indicate positive signals
    POSITIVE_KEYWORDS = {
        "hiring": ["найм", "вакансии", "hiring surge", "talent acquisition", "new positions"],
        "skills": ["обучение", "развитие", "upskilling", "training program", "career growth"],
        "culture": ["well-being", "благополучие", "employee satisfaction", "engagement"],
    }
    
    @staticmethod
    def calculate_risk_score(text: str, topic: str) -> float:
        """Calculate risk score based on content."""
        text_lower = text.lower()
        score = 0.5  # Base score
        
        # Check risk keywords
        for risk_topic, keywords in HRRules.RISK_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if risk_topic == topic:
                        score += 0.15
                    else:
                        score += 0.05
        
        # Check positive keywords (reduce risk)
        for pos_topic, keywords in HRRules.POSITIVE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def get_risk_level(score: float) -> dict:
        """Get risk level based on score."""
        for level, config in RISK_LEVELS.items():
            if score >= config["threshold"]:
                return {"level": level, **config}
        return {"level": "low", **RISK_LEVELS["low"]}
    
    @staticmethod
    def should_generate_alert(risk_score: float, topic: str, user_config: dict) -> bool:
        """Determine if alert should be generated."""
        sensitivity = user_config.get("sensitivity", "medium")
        focus_topics = user_config.get("focus_topics", [])
        
        thresholds = {
            "high": 0.3,
            "medium": 0.5,
            "low": 0.7
        }
        
        threshold = thresholds.get(sensitivity, 0.5)
        
        # Lower threshold for focus topics
        if topic in focus_topics:
            threshold -= 0.15
        
        return risk_score >= threshold
    
    @staticmethod
    def detect_anomaly(current_value: float, historical: list) -> dict:
        """Detect if current value is anomalous."""
        if len(historical) < 5:
            return {"is_anomaly": False, "deviation": 0}
        
        values = [h["value"] for h in historical[-20:]]
        avg = sum(values) / len(values)
        
        if avg == 0:
            return {"is_anomaly": False, "deviation": 0}
        
        deviation = abs(current_value - avg) / avg
        is_anomaly = deviation > ANOMALY_THRESHOLD
        
        return {
            "is_anomaly": is_anomaly,
            "deviation": deviation,
            "direction": "up" if current_value > avg else "down",
            "average": avg
        }
    
    @staticmethod
    def prioritize_insight(insight: dict, user_role: str) -> int:
        """Calculate priority score for insight based on user role."""
        base_priority = 50
        
        # Risk level impact
        risk_weights = {"critical": 40, "high": 25, "medium": 10, "low": 0}
        base_priority += risk_weights.get(insight.get("risk_level", "low"), 0)
        
        # Urgency impact
        urgency_weights = {"immediate": 30, "week": 15, "month": 5}
        base_priority += urgency_weights.get(insight.get("urgency", "month"), 0)
        
        return min(100, base_priority)
    
    @staticmethod
    def get_topic_trend_summary(trend_data: list) -> dict:
        """Summarize trend for a topic."""
        if len(trend_data) < 2:
            return {"direction": "stable", "change": 0, "description": "Недостаточно данных"}
        
        recent = trend_data[-5:] if len(trend_data) >= 5 else trend_data
        older = trend_data[-10:-5] if len(trend_data) >= 10 else trend_data[:len(trend_data)//2]
        
        recent_avg = sum(r["value"] for r in recent) / len(recent)
        older_avg = sum(o["value"] for o in older) / len(older) if older else recent_avg
        
        if older_avg == 0:
            change = 0
        else:
            change = ((recent_avg - older_avg) / older_avg) * 100
        
        if change > 10:
            direction = "up"
            desc = f"Рост на {change:.1f}%"
        elif change < -10:
            direction = "down"
            desc = f"Снижение на {abs(change):.1f}%"
        else:
            direction = "stable"
            desc = "Стабильно"
        
        return {"direction": direction, "change": change, "description": desc}


hr_rules = HRRules()

