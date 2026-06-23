from html import escape

def money(amount):
    try:
        amount = int(amount or 0)
    except Exception:
        amount = 0
    return f"{amount:,}".replace(",", " ") + " сум"

def short_money(amount):
    try:
        amount = int(amount or 0)
    except Exception:
        amount = 0
    if abs(amount) >= 1_000_000:
        return f"{amount / 1_000_000:.1f} млн"
    if abs(amount) >= 1_000:
        return f"{amount / 1_000:.0f} тыс"
    return str(amount)

def t(value):
    return escape(str(value).replace("\\n", " ").replace("\n", " ").strip())

def row(label, value):
    return f"<b>{t(label)}</b>: {t(value)}"

def card(title, lines):
    result = [f"<b>{t(title)}</b>"]
    for item in lines:
        if item is None:
            continue
        if item == "":
            result.append("")
        else:
            result.append(str(item))
    return "\n".join(result)

def empty(title, hint=""):
    lines = ["Пока нет данных."]
    if hint:
        lines += ["", t(hint)]
    return card(title, lines)

def error(text):
    return card("Ошибка", [t(text)])

def progress(percent, size=12):
    try:
        percent = int(round(float(percent)))
    except Exception:
        percent = 0
    percent = max(0, min(100, percent))
    filled = round(percent / 100 * size)
    return "█" * filled + "░" * (size - filled)
