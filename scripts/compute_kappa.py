"""
scripts/compute_kappa.py
------------------------
Считает Cohen's Kappa между двумя аннотаторами для labeled_news.json.

Использование:
    python scripts/compute_kappa.py
    python scripts/compute_kappa.py --file1 path/to/mine.json --file2 path/to/reviewer2.json
    python scripts/compute_kappa.py --update-methodology  # автоматически пишет в docs/methodology.md

Зависимости:
    pip install scikit-learn
"""

import json
import argparse
import sys
from pathlib import Path
from collections import Counter, defaultdict

from sklearn.metrics import cohen_kappa_score

# ── Пути ──────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE1 = ROOT / "tests" / "fixtures" / "labeled_news.json"
DEFAULT_FILE2 = ROOT / "tests" / "fixtures" / "labeled_news_reviewer2.json"
METHODOLOGY_PATH = ROOT / "docs" / "methodology.md"

TOPIC_CLASSES   = ["hiring", "layoffs", "salaries", "skills", "burnout", "culture", "diversity"]
RISK_CLASSES    = ["critical", "high", "medium", "low"]
KAPPA_TARGET    = 0.70
TOP_N_DISPUTES  = 5


# ── Загрузка ──────────────────────────────────────────────────────────────────

def load_annotations(path: Path) -> dict[str, dict]:
    """Возвращает {news_id: record}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["id"]: item for item in data}


# ── Kappa ─────────────────────────────────────────────────────────────────────

def compute_kappa(ann1: dict, ann2: dict) -> dict:
    """
    Вычисляет Cohen Kappa для общего подмножества news_id.
    Возвращает словарь с результатами.
    """
    common_ids = sorted(set(ann1.keys()) & set(ann2.keys()))
    if len(common_ids) < 2:
        raise ValueError(
            f"Общих записей слишком мало: {len(common_ids)}. "
            "Убедитесь что оба файла содержат пересекающиеся news_id."
        )

    y1_topic, y2_topic = [], []
    y1_risk,  y2_risk  = [], []
    disputes_topic, disputes_risk = [], []

    for nid in common_ids:
        t1 = ann1[nid].get("expected_topic", "")
        t2 = ann2[nid].get("expected_topic", "")
        r1 = ann1[nid].get("expected_risk_level", "")
        r2 = ann2[nid].get("expected_risk_level", "")

        # Пропускаем NEEDS_REVIEW
        if "NEEDS_REVIEW" in (t1, t2, r1, r2):
            continue

        y1_topic.append(t1)
        y2_topic.append(t2)
        y1_risk.append(r1)
        y2_risk.append(r2)

        if t1 != t2:
            disputes_topic.append({
                "id": nid,
                "title": ann1[nid].get("title", ""),
                "annotator1_topic": t1,
                "annotator2_topic": t2,
                "annotator1_notes": ann1[nid].get("expert_notes", ""),
                "annotator2_notes": ann2[nid].get("expert_notes", ""),
            })
        if r1 != r2:
            disputes_risk.append({
                "id": nid,
                "title": ann1[nid].get("title", ""),
                "annotator1_risk": r1,
                "annotator2_risk": r2,
                "annotator1_notes": ann1[nid].get("expert_notes", ""),
                "annotator2_notes": ann2[nid].get("expert_notes", ""),
            })

    n = len(y1_topic)
    if n < 2:
        raise ValueError(f"После фильтрации NEEDS_REVIEW осталось {n} записей — недостаточно.")

    kappa_topic = cohen_kappa_score(y1_topic, y2_topic, labels=TOPIC_CLASSES)
    kappa_risk  = cohen_kappa_score(y1_risk,  y2_risk,  labels=RISK_CLASSES)

    # Простое % согласия
    agree_topic = sum(a == b for a, b in zip(y1_topic, y2_topic)) / n * 100
    agree_risk  = sum(a == b for a, b in zip(y1_risk,  y2_risk))  / n * 100

    # Матрица расхождений по темам
    confusion = defaultdict(Counter)
    for a, b in zip(y1_topic, y2_topic):
        confusion[a][b] += 1

    return {
        "n_common":       len(common_ids),
        "n_evaluated":    n,
        "kappa_topic":    round(kappa_topic, 4),
        "kappa_risk":     round(kappa_risk,  4),
        "agree_topic_pct": round(agree_topic, 1),
        "agree_risk_pct":  round(agree_risk,  1),
        "disputes_topic": disputes_topic[:TOP_N_DISPUTES],
        "disputes_risk":  disputes_risk[:TOP_N_DISPUTES],
        "confusion_topic": {k: dict(v) for k, v in confusion.items()},
        "topic_counts_ann1": Counter(y1_topic),
        "topic_counts_ann2": Counter(y2_topic),
    }


# ── Вывод ─────────────────────────────────────────────────────────────────────

def print_report(result: dict, file1: Path, file2: Path):
    sep = "─" * 60

    print(f"\n{sep}")
    print("  COHEN'S KAPPA — МЕЖАННОТАТОРСКОЕ СОГЛАСИЕ")
    print(sep)
    print(f"  Аннотатор 1 : {file1.name}")
    print(f"  Аннотатор 2 : {file2.name}")
    print(f"  Общих записей   : {result['n_common']}")
    print(f"  Оценено (без NR): {result['n_evaluated']}")
    print(sep)

    # Тема
    k_t = result["kappa_topic"]
    flag_t = "✓" if k_t >= KAPPA_TARGET else "✗"
    print(f"\n  ТЕМА (7 классов)")
    print(f"    % согласия : {result['agree_topic_pct']}%")
    print(f"    Kappa      : {k_t}  {flag_t}  (цель ≥ {KAPPA_TARGET})")
    print(f"    Интерпрет. : {interpret_kappa(k_t)}")

    # Уровень риска
    k_r = result["kappa_risk"]
    flag_r = "✓" if k_r >= KAPPA_TARGET else "✗"
    print(f"\n  УРОВЕНЬ РИСКА (4 класса)")
    print(f"    % согласия : {result['agree_risk_pct']}%")
    print(f"    Kappa      : {k_r}  {flag_r}  (цель ≥ {KAPPA_TARGET})")
    print(f"    Интерпрет. : {interpret_kappa(k_r)}")

    # Спорные по теме
    if result["disputes_topic"]:
        print(f"\n  ТОП-{len(result['disputes_topic'])} СПОРНЫХ ЗАПИСЕЙ (тема)")
        for i, d in enumerate(result["disputes_topic"], 1):
            print(f"\n  {i}. [{d['id']}] {d['title'][:65]}")
            print(f"     Ann1: {d['annotator1_topic']:12s} | {d['annotator1_notes'][:70]}")
            print(f"     Ann2: {d['annotator2_topic']:12s} | {d['annotator2_notes'][:70]}")

    # Спорные по риску
    if result["disputes_risk"]:
        print(f"\n  ТОП-{len(result['disputes_risk'])} СПОРНЫХ ЗАПИСЕЙ (риск)")
        for i, d in enumerate(result["disputes_risk"], 1):
            print(f"\n  {i}. [{d['id']}] {d['title'][:65]}")
            print(f"     Ann1: {d['annotator1_risk']:8s} | {d['annotator1_notes'][:70]}")
            print(f"     Ann2: {d['annotator2_risk']:8s} | {d['annotator2_notes'][:70]}")

    print(f"\n{sep}")

    # Итог
    passed = k_t >= KAPPA_TARGET and k_r >= KAPPA_TARGET
    if passed:
        print("  ✓ ОБА ПОКАЗАТЕЛЯ ≥ 0.7 — разметку можно финализировать")
    else:
        fails = []
        if k_t < KAPPA_TARGET: fails.append(f"topic={k_t}")
        if k_r < KAPPA_TARGET: fails.append(f"risk={k_r}")
        print(f"  ✗ KAPPA НИЖЕ ПОРОГА ({', '.join(fails)})")
        print("  → Проведите ревизию спорных items (см. выше)")
        print("  → После консенсуса пересчитайте: python scripts/compute_kappa.py")
    print(sep)

    return passed


def interpret_kappa(k: float) -> str:
    if k < 0:    return "Хуже случайного"
    if k < 0.20: return "Слабое"
    if k < 0.40: return "Удовлетворительное"
    if k < 0.60: return "Умеренное"
    if k < 0.80: return "Существенное ✓"
    return "Почти идеальное ✓"


# ── Запись в methodology.md ───────────────────────────────────────────────────

METHODOLOGY_SECTION = "## Качество разметки"

def update_methodology(result: dict, file1: Path, file2: Path):
    """Вставляет/обновляет секцию 'Качество разметки' в docs/methodology.md."""
    from datetime import datetime

    passed = result["kappa_topic"] >= KAPPA_TARGET and result["kappa_risk"] >= KAPPA_TARGET
    status = "✅ Принята" if passed else "❌ Требует ревизии"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    section = f"""{METHODOLOGY_SECTION}

