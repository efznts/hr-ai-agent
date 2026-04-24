"""
config/sources_catalog.py
--------------------------
Курируемый каталог RSS-источников для HR-агрегатора.

Критерии отбора источников:
  - Авторитет:        признанные издания / организации в HR, бизнес, tech сфере
  - Обновляемость:    активный RSS-фид, публикации не реже 2-3 раз в неделю
  - HR-релевантность: контент пересекается хотя бы с одной темой из HR_TOPICS
  - Язык:             ru или en (смешанные не добавляются)
  - RSS:              фид должен быть публично доступен без авторизации

Статус is_active=False означает кандидата для A/B-тестирования —
источник не тянется агентом, пока не переведён в активный.
"""

from dataclasses import dataclass
from typing import Literal, Optional


Category = Literal["hr_official", "media", "community", "tech", "biz"]
Lang = Literal["ru", "en"]


@dataclass
class Source:
    source_id: str        # slug kebab-case, уникальный идентификатор
    name: str             # читаемое название
    url: str              # URL RSS-фида
    lang: Lang            # язык контента
    category: Category    # тематическая категория
    is_active: bool       # участвует ли в парсинге прямо сейчас
    quality_score: float  # субъективная оценка качества контента 0.0–1.0
    added_date: str       # дата добавления ISO 8601 (YYYY-MM-DD)
    description: str = "" # краткое описание источника


