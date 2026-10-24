#!/usr/bin/env python3
"""Маршрутизатор обращений службы поддержки (AIE1_Request Router).

Программа выполняет базовую маршрутизацию клиентских обращений из файлов JSON и CSV:
- Приводит данные к единой внутренней структуре.
- Определяет категорию (access, billing, bug, other) по детерминированным правилам.
- Определяет приоритет (high, medium, low).
- Сохраняет результат в итоговый JSON-файл.
- Обрабатывает ошибки ввода без вывода системного traceback.
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List


def normalize_text(text: str) -> str:
    """Приводит текст к нижнему регистру и заменяет 'ё' на 'е'."""
    return text.lower().replace("ё", "е")


def get_category(text_norm: str) -> str:
    """Определяет категорию обращения по ключевым словам в строгом порядке."""
    # 1. access: войти, пароль, нет доступа
    access_keywords = ["войти", "пароль", "нет доступа"]
    for kw in access_keywords:
        if kw in text_norm:
            return "access"

    # 2. billing: оплата, счет, тариф, спис
    billing_keywords = ["оплата", "счет", "тариф", "спис"]
    for kw in billing_keywords:
        if kw in text_norm:
            return "billing"

    # 3. bug: ошибка, не работает, падает, недоступен
    bug_keywords = ["ошибка", "не работает", "падает", "недоступен"]
    for kw in bug_keywords:
        if kw in text_norm:
            return "bug"

    # 4. other: если ни одно правило выше не сработало
    return "other"


def get_priority(text_norm: str, category: str) -> str:
    """Определяет приоритет обращения."""
    # 1. high, если текст содержит срочно, критично или недоступен всем
    high_keywords = ["срочно", "критично", "недоступен всем"]
    for kw in high_keywords:
        if kw in text_norm:
            return "high"

    # 2. medium, если категория равна access или bug и правило high не сработало
    if category in ("access", "bug"):
        return "medium"

    # 3. low во всех остальных случаях
    return "low"


def route_request(request: Dict[str, str]) -> Dict[str, str]:
    """Маршрутизирует одну запись обращения."""
    text_norm = normalize_text(request["text"])
    category = get_category(text_norm)
    priority = get_priority(text_norm, category)
    return {
        "id": request["id"],
        "category": category,
        "priority": priority,
    }


def parse_and_validate_record(raw_item: Any) -> Dict[str, str]:
    """Валидирует и нормализует отдельную запись (id и text)."""
    if not isinstance(raw_item, dict):
        raise ValueError("Запись должна быть объектом/словарем с полями id и text")

    if "id" not in raw_item or "text" not in raw_item:
        raise ValueError("В записи отсутствует обязательное поле id или text")

    raw_id = raw_item["id"]
    raw_text = raw_item["text"]

    if raw_id is None or raw_text is None:
        raise ValueError("Поле id или text не должно быть пустым (None)")

    clean_id = str(raw_id).strip()
    clean_text = str(raw_text).strip()

    if not clean_id or not clean_text:
        raise ValueError("Поле id или text не должно быть пустым после удаления пробелов")

    return {"id": clean_id, "text": clean_text}


def read_json(path: str) -> List[Dict[str, str]]:
    """Читает обращения из JSON файла."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        raise ValueError(f"Синтаксическая ошибка при чтении JSON: {err}") from err

    if not isinstance(data, list):
        raise ValueError("Корневой элемент JSON-файла должен быть массивом (списком)")

    cleaned_records = []
    for item in data:
        cleaned_records.append(parse_and_validate_record(item))
    return cleaned_records


def read_csv(path: str) -> List[Dict[str, str]]:
    """Читает обращения из CSV файла с использованием заголовков."""
    cleaned_records = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "id" not in reader.fieldnames or "text" not in reader.fieldnames:
            raise ValueError("CSV файл должен содержать заголовки 'id' и 'text'")
        for row in reader:
            cleaned_records.append(parse_and_validate_record(row))
    return cleaned_records


def read_input(path: str) -> List[Dict[str, str]]:
    """Выбирает способ чтения на основе расширения входного файла."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Входной файл не найден: {path}")

    _, ext = os.path.splitext(path)
    ext_lower = ext.lower()

    if ext_lower == ".json":
        return read_json(path)
    elif ext_lower == ".csv":
        return read_csv(path)
    else:
        raise ValueError(f"Неподдерживаемый формат файла: '{ext}'. Поддерживаются только .json и .csv")


def save_output(results: List[Dict[str, str]], output_path: str) -> None:
    """Сохраняет массив результатов в выходной JSON-файл."""
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_arguments() -> argparse.Namespace:
    """Настраивает и парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Маршрутизатор обращений службы поддержки на основе явных правил (AIE1)."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Путь к входному файлу с обращениями (.json или .csv)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Путь для сохранения результата в формате JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    try:
        records = read_input(args.input)
        results = [route_request(rec) for rec in records]
        save_output(results, args.output)
    except FileNotFoundError as err:
        sys.stderr.write(f"Ошибка: {err}\n")
        sys.exit(1)
    except ValueError as err:
        sys.stderr.write(f"Ошибка: {err}\n")
        sys.exit(1)
    except Exception as err:
        sys.stderr.write(f"Непредвиденная ошибка: {err}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