> Последнее обновление: {now}

### Методология

Разметка выполнена двумя независимыми аннотаторами по единому гайдлайну.
Согласованность оценивается через **Cohen's Kappa** — стандартную метрику
межаннотаторского согласия, учитывающую случайное совпадение.

Пороговое значение: **κ ≥ 0.70** (существенное согласие по шкале Landis & Koch).

### Результаты

| Измерение             | % согласия | Kappa  | Интерпретация          | Статус |
|-----------------------|-----------|--------|------------------------|--------|
| Тема (7 классов)      | {result['agree_topic_pct']}%      | {result['kappa_topic']}  | {interpret_kappa(result['kappa_topic'])} | {status} |
| Уровень риска (4 кл.) | {result['agree_risk_pct']}%      | {result['kappa_risk']}  | {interpret_kappa(result['kappa_risk'])} | {status} |

- Аннотатор 1: `{file1.name}`
- Аннотатор 2: `{file2.name}`
- Общих записей: **{result['n_common']}**, оценено (без NEEDS_REVIEW): **{result['n_evaluated']}**

### Спорные случаи (тема)

"""
    if result["disputes_topic"]:
        for d in result["disputes_topic"]:
            section += (
                f"- **[{d['id']}]** {d['title'][:80]}  \n"
                f"  Ann1: `{d['annotator1_topic']}` — {d['annotator1_notes'][:100]}  \n"
                f"  Ann2: `{d['annotator2_topic']}` — {d['annotator2_notes'][:100]}\n\n"
            )
    else:
        section += "_Нет расхождений по теме._\n\n"

    section += "### Спорные случаи (риск)\n\n"
    if result["disputes_risk"]:
        for d in result["disputes_risk"]:
            section += (
                f"- **[{d['id']}]** {d['title'][:80]}  \n"
                f"  Ann1: `{d['annotator1_risk']}` — {d['annotator1_notes'][:100]}  \n"
                f"  Ann2: `{d['annotator2_risk']}` — {d['annotator2_notes'][:100]}\n\n"
            )
    else:
        section += "_Нет расхождений по риску._\n\n"

    section += f"""### Шкала Landis & Koch

