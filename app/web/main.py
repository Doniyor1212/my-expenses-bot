from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.db.migrations import run_migrations
from app.repositories.finance import FinanceRepository
from app.services.ai_advisor import AIAdvisorService

app = FastAPI(title="MyCost Web Cabinet", version="4.0.0")
repo = FinanceRepository()
ai = AIAdvisorService(repo)


@app.on_event("startup")
def startup():
    run_migrations()


@app.get("/health")
def health():
    return {"status": "ok", "service": "mycost"}


@app.get("/api/users/{telegram_id}/dashboard")
def dashboard(telegram_id: int):
    return repo.snapshot(telegram_id, months=6)


@app.post("/api/users/{telegram_id}/ai")
def ai_answer(telegram_id: int, payload: dict):
    return {"answer": ai.answer(telegram_id, payload.get("question", ""))}


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html><head><title>MyCost</title></head>
    <body style='font-family:Arial;max-width:900px;margin:40px auto'>
    <h1>MyCost Web Cabinet</h1>
    <p>API готов: /health, /api/users/{telegram_id}/dashboard, /api/users/{telegram_id}/ai</p>
    <p>Следующий шаг: авторизация Telegram Login Widget и React/Vue UI.</p>
    </body></html>
    """
