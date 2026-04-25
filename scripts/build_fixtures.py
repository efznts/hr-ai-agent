"""
scripts/build_fixtures.py
--------------------------
Собирает реальные новости из активных RSS-источников и строит:
  - tests/fixtures/labeled_news.json   (50 размеченных новостей)
  - docs/topic_coverage_matrix.csv     (реальное покрытие тем)

Использование:
  pip install feedparser langdetect openai python-dotenv
  python scripts/build_fixtures.py

Требует OPENAI_API_KEY в .env (используется для авто-лейблинга тем и рисков).
Финальная разметка должна быть верифицирована экспертом вручную.
"""

import json
import csv
import os
import time
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter

import feedparser
from langdetect import detect, LangDetectException
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Конфиг ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "tests" / "fixtures"
DOCS_DIR = ROOT / "docs"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_TOTAL = 50          # итоговое кол-во новостей
RU_RATIO = 0.60            # доля RU
EN_RATIO = 0.40            # доля EN
ITEMS_PER_SOURCE = 8       # сколько брать из каждого фида (потом отбираем)
MAX_CONTENT_SENTENCES = 5  # обрезаем контент

HR_TOPICS = [
    "hiring", "layoffs", "salaries", "skills",
    "burnout", "culture", "diversity"
]

RISK_LEVELS = ["critical", "high", "medium", "low"]

# Активные источники из sources_catalog.py
ACTIVE_SOURCES = [
    {"source_id": "shrm-news",            "url": "https://www.shrm.org/rss/pages/rss.aspx",                   "lang": "en", "category": "hr_official"},
    {"source_id": "atd-org",              "url": "https://www.td.org/rss",                                     "lang": "en", "category": "hr_official"},
    {"source_id": "hbr",                  "url": "https://hbr.org/feed",                                       "lang": "en", "category": "media"},
    {"source_id": "fast-company-work",    "url": "https://www.fastcompany.com/work-life/rss",                  "lang": "en", "category": "media"},
    {"source_id": "forbes-work",          "url": "https://www.forbes.com/leadership/feed/",                    "lang": "en", "category": "media"},
    {"source_id": "fortune-at-work",      "url": "https://fortune.com/section/at-work/feed/",                  "lang": "en", "category": "media"},
    {"source_id": "the-muse",             "url": "https://www.themuse.com/rss",                                "lang": "en", "category": "media"},
    {"source_id": "vc-ru",                "url": "https://vc.ru/feed",                                         "lang": "ru", "category": "media"},
    {"source_id": "rbc-hr",               "url": "https://rbc.ru/v10/ajax/get-rss-news/person/",               "lang": "ru", "category": "media"},
    {"source_id": "vedomosti-hr",         "url": "https://www.vedomosti.ru/rss/rubric/management",             "lang": "ru", "category": "media"},
    {"source_id": "habr",                 "url": "https://habr.com/ru/rss/all/",                               "lang": "ru", "category": "community"},
    {"source_id": "hacker-news",          "url": "https://news.ycombinator.com/rss",                           "lang": "en", "category": "community"},
    {"source_id": "reddit-humanresources","url": "https://www.reddit.com/r/humanresources/.rss",               "lang": "en", "category": "community"},
    {"source_id": "medium-hr",            "url": "https://medium.com/feed/tag/human-resources",                "lang": "en", "category": "community"},
    {"source_id": "hr-ru",                "url": "https://hr.ru/rss/news.xml",                                 "lang": "ru", "category": "community"},
    {"source_id": "techcrunch-hr",        "url": "https://techcrunch.com/tag/hr/feed/",                        "lang": "en", "category": "tech"},
    {"source_id": "wired-work",           "url": "https://www.wired.com/feed/tag/work/rss",                    "lang": "en", "category": "tech"},
    {"source_id": "economist-business",   "url": "https://www.economist.com/business/rss.xml",                 "lang": "en", "category": "biz"},
    {"source_id": "mit-sloan",            "url": "https://sloanreview.mit.edu/feed/",                          "lang": "en", "category": "biz"},
]

# ── OpenAI helper ─────────────────────────────────────────────────────────────

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LABEL_PROMPT = """You are an HR analyst labeling news for an HR intelligence system.

Given a news title and content, return a JSON object with:
- "expected_topic": one of {topics}
- "expected_risk_level": one of {risks}  
- "expert_notes": 1-2 sentences explaining the label in Russian

Risk level guidelines:
- critical: mass layoffs 1000+, systemic crisis, major legal violations, >50% burnout rates
- high: significant trend affecting many workers/companies, notable financial impact
- medium: industry trend, moderate impact, mixed signals
- low: positive news, best practices, minor developments

Respond ONLY with valid JSON, no markdown.

Title: {{title}}
Content: {{content}}
Lang: {{lang}}
""".format(topics=HR_TOPICS, risks=RISK_LEVELS)


