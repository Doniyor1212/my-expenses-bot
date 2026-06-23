import os
from collections import defaultdict
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from database import get_expenses


def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " сум"


def short_money(amount: int) -> str:
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f} млн"
    if amount >= 1_000:
        return f"{amount / 1_000:.0f} тыс"
    return str(amount)


def get_font(size: int, bold: bool = False):
    paths = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def create_shadow(size, box, radius=56, offset=(0, 18), blur=34):
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    x1, y1, x2, y2 = box
    ox, oy = offset
    draw.rounded_rectangle(
        (x1 + ox, y1 + oy, x2 + ox, y2 + oy),
        radius=radius,
        fill=(15, 23, 42, 32),
    )
    return shadow.filter(ImageFilter.GaussianBlur(blur))


def draw_centered_text(draw, center_x, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((center_x - text_width / 2, y), text, font=font, fill=fill)


def build_expense_pie_chart(telegram_id: int) -> str | None:
    expenses = get_expenses(telegram_id)
    if not expenses:
        return None

    categories = defaultdict(int)
    for item in expenses:
        categories[item.get("category", "Прочее")] += int(item.get("amount", 0))

    sorted_items = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    total = sum(categories.values())
    total_operations = len(expenses)
    today = datetime.now().day
    avg_per_day = total // max(today, 1)
    top_category = sorted_items[0][0]

    os.makedirs("charts", exist_ok=True)
    file_path = f"charts/expenses_{telegram_id}.png"

    width = 1800
    height = max(1120, 620 + len(sorted_items) * 84)

    bg = "#EEF2F7"
    card_bg = "#FFFFFF"
    text_main = "#111827"
    text_muted = "#6B7280"
    line = "#E5E7EB"

    palette = [
        "#635BFF", "#22C55E", "#F97316", "#3B82F6",
        "#14B8A6", "#EC4899", "#EAB308", "#8B5CF6",
        "#06B6D4", "#84CC16", "#F43F5E", "#10B981",
    ]

    img = Image.new("RGBA", (width, height), bg)
    card_box = (90, 90, width - 90, height - 90)
    img.alpha_composite(create_shadow((width, height), card_box))

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(card_box, radius=64, fill=card_bg)

    font_title = get_font(58, True)
    font_subtitle = get_font(30)
    font_kpi_title = get_font(21)
    font_kpi_value = get_font(30, True)
    font_total = get_font(62, True)
    font_total_label = get_font(24)
    font_total_small = get_font(21)
    font_category = get_font(30, True)
    font_category_info = get_font(23)
    font_footer = get_font(21)

    draw.text((140, 130), "Расходы по категориям", font=font_title, fill=text_main)
    current_month = datetime.now().strftime("%m.%Y")
    draw.text((140, 205), f"Аналитика расходов · {current_month}", font=font_subtitle, fill=text_muted)

    kpi_y = 290
    kpi_h = 112
    kpi_w = 355
    kpi_gap = 25
    kpis = [
        ("Потрачено", money(total), "#F3F0FF"),
        ("Средний день", money(avg_per_day), "#EEF8F3"),
        ("Операций", str(total_operations), "#FFF7ED"),
        ("Топ категория", top_category, "#EFF6FF"),
    ]

    for i, (title, value, fill) in enumerate(kpis):
        x1 = 140 + i * (kpi_w + kpi_gap)
        y1 = kpi_y
        x2 = x1 + kpi_w
        y2 = y1 + kpi_h
        draw.rounded_rectangle((x1, y1, x2, y2), radius=28, fill=fill)
        draw.text((x1 + 25, y1 + 20), title, font=font_kpi_title, fill=text_muted)
        draw.text((x1 + 25, y1 + 56), value, font=font_kpi_value, fill=text_main)

    draw.line((140, 455, width - 140, 455), fill=line, width=2)

    center_x, center_y = 520, 710
    radius = 210
    thickness = 64
    start_angle = -90

    for i, (_, value) in enumerate(sorted_items):
        percent = value / total
        end_angle = start_angle + percent * 360
        draw.arc(
            (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            start=start_angle,
            end=end_angle,
            fill=palette[i % len(palette)],
            width=thickness,
        )
        start_angle = end_angle

    draw.ellipse(
        (
            center_x - radius + thickness + 8,
            center_y - radius + thickness + 8,
            center_x + radius - thickness - 8,
            center_y + radius - thickness - 8,
        ),
        fill=card_bg,
    )

    draw_centered_text(draw, center_x, center_y - 68, short_money(total), font_total, text_main)
    draw_centered_text(draw, center_x, center_y + 10, "общие расходы", font_total_label, text_muted)
    draw_centered_text(draw, center_x, center_y + 50, f"{total_operations} операций", font_total_small, text_muted)

    legend_x = 930
    legend_y = 525
    legend_gap = 84

    for i, (category, amount) in enumerate(sorted_items):
        y = legend_y + i * legend_gap
        percent = amount / total * 100
        color = palette[i % len(palette)]
        draw.ellipse((legend_x, y + 13, legend_x + 28, y + 41), fill=color)
        draw.text((legend_x + 52, y), category, font=font_category, fill=text_main)
        draw.text((legend_x + 52, y + 43), f"{percent:.1f}% · {money(amount)}", font=font_category_info, fill=text_muted)

    draw.text((140, height - 150), "MyCost Premium", font=font_footer, fill="#9CA3AF")

    img = img.convert("RGB")
    img.save(file_path, quality=96)
    return file_path
