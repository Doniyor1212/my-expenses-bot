import asyncio
import os
import ui

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import (
    init_db,
    add_expense,
    add_income,
    delete_last_operation,
    clear_all_operations,
    get_last_operation,
    update_operation,
    get_operation_by_id,
    delete_operation_by_id,
    duplicate_operation_by_id
)
from parser import parse_many
from reports import build_balance_report, build_history_report
from statistics import build_statistics_report
from keyboards import main_keyboard
from voice import recognize_voice
from charts import build_expense_pie_chart
from period_reports import build_period_report
from services.ai_analysis import generate_ai_expense_analysis
from app.core.logging import setup_logging
from app.db.migrations import run_migrations
from app.services.ai_advisor import AIAdvisorService
from app.services.ocr_receipts import ReceiptOCRService
from app.services.premium import PremiumService
from services.budgets import build_budget_report, set_budget_for_current_month, delete_budget_for_current_month
from services.goals import build_goals_report, create_goal_from_text, add_saving_from_text, delete_goal_from_text


bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

setup_logging()
init_db()
run_migrations()
ai_advisor_service = AIAdvisorService()
receipt_ocr_service = ReceiptOCRService()
premium_service = PremiumService()

clear_confirm_users = set()
edit_users = {}


def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " сум"


def category_icon(category: str) -> str:
    return ""


def operation_keyboard(table: str, operation_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{table}:{operation_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{table}:{operation_id}"),
            ],
            [
                InlineKeyboardButton(text="📋 Дублировать", callback_data=f"duplicate:{table}:{operation_id}")
            ]
        ]
    )


def report_period_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сегодня", callback_data="report:today"), InlineKeyboardButton(text="Вчера", callback_data="report:yesterday")],
            [InlineKeyboardButton(text="Неделя", callback_data="report:week"), InlineKeyboardButton(text="Месяц", callback_data="report:month")]
        ]
    )


def operation_card(title: str, item: dict) -> str:
    clean_title = (
        title.replace("💰", "").replace("💸", "").replace("🗑", "")
        .replace("✅", "").replace("📋", "").replace("✏️", "").replace("🧾", "").strip()
    )
    return ui.card(clean_title, [
        ui.row("Описание", item.get("description", "Без описания")),
        ui.row("Категория", item.get("category", "Прочее")),
        ui.row("Сумма", money(int(item.get("amount", 0)))),
    ])


async def remove_inline_buttons(callback: CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "MyCost Bot\n\n"
        "Примеры:\n"
        "Кофе 35000\n"
        "Такси 50000\n"
        "Зарплата 35000000\n\n"
        "Команды:\n"
        "Баланс\n"
        "Отчет\n"
        "Статистика\n"
        "График\n"
        "История\n"
        "Последние\n"
        "Удалить последнее\n"
        "Редактировать последнее\n"
        "Очистить всё\n\n"
        "Можно отправить голосовое или фото чека.\n\n"
        "AI-вопросы:\n"
        "AI Почему трачу больше?\n"
        "AI Можно купить iPhone за 12 млн?\n\n"
        "Web: http://localhost:8000",
        reply_markup=main_keyboard()
    )


async def process_text(message: Message, text: str):
    operations = parse_many(text)

    if not operations:
        await message.answer(
            "Не удалось определить сумму.\n\n"
            "Примеры:\n"
            "Кофе 35000\n"
            "Такси 50000\n"
            "Зарплата 35000000"
        )
        return

    added_count = 0

    for item in operations:
        if item["amount"] <= 0:
            continue

        if item["type"] == "income":
            operation_id = add_income(
                message.from_user.id,
                item["category"],
                item["description"],
                item["amount"]
            )

            item["id"] = operation_id
            item["table"] = "incomes"

            await message.answer(
                operation_card("Доход добавлен", item),
                reply_markup=operation_keyboard("incomes", operation_id)
            )

        else:
            operation_id = add_expense(
                message.from_user.id,
                item["category"],
                item["description"],
                item["amount"]
            )

            item["id"] = operation_id
            item["table"] = "expenses"

            await message.answer(
                operation_card("Расход добавлен", item),
                reply_markup=operation_keyboard("expenses", operation_id)
            )

        added_count += 1

    if added_count == 0:
        await message.answer(
            "Не удалось определить сумму.\n\n"
            "Примеры:\n"
            "Кофе 35000\n"
            "Такси 50000\n"
            "Зарплата 35000000"
        )


