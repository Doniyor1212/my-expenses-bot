from __future__ import annotations

import json
import re
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import get_settings
from parser import parse_many


class ReceiptOCRService:
    def parse_receipt_image(self, image_path: str) -> list[dict]:
        text = self._try_gemini_vision(image_path)

        if not text:
            return []

        print("=" * 80)
        print("OCR GEMINI FULL TEXT:")
        print(text)
        print("=" * 80)
        print("OCR GEMINI REPR:")
        print(repr(text))
        print("=" * 80)

        data = self._extract_json(text)

        if isinstance(data, list):
            result = [
                self._normalize(x)
                for x in data
                if isinstance(x, dict) and x.get("amount")
            ]
            return [x for x in result if x["amount"] > 0]

        if isinstance(data, dict):
            if "operations" in data and isinstance(data["operations"], list):
                result = [
                    self._normalize(x)
                    for x in data["operations"]
                    if isinstance(x, dict) and x.get("amount")
                ]
                return [x for x in result if x["amount"] > 0]

            if data.get("amount"):
                item = self._normalize(data)
                return [item] if item["amount"] > 0 else []

        fallback = self._fallback_from_text(text)
        if fallback:
            return [fallback]

        parsed = parse_many(text)
        return parsed if parsed else []

    def _try_gemini_vision(self, image_path: str) -> str | None:
        settings = get_settings()
        api_key = getattr(settings, "gemini_api_key", None)

        if not api_key:
            print("OCR GEMINI ERROR: GEMINI_API_KEY не найден")
            return None

        try:
            image_bytes = Path(image_path).read_bytes()
            client = genai.Client(api_key=api_key)

            prompt = """
Ты OCR-сервис для Telegram-бота учета расходов.

Распознай чек на фото.

Верни СТРОГО валидный JSON. Без markdown. Без пояснений.

Формат:
[
  {
    "type": "expense",
    "category": "Кафе",
    "description": "Название магазина",
    "amount": 194700
  }
]

Правила:
- Верни только одну операцию.
- amount только число без пробелов и валюты.
- Валюта UZS.
- Используй итоговую сумму к оплате.
- Если есть "ИТОГО К ОПЛАТЕ" — бери эту сумму.
- Если есть кафе/ресторан/ош/сомса/чай/еда — category = "Кафе".
- Если не уверен в названии — description = "Чек".
"""

            response = client.models.generate_content(
                model=getattr(settings, "vision_model", "gemini-2.5-flash"),
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg",
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )

            return response.text

        except Exception as e:
            print(f"OCR GEMINI ERROR: {e}")
            return None

    def _normalize(self, item: dict) -> dict:
        amount = self._to_int(item.get("amount", 0))

        description = (
            item.get("description")
            or item.get("name")
            or item.get("title")
            or item.get("merchant")
            or "Чек"
        )

        category = item.get("category") or self._detect_category(description)

        return {
            "type": item.get("type", "expense"),
            "category": str(category).strip() or "Прочее",
            "description": str(description).strip().capitalize(),
            "amount": amount,
        }

    def _detect_category(self, text: str) -> str:
        text = str(text).lower()

        cafe_words = [
            "кафе", "coffee", "cafe", "ресторан", "osh", "ош",
            "somsa", "сомса", "чай", "еда", "nomdor", "markazi",
            "food", "burger", "kfc", "evos"
        ]

        for word in cafe_words:
            if word in text:
                return "Кафе"

        return "Прочее"

    def _to_int(self, value) -> int:
        if value is None:
            return 0

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        value = str(value)
        value = re.sub(r"[^\d]", "", value)

        return int(value) if value else 0

    def _extract_json(self, text: str):
        if not text:
            return None

        text = text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(text)
        except Exception as e:
            print(f"OCR JSON ERROR direct: {e}")

        array_match = re.search(r"\[[\s\S]*\]", text)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except Exception as e:
                print(f"OCR JSON ERROR array: {e}")

        object_match = re.search(r"\{[\s\S]*\}", text)
        if object_match:
            try:
                return json.loads(object_match.group(0))
            except Exception as e:
                print(f"OCR JSON ERROR object: {e}")

        return None

    def _fallback_from_text(self, text: str) -> dict | None:
        if not text:
            return None

        clean = text.lower().replace("\xa0", " ")

        amounts = re.findall(r"\d[\d\s.,]{2,}", clean)
        parsed_amounts = []

        for item in amounts:
            amount = self._to_int(item)
            if amount >= 1000:
                parsed_amounts.append(amount)

        if not parsed_amounts:
            return None

        amount = max(parsed_amounts)

        category = self._detect_category(clean)
        description = "Чек"

        for keyword in ["nomdor", "somsa", "osh", "markazi"]:
            if keyword in clean:
                description = "Nomdor Somsa Osh Markazi"
                category = "Кафе"
                break

        return {
            "type": "expense",
            "category": category,
            "description": description,
            "amount": amount,
        }