| Kappa        | Интерпретация         |
|--------------|-----------------------|
| < 0.00       | Хуже случайного       |
| 0.00 – 0.20  | Слабое                |
| 0.21 – 0.40  | Удовлетворительное    |
| 0.41 – 0.60  | Умеренное             |
| 0.61 – 0.80  | Существенное          |
| 0.81 – 1.00  | Почти идеальное       |

"""

    # Читаем существующий файл или создаём новый
    if METHODOLOGY_PATH.exists():
        content = METHODOLOGY_PATH.read_text(encoding="utf-8")
        # Заменяем секцию если уже есть
        if METHODOLOGY_SECTION in content:
            # Ищем следующий заголовок того же уровня или конец файла
            import re
            pattern = rf"{re.escape(METHODOLOGY_SECTION)}.*?(?=\n## |\Z)"
            content = re.sub(pattern, section.rstrip(), content, flags=re.DOTALL)
        else:
            content += "\n\n" + section
    else:
        METHODOLOGY_PATH.parent.mkdir(parents=True, exist_ok=True)
        content = f"# Методология разметки HR-агрегатора\n\n{section}"

    METHODOLOGY_PATH.write_text(content, encoding="utf-8")
    print(f"\n✓ docs/methodology.md обновлён")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Вычисляет Cohen Kappa для двух аннотаторов")
    parser.add_argument("--file1", type=Path, default=DEFAULT_FILE1,
                        help="JSON с разметкой аннотатора 1 (default: labeled_news.json)")
    parser.add_argument("--file2", type=Path, default=DEFAULT_FILE2,
                        help="JSON с разметкой аннотатора 2 (default: labeled_news_reviewer2.json)")
    parser.add_argument("--update-methodology", action="store_true",
                        help="Записать результат в docs/methodology.md")
    parser.add_argument("--json", action="store_true",
                        help="Вывести результат в JSON (для CI/скриптов)")
    args = parser.parse_args()

    # Проверка файлов
    for path, name in [(args.file1, "file1"), (args.file2, "file2")]:
        if not path.exists():
            print(f"✗ Файл не найден: {path}")
            print(f"  Убедитесь что {name} существует или передайте --{name} <путь>")
            sys.exit(1)

    ann1 = load_annotations(args.file1)
    ann2 = load_annotations(args.file2)

    print(f"Загружено: ann1={len(ann1)} записей, ann2={len(ann2)} записей")

    try:
        result = compute_kappa(ann1, ann2)
    except ValueError as e:
        print(f"✗ Ошибка: {e}")
        sys.exit(1)

    if args.json:
        # Убираем не-сериализуемые Counter'ы
        out = {k: v for k, v in result.items()
               if k not in ("confusion_topic", "topic_counts_ann1", "topic_counts_ann2")}
        out["topic_counts_ann1"] = dict(result["topic_counts_ann1"])
        out["topic_counts_ann2"] = dict(result["topic_counts_ann2"])
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        passed = print_report(result, args.file1, args.file2)

    if args.update_methodology:
        update_methodology(result, args.file1, args.file2)

    # Exit code для CI: 0 = OK, 1 = kappa < 0.7
    passed = (result["kappa_topic"] >= KAPPA_TARGET and
              result["kappa_risk"]  >= KAPPA_TARGET)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