@dp.message(F.voice)
async def voice_handler(message: Message):
    file = await bot.get_file(message.voice.file_id)

    os.makedirs("media", exist_ok=True)
    ogg_path = f"media/voice_{message.message_id}.ogg"

    await bot.download_file(file.file_path, destination=ogg_path)

    text = recognize_voice(ogg_path)

    if not text:
        await message.answer("Не смог распознать голос.")
        return

    await message.answer(f"Распознал:\n{text}")
    await process_text(message, text)



@dp.message(F.photo)
async def receipt_photo_handler(message: Message):
    """OCR чеков через GPT Vision. Если OPENAI_API_KEY не задан, мягко сообщает что OCR не включен."""
    os.makedirs("media/receipts", exist_ok=True)
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    path = f"media/receipts/receipt_{message.from_user.id}_{message.message_id}.jpg"
    await bot.download_file(file.file_path, destination=path)

    operations = receipt_ocr_service.parse_receipt_image(path)

    if not operations:
        await message.answer(
            "🧾 Фото чека получено.\n\n"
            "OCR через GPT Vision не смог распознать операции.\n"
            "Проверьте OPENAI_API_KEY в .env или отправьте текстом: Кофе 35000"
        )
        return

    added = 0
    for item in operations:
        if item.get("amount", 0) <= 0:
            continue
        if item.get("type") == "income":
            operation_id = add_income(message.from_user.id, item.get("category", "Доход"), item.get("description", "Чек"), item["amount"])
            table = "incomes"
            title = "Доход из чека добавлен"
        else:
            operation_id = add_expense(message.from_user.id, item.get("category", "Прочее"), item.get("description", "Чек"), item["amount"])
            table = "expenses"
            title = "Расход из чека добавлен"
        item["id"] = operation_id
        item["table"] = table
        await message.answer(operation_card(title, item), reply_markup=operation_keyboard(table, operation_id))
        added += 1

    await message.answer(f"✅ Из чека добавлено операций: {added}")

@dp.callback_query(F.data.startswith("delete:"))
async def callback_delete(callback: CallbackQuery):
    await remove_inline_buttons(callback)

    _, table, operation_id = callback.data.split(":")
    operation_id = int(operation_id)

    item = delete_operation_by_id(table, operation_id, callback.from_user.id)

    if not item:
        await callback.message.answer("Эта операция уже удалена или не найдена.")
        await callback.answer()
        return

    if callback.from_user.id in edit_users:
        del edit_users[callback.from_user.id]

    await callback.message.answer(operation_card("Операция удалена", item))
    await callback.answer("Удалено")


@dp.callback_query(F.data.startswith("duplicate:"))
async def callback_duplicate(callback: CallbackQuery):
    _, table, operation_id = callback.data.split(":")
    operation_id = int(operation_id)

    new_item = duplicate_operation_by_id(table, operation_id, callback.from_user.id)

    if not new_item:
        await callback.message.answer("Эта операция уже удалена или не найдена.")
        await callback.answer()
        return

    title = "Доход повторен" if new_item["type"] == "income" else "Расход повторен"

    await callback.message.answer(
        operation_card(title, new_item),
        reply_markup=operation_keyboard(new_item["table"], new_item["id"])
    )

    await callback.answer("Продублировано")


@dp.callback_query(F.data.startswith("edit:"))
async def callback_edit(callback: CallbackQuery):
    await remove_inline_buttons(callback)

    _, table, operation_id = callback.data.split(":")
    operation_id = int(operation_id)

    item = get_operation_by_id(table, operation_id, callback.from_user.id)

    if not item:
        await callback.message.answer("Эта операция уже удалена или не найдена.")
        await callback.answer()
        return

    edit_users[callback.from_user.id] = {
        "table": table,
        "operation_id": operation_id
    }

    await callback.message.answer(
        "✏️ Редактирование операции\n\n"
        f"Сейчас:\n"
        f"📝 {item['description']}\n"
        f"📂 {item['category']}\n"
        f"💵 {money(item['amount'])}\n\n"
        "Напишите новый вариант, например:\n"
        "Кола 25000\n\n"
        "Для отмены напишите:\n"
        "ОТМЕНА"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("report:"))
async def report_period_callback(callback: CallbackQuery):
    period = callback.data.split(":")[1]

    await callback.message.answer(
        build_period_report(callback.from_user.id, period)
    )

    await callback.answer()


