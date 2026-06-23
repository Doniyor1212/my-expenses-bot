# MyCost Bot v4 — CORE + AI + OCR + Web + Premium

## Что добавлено

### CORE
- Новая структура `app/`:
  - `core` — конфиг, логирование, кеш
  - `db` — подключение и миграции
  - `models` — доменные модели
  - `repositories` — слой доступа к данным
  - `services` — бизнес-логика AI/OCR/Premium
  - `web` — FastAPI web cabinet
- Миграции БД: `schema_migrations`, `user_profiles`, `receipt_imports`, `ai_dialogs`, `premium_features`.
- Логирование через `app.core.logging`.
- TTL-cache для AI-ответов.
- Dockerfile и docker-compose.
- Pytest тесты.

### AI
Команды:
- `AI Почему трачу больше?`
- `AI Можно купить iPhone за 12 млн?`

Если в `.env` есть `OPENAI_API_KEY`, AI отвечает через OpenAI на основании бюджета, целей, доходов, расходов и истории. Если ключа нет — работает локальный rule-based AI.

### OCR чеков
Отправьте фото чека в бот. При наличии `OPENAI_API_KEY` бот использует GPT Vision и автоматически добавляет операции.

### Web-кабинет
Запуск:
```bash
uvicorn app.web.main:app --host 0.0.0.0 --port 8000
```
Адрес:
```text
http://localhost:8000
```
API:
- `GET /health`
- `GET /api/users/{telegram_id}/dashboard`
- `POST /api/users/{telegram_id}/ai`

### Premium
Команды:
- `Премиум`
- `Premium`

Заложена модель тарифов и список функций уровня ZenMoney: бюджеты, цели, AI, OCR, Web, экспорт, лимиты.

## Запуск бота
```bash
pip install -r requirements.txt
python main.py
```

## Docker
```bash
docker compose up --build
```

## .env пример
```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_key_optional
DATABASE_URL=sqlite:///data/expenses.db
OPENAI_MODEL=gpt-4.1-mini
VISION_MODEL=gpt-4.1-mini
LOG_LEVEL=INFO
```

## Тесты
```bash
pytest -q
```