def label_with_llm(title: str, content: str, lang: str) -> dict:
    """Авто-лейблинг через OpenAI. Fallback на manual если нет ключа."""
    prompt = LABEL_PROMPT.replace("{{title}}", title) \
                         .replace("{{content}}", content) \
                         .replace("{{lang}}", lang)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
        )
        raw = resp.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  ⚠ LLM error: {e} — помечаем как NEEDS_REVIEW")
        return {
            "expected_topic": "NEEDS_REVIEW",
            "expected_risk_level": "NEEDS_REVIEW",
            "expert_notes": "Требует ручной разметки"
        }


# ── RSS fetcher ───────────────────────────────────────────────────────────────

def fetch_feed(source: dict, max_items: int = ITEMS_PER_SOURCE) -> list[dict]:
    """Тянет RSS и возвращает список сырых статей."""
    print(f"  Fetching {source['source_id']} ...", end=" ", flush=True)
    try:
        feed = feedparser.parse(source["url"])
        entries = feed.entries[:max_items]
        results = []
        for entry in entries:
            title = entry.get("title", "").strip()
            if not title:
                continue
            # Контент: summary или content[0].value
            raw_content = ""
            if hasattr(entry, "content") and entry.content:
                raw_content = entry.content[0].value
            elif hasattr(entry, "summary"):
                raw_content = entry.summary
            # Убираем HTML-теги грубо
            import re
            clean = re.sub(r"<[^>]+>", " ", raw_content)
            clean = re.sub(r"\s+", " ", clean).strip()
            # Берём первые N предложений
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if len(s.strip()) > 20]
            content = " ".join(sentences[:MAX_CONTENT_SENTENCES])
            if len(content) < 50:
                continue
            url = entry.get("link", source["url"])
            results.append({
                "source_id": source["source_id"],
                "source_lang": source["lang"],
                "url": url,
                "title": title,
                "content": content,
            })
        print(f"→ {len(results)} items")
        return results
    except Exception as e:
        print(f"→ ERROR: {e}")
        return []


def detect_lang(title: str, content: str) -> str:
    try:
        return detect(title + " " + content[:200])
    except LangDetectException:
        return "unknown"


# ── Main pipeline ─────────────────────────────────────────────────────────────

def build_labeled_news() -> tuple[list[dict], dict]:
    """
    Возвращает:
      - список размеченных новостей (50 штук)
      - словарь {source_id: Counter(topic -> count)} для матрицы
    """
    print("\n=== Шаг 1: Сбор новостей из RSS ===")
    all_items = []
    for source in ACTIVE_SOURCES:
        items = fetch_feed(source)
        all_items.extend(items)
        time.sleep(0.5)  # вежливый таймаут

    print(f"\nВсего собрано: {len(all_items)} статей")

    print("\n=== Шаг 2: Дедупликация и фильтрация ===")
    seen_urls = set()
    seen_titles = set()
    unique = []
    for item in all_items:
        url_hash = hashlib.md5(item["url"].encode()).hexdigest()
        title_lower = item["title"].lower()[:80]
        if url_hash in seen_urls or title_lower in seen_titles:
            continue
        seen_urls.add(url_hash)
        seen_titles.add(title_lower)
        unique.append(item)

    print(f"После дедупликации: {len(unique)} статей")

    print("\n=== Шаг 3: Определение языка и балансировка ===")
    ru_items = []
    en_items = []
    for item in unique:
        detected = detect_lang(item["title"], item["content"])
        actual_lang = detected if detected in ("ru", "en") else item["source_lang"]
        item["lang"] = actual_lang
        if actual_lang == "ru":
            ru_items.append(item)
        else:
            en_items.append(item)

    print(f"RU: {len(ru_items)}, EN: {len(en_items)}")

    # Балансируем ~60/40
    target_ru = int(TARGET_TOTAL * RU_RATIO)  # 30
    target_en = TARGET_TOTAL - target_ru       # 20
    selected_ru = ru_items[:target_ru]
    selected_en = en_items[:target_en]
    selected = selected_ru + selected_en

    print(f"Отобрано: RU={len(selected_ru)}, EN={len(selected_en)}, итого={len(selected)}")

    print("\n=== Шаг 4: Авто-лейблинг через LLM ===")
    labeled = []
    source_topic_counts = defaultdict(Counter)  # для матрицы

    for i, item in enumerate(selected):
        news_id = f"news_{i+1:03d}"
        print(f"  [{i+1}/{len(selected)}] {news_id}: {item['title'][:60]}...")
        labels = label_with_llm(item["title"], item["content"], item["lang"])
        time.sleep(0.3)  # rate limit

        record = {
            "id": news_id,
            "url": item["url"],
            "title": item["title"],
            "content": item["content"],
            "lang": item["lang"],
            "source_id": item["source_id"],  # для матрицы, потом можно убрать
            "expected_topic": labels.get("expected_topic", "NEEDS_REVIEW"),
            "expected_risk_level": labels.get("expected_risk_level", "NEEDS_REVIEW"),
            "expert_notes": labels.get("expert_notes", "Требует ручной разметки"),
            "labeled_at": datetime.utcnow().isoformat(),
            "needs_review": labels.get("expected_topic") == "NEEDS_REVIEW",
        }
        labeled.append(record)

        # Для матрицы покрытия
        topic = labels.get("expected_topic")
        if topic in HR_TOPICS:
            source_topic_counts[item["source_id"]][topic] += 1

    return labeled, source_topic_counts


