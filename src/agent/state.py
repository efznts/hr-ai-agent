
"""
Agent state management - memory of observations and insights.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.settings import DATA_DIR


class AgentState:
    """Manages persistent state for the HR agent."""
    
    def __init__(self):
        self.state_file = DATA_DIR / "state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return self._default_state()
    
    def _default_state(self) -> dict:
        return {
            "last_check": None,
            "observations": [],
            "insights": [],
            "trends": {
                "hiring": [],
                "layoffs": [],
                "salaries": [],
                "skills": [],
                "burnout": [],
                "culture": [],
                "diversity": []
            },
            "alerts": [],
            "processed_urls": [],
            "metrics": {
                "total_sources_checked": 0,
                "total_insights_generated": 0,
                "anomalies_detected": 0
            }
        }
    
    def save(self):
        """Persist state to file."""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2, default=str)
    
    def add_observation(self, obs: dict):
        """Add new observation to memory."""
        obs["timestamp"] = datetime.now().isoformat()
        self.state["observations"].append(obs)
        # Keep last 500 observations
        self.state["observations"] = self.state["observations"][-500:]
        self.save()
    
    def add_insight(self, insight: dict):
        """Add generated insight."""
        insight["generated_at"] = datetime.now().isoformat()
        self.state["insights"].insert(0, insight)
        # Keep last 100 insights
        self.state["insights"] = self.state["insights"][:100]
        self.state["metrics"]["total_insights_generated"] += 1
        self.save()
    
    def add_trend_point(self, topic: str, value: float):
        """Add data point to trend tracking."""
        point = {
            "timestamp": datetime.now().isoformat(),
            "value": value
        }
        if topic in self.state["trends"]:
            self.state["trends"][topic].append(point)
            # Keep last 100 points per topic
            self.state["trends"][topic] = self.state["trends"][topic][-100:]
        self.save()
    
    def add_alert(self, alert: dict):
        """Add alert to state."""
        alert["created_at"] = datetime.now().isoformat()
        alert["acknowledged"] = False
        self.state["alerts"].insert(0, alert)
        self.state["alerts"] = self.state["alerts"][:50]
        self.save()
    
    def is_url_processed(self, url: str) -> bool:
        """Check if URL was already processed."""
        return url in self.state["processed_urls"]
    
    def mark_url_processed(self, url: str):
        """Mark URL as processed."""
        if url not in self.state["processed_urls"]:
            self.state["processed_urls"].append(url)
            # Keep last 1000 URLs
            self.state["processed_urls"] = self.state["processed_urls"][-1000:]
            self.save()
    
    def get_recent_insights(self, limit: int = 10) -> list:
        """Get recent insights."""
        return self.state["insights"][:limit]
    
    def get_trend_data(self, topic: str) -> list:
        """Get trend data for topic."""
        return self.state["trends"].get(topic, [])
    
    def get_unacknowledged_alerts(self) -> list:
        """Get alerts that need attention."""
        return [a for a in self.state["alerts"] if not a.get("acknowledged")]
    
    def update_last_check(self):
        """Update last check timestamp."""
        self.state["last_check"] = datetime.now().isoformat()
        self.state["metrics"]["total_sources_checked"] += 1
        self.save()
    
    def record_anomaly(self):
        """Increment anomaly counter."""
        self.state["metrics"]["anomalies_detected"] += 1
        self.save()
    
    def reset(self):
        """Reset agent state to initial."""
        self.state = self._default_state()
        self.save()



# Singleton
agent_state = AgentState()
