from parser import parse_many


def test_parse_expense():
    item = parse_many("кофе 35000")[0]
    assert item["amount"] == 35000
    assert item["type"] == "expense"


def test_parse_income():
    item = parse_many("зарплата 1000000")[0]
    assert item["type"] == "income"
    assert item["category"] == "Доход"