def build_coverage_matrix(source_topic_counts: dict) -> list[dict]:
    """
    Строит матрицу покрытия на основе реальных данных.
    Для источников без достаточной статистики (<3 статей) помечает как estimated.
    """
    print("\n=== Шаг 5: Матрица покрытия ===")
    rows = []

    source_map = {s["source_id"]: s for s in ACTIVE_SOURCES}

    for source in ACTIVE_SOURCES:
        sid = source["source_id"]
        counts = source_topic_counts.get(sid, Counter())
        total = sum(counts.values())

        row = {
            "source_id": sid,
            "source_name": sid,  # заменить на name из каталога при необходимости
            "lang": source["lang"],
            "category": source["category"],
            "total_labeled": total,
            "data_quality": "real" if total >= 3 else "estimated",
        }

        # Проценты по темам
        for topic in HR_TOPICS:
            if total > 0:
                row[topic] = round(counts.get(topic, 0) / total * 100)
            else:
                row[topic] = 0

        # Нормализуем до 100% (из-за округления)
        topic_sum = sum(row[t] for t in HR_TOPICS)
        if topic_sum > 0 and topic_sum != 100:
            # Добавляем разницу к самой большой теме
            biggest = max(HR_TOPICS, key=lambda t: row[t])
            row[biggest] += (100 - topic_sum)

        rows.append(row)
        print(f"  {sid}: total={total}, quality={row['data_quality']}")

    return rows


def save_labeled_news(labeled: list[dict]):
    """Сохраняет labeled_news.json (без служебных полей)."""
    output = []
    for item in labeled:
        clean = {k: v for k, v in item.items()
                 if k not in ("source_id", "labeled_at", "needs_review")}
        output.append(clean)

    path = FIXTURES_DIR / "labeled_news.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {path}")

    # Отдельно сохраняем items с needs_review для ручной проверки
    needs_review = [item for item in labeled if item.get("needs_review")]
    if needs_review:
        review_path = FIXTURES_DIR / "labeled_news_needs_review.json"
        with open(review_path, "w", encoding="utf-8") as f:
            json.dump(needs_review, f, ensure_ascii=False, indent=2)
        print(f"⚠ {len(needs_review)} items требуют ручной разметки → {review_path}")


def save_coverage_matrix(rows: list[dict]):
    path = DOCS_DIR / "topic_coverage_matrix.csv"
    fieldnames = ["source_id", "source_name", "lang", "category",
                  "total_labeled", "data_quality"] + HR_TOPICS
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ {path}")


def print_summary(labeled: list[dict]):
    topics = Counter(n["expected_topic"] for n in labeled)
    risks = Counter(n["expected_risk_level"] for n in labeled)
    langs = Counter(n["lang"] for n in labeled)
    needs_review = sum(1 for n in labeled if n.get("needs_review"))

    print("\n=== Итог ===")
    print(f"Всего: {len(labeled)}")
    print(f"Языки: RU={langs['ru']} ({langs['ru']/len(labeled)*100:.0f}%), EN={langs['en']} ({langs['en']/len(labeled)*100:.0f}%)")
    print(f"Темы: {dict(topics)}")
    print(f"Риски: {dict(risks)}")
    if needs_review:
        print(f"⚠ Требуют ручной проверки: {needs_review}")
    else:
        print("✓ Все записи размечены")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠ OPENAI_API_KEY не задан — лейблинг будет помечать все как NEEDS_REVIEW")
        print("  Установи ключ в .env или передай: OPENAI_API_KEY=sk-... python scripts/build_fixtures.py\n")

    labeled, source_topic_counts = build_labeled_news()
    matrix_rows = build_coverage_matrix(source_topic_counts)

    save_labeled_news(labeled)
    save_coverage_matrix(matrix_rows)
    print_summary(labeled)

    print("\nГотово. Следующие шаги:")
    print("  1. Проверь labeled_news_needs_review.json если файл создан")
    print("  2. Верифицируй выборку вручную (хотя бы 10-15 записей)")
    print("  3. Для источников с data_quality=estimated — запусти снова через неделю")
    print("  4. Скинь список новых ключевых слов Павленко из expert_notes")