SOURCES: list[Source] = [

    # ── hr_official ───────────────────────────────────────────────────────────

    Source(
        source_id="shrm-news",
        name="SHRM News",
        url="https://www.shrm.org/rss/pages/rss.aspx",
        lang="en",
        category="hr_official",
        is_active=True,
        quality_score=0.90,
        added_date="2024-01-01",
        description="Официальный фид Society for Human Resource Management.",
    ),
    Source(
        source_id="atd-org",
        name="ATD (Association for Talent Development)",
        url="https://www.td.org/rss",
        lang="en",
        category="hr_official",
        is_active=True,
        quality_score=0.85,
        added_date="2025-01-15",
        description="Лидирующая ассоциация по развитию талантов и L&D.",
    ),
    Source(
        source_id="worldatwork",
        name="WorldatWork",
        url="https://worldatwork.org/feed",
        lang="en",
        category="hr_official",
        is_active=False,  # A/B кандидат
        quality_score=0.80,
        added_date="2025-04-22",
        description="Ассоциация специалистов по компенсациям и льготам (Total Rewards).",
    ),
    Source(
        source_id="hr-com",
        name="HR.com",
        url="https://www.hr.com/en/rss_feeds/",
        lang="en",
        category="hr_official",
        is_active=False,  # A/B кандидат
        quality_score=0.75,
        added_date="2025-04-22",
        description="Комьюнити и новости для HR-профессионалов.",
    ),

    # ── media EN ──────────────────────────────────────────────────────────────

    Source(
        source_id="hbr",
        name="Harvard Business Review",
        url="https://hbr.org/feed",
        lang="en",
        category="media",
        is_active=True,
        quality_score=0.90,
        added_date="2024-01-01",
        description="Академически строгие статьи по менеджменту, лидерству и HR.",
    ),
    Source(
        source_id="fast-company-work",
        name="Fast Company — Work Life",
        url="https://www.fastcompany.com/work-life/rss",
        lang="en",
        category="media",
        is_active=True,
        quality_score=0.80,
        added_date="2025-01-15",
        description="Трудовая культура, карьера, будущее работы.",
    ),
    Source(
        source_id="forbes-work",
        name="Forbes — Leadership",
        url="https://www.forbes.com/leadership/feed/",
        lang="en",
        category="media",
        is_active=True,
        quality_score=0.78,
        added_date="2025-01-15",
        description="HR-аналитика и истории с уклоном в бизнес-результат.",
    ),
    Source(
        source_id="fortune-at-work",
        name="Fortune — At Work",
        url="https://fortune.com/section/at-work/feed/",
        lang="en",
        category="media",
        is_active=True,
        quality_score=0.80,
        added_date="2025-01-15",
        description="Найм, увольнения, тренды рынка труда от Fortune.",
    ),
    Source(
        source_id="the-muse",
        name="The Muse",
        url="https://www.themuse.com/rss",
        lang="en",
        category="media",
        is_active=True,
        quality_score=0.70,
        added_date="2024-01-01",
        description="Карьерные советы и истории для соискателей и рекрутеров.",
    ),

    # ── media RU ──────────────────────────────────────────────────────────────

    Source(
        source_id="vc-ru",
        name="VC.ru",
        url="https://vc.ru/feed",
        lang="ru",
        category="media",
        is_active=True,
        quality_score=0.75,
        added_date="2024-01-01",
        description="Бизнес и технологии, регулярные материалы о рынке труда в IT.",
    ),
    Source(
        source_id="rbc-hr",
        name="РБК — Карьера",
        url="https://rbc.ru/v10/ajax/get-rss-news/person/",
        lang="ru",
        category="media",
        is_active=True,
        quality_score=0.82,
        added_date="2025-01-15",
        description="Новости рынка труда, зарплатные исследования, увольнения.",
    ),
    Source(
        source_id="vedomosti-hr",
        name="Ведомости — Менеджмент",
        url="https://www.vedomosti.ru/rss/rubric/management",
        lang="ru",
        category="media",
        is_active=True,
        quality_score=0.83,
        added_date="2025-01-15",
        description="Деловые новости с фокусом на управление персоналом.",
    ),
    Source(
        source_id="kommersant-hr",
        name="Коммерсантъ — Управление",
        url="https://www.kommersant.ru/RSS/section-management.xml",
        lang="ru",
        category="media",
        is_active=False,  # A/B кандидат
        quality_score=0.80,
        added_date="2025-04-22",
        description="HR-материалы из раздела «Менеджмент» Коммерсанта.",
    ),
    Source(
        source_id="hr-tv-ru",
        name="HR-tv.ru",
        url="https://hr-tv.ru/rss.xml",
        lang="ru",
        category="media",
        is_active=False,  # A/B кандидат
        quality_score=0.72,
        added_date="2025-04-22",
        description="Российское HR-медиа: интервью, кейсы, аналитика.",
    ),

    # ── community ─────────────────────────────────────────────────────────────

    Source(
        source_id="habr",
        name="Habr",
        url="https://habr.com/ru/rss/all/",
        lang="ru",
        category="community",
        is_active=True,
        quality_score=0.75,
        added_date="2024-01-01",
        description="IT-сообщество: карьера в технологиях, управление командами.",
    ),
    Source(
        source_id="hacker-news",
        name="Hacker News",
        url="https://news.ycombinator.com/rss",
        lang="en",
        category="community",
        is_active=True,
        quality_score=0.72,
        added_date="2024-01-01",
        description="Технологическое сообщество: стартапы, найм, рынок труда в tech.",
    ),
    Source(
        source_id="reddit-humanresources",
        name="Reddit r/humanresources",
        url="https://www.reddit.com/r/humanresources/.rss",
        lang="en",
        category="community",
        is_active=True,
        quality_score=0.70,
        added_date="2025-01-15",
        description="Обсуждения практикующих HR-специалистов со всего мира.",
    ),
    Source(
        source_id="reddit-cs-careers",
        name="Reddit r/cscareerquestions",
        url="https://www.reddit.com/r/cscareerquestions/.rss",
        lang="en",
        category="community",
        is_active=False,  # A/B кандидат — tech-уклон, слабо релевантен HR
        quality_score=0.65,
        added_date="2024-01-01",
        description="Карьерные вопросы в IT — полезно для рекрутинга разработчиков.",
    ),
    Source(
        source_id="medium-hr",
        name="Medium — Human Resources",
        url="https://medium.com/feed/tag/human-resources",
        lang="en",
        category="community",
        is_active=True,
        quality_score=0.68,
        added_date="2025-01-15",
        description="Авторские колонки практиков по HR, культуре и лидерству.",
    ),
    Source(
        source_id="hr-ru",
        name="HR.ru",
        url="https://hr.ru/rss/news.xml",
        lang="ru",
        category="community",
        is_active=True,
        quality_score=0.72,
        added_date="2025-04-22",
        description="Российское HR-комьюнити: вакансии, новости, кейсы.",
    ),

    # ── tech ──────────────────────────────────────────────────────────────────

    Source(
        source_id="techcrunch-hr",
        name="TechCrunch — HR",
        url="https://techcrunch.com/tag/hr/feed/",
        lang="en",
        category="tech",
        is_active=True,
        quality_score=0.78,
        added_date="2025-01-15",
        description="HR-tech стартапы, инструменты рекрутинга, автоматизация.",
    ),
    Source(
        source_id="wired-work",
        name="Wired — Work",
        url="https://www.wired.com/feed/tag/work/rss",
        lang="en",
        category="tech",
        is_active=True,
        quality_score=0.80,
        added_date="2025-04-22",
        description="Влияние технологий на труд, удалёнка, AI на рабочем месте.",
    ),
    Source(
        source_id="venturebeat-ai",
        name="VentureBeat — AI",
        url="https://venturebeat.com/category/ai/feed/",
        lang="en",
        category="tech",
        is_active=False,  # A/B кандидат
        quality_score=0.74,
        added_date="2025-04-22",
        description="AI-инструменты для HR, автоматизация найма и онбординга.",
    ),

    # ── biz ───────────────────────────────────────────────────────────────────

    Source(
        source_id="economist-business",
        name="The Economist — Business",
        url="https://www.economist.com/business/rss.xml",
        lang="en",
        category="biz",
        is_active=True,
        quality_score=0.88,
        added_date="2025-04-22",
        description="Глобальные бизнес-тренды, рынок труда, управление компаниями.",
    ),
    Source(
        source_id="mit-sloan",
        name="MIT Sloan Management Review",
        url="https://sloanreview.mit.edu/feed/",
        lang="en",
        category="biz",
        is_active=True,
        quality_score=0.87,
        added_date="2025-04-22",
        description="Исследования по менеджменту, лидерству и будущему работы.",
    ),
]


# ── Экспорт ───────────────────────────────────────────────────────────────────

def get_all_sources() -> list[Source]:
    """Вернуть все источники из каталога."""
    return SOURCES


def get_active_sources() -> list[Source]:
    """Вернуть только активные источники (is_active=True)."""
    return [s for s in SOURCES if s.is_active]


def get_by_id(source_id: str) -> Optional[Source]:
    """Найти источник по его slug-идентификатору. Вернуть None если не найден."""
    return next((s for s in SOURCES if s.source_id == source_id), None)


def get_by_category(category: Category) -> list[Source]:
    """Вернуть все источники заданной категории (активные и неактивные)."""
    return [s for s in SOURCES if s.category == category]


def get_by_lang(lang: Lang) -> list[Source]:
    """Вернуть все источники заданного языка."""
    return [s for s in SOURCES if s.lang == lang]
