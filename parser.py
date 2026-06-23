import re
from categories import detect_category


INCOME_WORDS = [
    "зарплата", "получил", "получила", "аванс",
    "доход", "премия", "бонус", "кэшбек", "cashback"
]


STOP_WORDS = [
    "купил", "купила", "купили",
    "потратил", "потратила",
    "заплатил", "заплатила",
    "получил", "получила",
    "за", "на", "и", "в", "с",
    "сум", "сума", "сумов",
    "тысяч", "тысяча", "тысячи", "тыс",
    "миллион", "миллиона", "миллионов", "млн"
]


CATEGORY_KEYWORDS = {
    "Кафе": [
        "кафе", "кофе", "coffee", "cafe", "cappuccino", "latte", "americano",
        "чай", "еда", "обед", "ужин", "завтрак",
        "ресторан", "restaurant", "evos", "евос", "kfc", "мак", "макдональдс",
        "доставка", "пицца", "бургер", "шаурма", "донер",
        "ош", "плов", "сомса", "нон", "салат"
    ],
    "Транспорт": [
        "такси", "taxi", "яндекс", "yandex", "uber", "транспорт",
        "метро", "автобус", "бензин", "заправка", "топливо"
    ],
    "Покупки": [
        "покупки", "покупка", "купил", "купила", "маркет",
        "магазин", "вещи", "техника", "телефон", "ноутбук",
        "wildberries", "wb", "ozon", "uzum"
    ],
    "Развлечения": [
        "развлечения", "кино", "игры", "game", "playstation",
        "ps", "боулинг", "клуб", "бар", "парк", "отдых"
    ],
    "Напитки": [
        "напитки", "кола", "cola", "pepsi", "пепси", "сок",
        "вода", "энергетик", "redbull", "flash"
    ],
    "Продукты": [
        "продукты", "корзинка", "makro", "макро", "супермаркет",
        "мясо", "хлеб", "молоко", "овощи", "фрукты"
    ],
    "Здоровье": [
        "аптека", "лекарство", "таблетки", "врач", "больница",
        "клиника", "здоровье", "анализы"
    ],
    "Дом": [
        "дом", "аренда", "квартира", "ремонт", "мебель"
    ],
    "Коммунальные": [
        "коммуналка", "свет", "газ", "вода", "электричество",
        "интернет", "мусор"
    ],
    "Одежда": [
        "одежда", "футболка", "брюки", "джинсы", "куртка",
        "обувь", "кроссовки"
    ],
    "Переводы": [
        "перевод", "перевел", "перевела", "отправил", "отправила"
    ],
}


NUMBER_WORDS = {
    "ноль": 0,
    "один": 1, "одна": 1, "одно": 1,
    "два": 2, "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
    "двадцать": 20,
    "тридцать": 30,
    "сорок": 40,
    "пятьдесят": 50,
    "шестьдесят": 60,
    "семьдесят": 70,
    "восемьдесят": 80,
    "девяносто": 90,
    "сто": 100,
}


THOUSAND_WORDS = ["тыс", "тысяч", "тысяча", "тысячи"]
MILLION_WORDS = ["млн", "миллион", "миллиона", "миллионов"]


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ё", "е")
    text = re.sub(r"(?<=\d)[\s.,](?=\d)", "", text)
    text = text.replace(",", " ")
    text = text.replace(";", " ")
    text = text.replace(".", " ")
    text = " ".join(text.split())
    return text


def detect_type(text: str) -> str:
    text = normalize_text(text)

    for word in INCOME_WORDS:
        if word in text:
            return "income"

    return "expense"


def detect_category_smart(description: str, full_text: str = "") -> str:
    search_text = normalize_text(f"{description} {full_text}")

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in search_text:
                return category

    return detect_category(description)


def parse_amount(token: str, next_token: str = "") -> int:
    token = token.lower().strip()
    next_token = next_token.lower().strip()

    multiplier = 1

    if token.endswith("к"):
        multiplier = 1000
        token = token.replace("к", "")

    if next_token in THOUSAND_WORDS:
        multiplier = 1000

    if next_token in MILLION_WORDS:
        multiplier = 1_000_000

    token = re.sub(r"\D", "", token)

    if not token:
        return 0

    amount = int(token) * multiplier

    if multiplier == 1 and 10 <= amount <= 999:
        amount *= 1000

    return amount


def parse_word_amount(words: list, start_index: int) -> tuple[int, int]:
    total = 0
    current = 0
    last_index = start_index

    i = start_index
    while i < len(words):
        word = words[i]

        if word in NUMBER_WORDS:
            current += NUMBER_WORDS[word]
            last_index = i
            i += 1
            continue

        if word in THOUSAND_WORDS:
            if current == 0:
                current = 1
            total += current * 1000
            current = 0
            last_index = i
            i += 1
            continue

        if word in MILLION_WORDS:
            if current == 0:
                current = 1
            total += current * 1_000_000
            current = 0
            last_index = i
            i += 1
            continue

        break

    total += current
    return total, last_index


def clean_description(words: list) -> str:
    cleaned = []

    for word in words:
        word = word.strip()

        if not word:
            continue

        if word in STOP_WORDS:
            continue

        if re.search(r"\d", word):
            continue

        if word in NUMBER_WORDS:
            continue

        cleaned.append(word)

    description = " ".join(cleaned).strip()

    if not description:
        description = "Без описания"

    return description.capitalize()


def find_amount(words: list) -> tuple[int, int]:
    for i, word in enumerate(words):
        next_word = words[i + 1] if i + 1 < len(words) else ""

        if re.search(r"\d", word):
            return parse_amount(word, next_word), i

        if word in NUMBER_WORDS:
            amount, last_index = parse_word_amount(words, i)
            next_after = words[last_index + 1] if last_index + 1 < len(words) else ""

            if amount > 0:
                if next_after not in THOUSAND_WORDS + MILLION_WORDS and 10 <= amount <= 999:
                    amount *= 1000
                return amount, i

    return 0, -1


def parse_message(text: str) -> dict:
    original_text = text
    text = normalize_text(text)
    words = text.split()

    amount, amount_index = find_amount(words)

    description_words = words[:amount_index] if amount_index != -1 else words
    description = clean_description(description_words)

    operation_type = detect_type(text)

    if operation_type == "income":
        category = "Доход"
    else:
        category = detect_category_smart(description, original_text)

    return {
        "type": operation_type,
        "category": category,
        "description": description,
        "amount": amount
    }


def split_operations(text: str) -> list:
    text = normalize_text(text)
    words = text.split()

    operations = []
    current_words = []

    i = 0

    while i < len(words):
        word = words[i]
        current_words.append(word)

        if re.search(r"\d", word):
            next_word = words[i + 1] if i + 1 < len(words) else ""

            if next_word in THOUSAND_WORDS + MILLION_WORDS:
                current_words.append(next_word)
                i += 1

            operations.append(" ".join(current_words))
            current_words = []

        elif word in NUMBER_WORDS:
            amount, last_index = parse_word_amount(words, i)

            if amount > 0:
                while i < last_index:
                    i += 1
                    current_words.append(words[i])

                operations.append(" ".join(current_words))
                current_words = []

        i += 1

    return operations


def parse_many(text: str) -> list:
    parts = split_operations(text)
    result = []

    for part in parts:
        item = parse_message(part)

        if item["amount"] > 0:
            result.append(item)

    return result