@dp.message(lambda m: m.text and m.from_user.id in edit_users)
async def confirm_edit(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text.lower() == "отмена":
        del edit_users[user_id]
        await message.answer("❌ Редактирование отменено.")
        return

    parsed = parse_many(text)

    if not parsed or parsed[0]["amount"] <= 0:
        await message.answer(
            "Не удалось определить новую сумму.\n\n"
            "Пример:\n"
            "Кола 25000"
        )
        return

    edit_data = edit_users[user_id]
    table = edit_data["table"]
    operation_id = edit_data["operation_id"]

    old_item = get_operation_by_id(table, operation_id, user_id)

    if not old_item:
        del edit_users[user_id]
        await message.answer("Эта операция уже удалена или не найдена.")
        return

    new_item = parsed[0]

    update_operation(
        table,
        operation_id,
        user_id,
        new_item["category"],
        new_item["description"],
        new_item["amount"]
    )

    del edit_users[user_id]

    updated_item = get_operation_by_id(table, operation_id, user_id)

    await message.answer(
        operation_card("Операция обновлена", updated_item),
        reply_markup=operation_keyboard(table, operation_id)
    )


@dp.message(lambda m: m.text and m.text.lower() == "баланс")
async def balance(message: Message):
    await message.answer(build_balance_report(message.from_user.id))


@dp.message(lambda m: m.text and m.text.lower() == "отчет")
async def report(message: Message):
    await message.answer(ui.card("Отчет", ["Выберите период"]), reply_markup=report_period_keyboard())


@dp.message(lambda m: m.text and m.text.lower() == "статистика")
async def statistics(message: Message):
    await message.answer(build_statistics_report(message.from_user.id))


@dp.message(lambda m: m.text and m.text.lower() in ["🎯 цели", "цели", "мои цели"])
async def goals_report(message: Message):
    await message.answer(build_goals_report(message.from_user.id))


@dp.message(lambda m: m.text and (
    m.text.lower().startswith("цель ")
    or m.text.lower().startswith("создать цель ")
    or m.text.lower().startswith("новая цель ")
))
async def create_goal_handler(message: Message):
    await message.answer(create_goal_from_text(message.from_user.id, message.text))


@dp.message(lambda m: m.text and (
    m.text.lower().startswith("пополнить ")
    or m.text.lower().startswith("пополнить цель ")
    or m.text.lower().startswith("отложить ")
    or m.text.lower().startswith("отложить на ")
))
async def add_goal_saving_handler(message: Message):
    await message.answer(add_saving_from_text(message.from_user.id, message.text))


@dp.message(lambda m: m.text and (
    m.text.lower().startswith("удалить цель ")
    or m.text.lower().startswith("удали цель ")
))
async def delete_goal_handler(message: Message):
    await message.answer(delete_goal_from_text(message.from_user.id, message.text))


@dp.message(lambda m: m.text and m.text.lower() in ["💰 бюджет", "бюджет"])
async def budget_report(message: Message):
    await message.answer(build_budget_report(message.from_user.id))


@dp.message(lambda m: m.text and m.text.lower().startswith("бюджет "))
async def set_budget(message: Message):
    parts = message.text.strip().split()

    if len(parts) < 2:
        await message.answer(
            "Укажите сумму бюджета.\n\n"
            "Пример:\n"
            "Бюджет 6000000"
        )
        return

    raw_amount = parts[1].replace(" ", "").replace(",", "").replace(".", "")

    if not raw_amount.isdigit():
        await message.answer(
            "Не удалось определить сумму бюджета.\n\n"
            "Пример:\n"
            "Бюджет 6000000"
        )
        return

    amount = int(raw_amount)

    if amount <= 0:
        await message.answer("Бюджет должен быть больше 0.")
        return

    await message.answer(set_budget_for_current_month(message.from_user.id, amount))


@dp.message(lambda m: m.text and m.text.lower() in ["удалить бюджет", "сбросить бюджет"])
async def delete_budget(message: Message):
    await message.answer(delete_budget_for_current_month(message.from_user.id))



@dp.message(lambda m: m.text and m.text.lower().startswith(("ai ", "аи ", "ии ", "спроси ")))
async def ai_question_handler(message: Message):
    question = message.text.strip()
    for prefix in ["AI ", "ai ", "АИ ", "аи ", "ИИ ", "ии ", "спроси ", "Спроси "]:
        if question.startswith(prefix):
            question = question[len(prefix):].strip()
            break
    if not question:
        await message.answer("Напишите вопрос, например: AI Можно купить iPhone за 12 млн?")
        return
    await message.answer(ai_advisor_service.answer(message.from_user.id, question))


@dp.message(lambda m: m.text and m.text.lower() in ["premium", "премиум", "💎 premium", "💎 премиум"])
async def premium_handler(message: Message):
    await message.answer(premium_service.build_plan_text(message.from_user.id))


@dp.message(lambda m: m.text and m.text.lower() in ["web", "веб", "кабинет", "личный кабинет"])
async def web_handler(message: Message):
    await message.answer(
        "🌐 Web-кабинет\n\n"
        "Запуск локально:\n"
        "uvicorn app.web.main:app --host 0.0.0.0 --port 8000\n\n"
        "Docker:\n"
        "docker compose up --build\n\n"
        "Адрес: http://localhost:8000"
    )

@dp.message(lambda m: m.text and m.text.lower() in ["🤖 ai-анализ", "ai-анализ", "аи-анализ", "ai анализ", "аи анализ", "ии-анализ", "ии анализ"])
async def ai_analysis(message: Message):
    await message.answer(generate_ai_expense_analysis(message.from_user.id))


@dp.message(lambda m: m.text and m.text.lower() in ["график", "диаграмма"])
async def chart(message: Message):
    chart_path = build_expense_pie_chart(message.from_user.id)

    if not chart_path:
        await message.answer(ui.empty("График", "Нет данных для построения графика."))
        return

    photo = FSInputFile(chart_path)

    await message.answer_photo(
        photo,
        caption="Расходы по категориям"
    )


@dp.message(lambda m: m.text and m.text.lower() in ["история", "последние"])
async def history(message: Message):
    await message.answer(build_history_report(message.from_user.id))


@dp.message(lambda m: m.text and m.text.lower() in ["удалить", "удалить последний", "удалить последнее"])
async def delete_last(message: Message):
    item = delete_last_operation(message.from_user.id)

    if not item:
        await message.answer("Удалять нечего.")
        return

    await message.answer(operation_card("Последняя операция удалена", item))


@dp.message(lambda m: m.text and m.text.lower() in ["редактировать последнее", "изменить последнее"])
async def ask_edit_last(message: Message):
    item = get_last_operation(message.from_user.id)

    if not item:
        await message.answer("Редактировать нечего.")
        return

    edit_users[message.from_user.id] = {
        "table": item["table"],
        "operation_id": item["id"]
    }

    await message.answer(
        "✏️ Редактирование последней операции\n\n"
        f"Сейчас:\n"
        f"📝 {item['description']}\n"
        f"📂 {item['category']}\n"
        f"💵 {money(item['amount'])}\n\n"
        "Напишите новый вариант, например:\n"
        "Кола 25000\n\n"
        "Для отмены напишите:\n"
        "ОТМЕНА"
    )


@dp.message(lambda m: m.text and m.text.lower() in ["очистить всё", "очистить все"])
async def ask_clear_all(message: Message):
    clear_confirm_users.add(message.from_user.id)

    await message.answer(
        "⚠️ Вы уверены, что хотите очистить всю историю?\n\n"
        "Это действие нельзя отменить.\n\n"
        "Для подтверждения напишите:\n"
        "ОЧИСТИТЬ\n\n"
        "Для отмены напишите:\n"
        "ОТМЕНА"
    )


@dp.message(lambda m: m.text and m.text.lower() == "очистить")
async def confirm_clear_all(message: Message):
    if message.from_user.id not in clear_confirm_users:
        await message.answer(
            "Чтобы очистить историю, сначала нажмите или напишите:\n"
            "Очистить всё"
        )
        return

    clear_all_operations(message.from_user.id)
    clear_confirm_users.remove(message.from_user.id)

    if message.from_user.id in edit_users:
        del edit_users[message.from_user.id]

    await message.answer("✅ Вся история очищена.")


@dp.message(lambda m: m.text and m.text.lower() == "отмена")
async def cancel_action(message: Message):
    user_id = message.from_user.id

    if user_id in clear_confirm_users:
        clear_confirm_users.remove(user_id)
        await message.answer("❌ Очистка отменена.")
        return

    if user_id in edit_users:
        del edit_users[user_id]
        await message.answer("❌ Редактирование отменено.")
        return

    await message.answer("Операция отменена.")


@dp.message(F.text)
async def save(message: Message):
    await process_text(message, message.text)


async def main():
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
