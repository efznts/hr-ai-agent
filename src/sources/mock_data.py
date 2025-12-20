
"""
Mock data generator for demonstration purposes.
All mock data is clearly marked.
"""
import random
import uuid
from datetime import datetime


class MockDataGenerator:
    """
    Generates realistic HR news mock data for demo.
    
    NOTE: This is clearly marked mock data for hackathon demonstration.
    In production, this would be replaced with additional real data sources.
    """
    
    MOCK_NEWS = [
        {
            "title": "Tech Giants Announce Major Layoffs Amid Economic Uncertainty",
            "content": "Several major technology companies have announced significant workforce reductions. Meta, Amazon, and Google are among the companies implementing layoffs affecting thousands of employees. Industry analysts suggest this trend may continue into 2024.",
            "topic": "layoffs",
            "lang": "en"
        },
        {
            "title": "Remote Work Burnout Reaches Record Levels in Survey",
            "content": "A new workplace survey reveals that 67% of remote workers report experiencing burnout symptoms. The study highlights concerns about work-life balance and the need for better mental health support in distributed teams.",
            "topic": "burnout",
            "lang": "en"
        },
        {
            "title": "AI Skills Gap Widens as Demand Outpaces Training",
            "content": "Companies are struggling to find qualified AI talent as demand for machine learning engineers and data scientists continues to surge. HR leaders report that upskilling existing employees is becoming a priority.",
            "topic": "skills",
            "lang": "en"
        },
        {
            "title": "Salary Transparency Laws Drive Compensation Changes",
            "content": "New salary transparency regulations are forcing companies to review their compensation structures. HR departments are implementing pay equity audits and adjusting salary bands to ensure compliance.",
            "topic": "salaries",
            "lang": "en"
        },
        {
            "title": "Компании увеличивают бюджеты на найм IT-специалистов",
            "content": "Российские компании планируют увеличить расходы на привлечение IT-талантов на 30% в следующем году. Конкуренция за квалифицированных разработчиков остаётся высокой.",
            "topic": "hiring",
            "lang": "ru"
        },
        {
            "title": "Diversity Initiatives Show Mixed Results in Annual Report",
            "content": "The latest diversity and inclusion metrics reveal progress in some areas while highlighting persistent gaps. Companies are reevaluating their D&I strategies and investing in new approaches.",
            "topic": "diversity",
            "lang": "en"
        },
        {
            "title": "Four-Day Work Week Trials Report Positive Outcomes",
            "content": "Pilot programs for the four-day work week show improved employee satisfaction and maintained productivity. More companies are considering implementing flexible work schedules.",
            "topic": "culture",
            "lang": "en"
        },
        {
            "title": "Массовые сокращения в финтех-секторе",
            "content": "Ряд финтех-компаний объявили о сокращении штата на 15-20%. Эксперты связывают это с изменением экономических условий и переоценкой бизнес-моделей.",
            "topic": "layoffs",
            "lang": "ru"
        }
    ]
    
    def generate_batch(self, count: int = 5) -> list:
        """Generate a batch of mock news items."""
        items = []
        selected = random.sample(self.MOCK_NEWS, min(count, len(self.MOCK_NEWS)))
        
        for news in selected:
            item = {
                "id": f"mock_{uuid.uuid4().hex[:8]}",
                "url": f"https://mock-news.example.com/{uuid.uuid4().hex[:8]}",
                "title": news["title"],
                "content": news["content"],
                "published": datetime.now().isoformat(),
                "source": "Mock HR News (Demo)",
                "lang": news["lang"],
                "type": "mock",
                "is_mock": True  # Clearly marked as mock data
            }
            items.append(item)
        
        return items
