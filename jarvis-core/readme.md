# JARVIS — Backend Setup

> Just A Rather Very Intelligent System

## Требования

- Python 3.9+
- macOS (тестировалось на Mac)

---

## Первый запуск

### 1. Клонируй и войди в папку
```bash
cd jarvis-core
```

### 2. Активируй виртуальное окружение
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установи зависимости
```bash
pip install -r requirements.txt
```

### 4. Создай `.env` файл
```bash
nano .env
```

Вставь:
```
FEATHERLESS_API_KEY=твой_ключ
JIRA_API_TOKEN=твой_токен
JIRA_EMAIL=твой@email.com
JIRA_BASE_URL=https://kadyelyer.atlassian.net
JIRA_PROJECT_KEY=JAR
SPEECHMATICS_API_KEY=твой_ключ
```

### 5. Авторизуй Gmail (только первый раз)
```bash
python3 -c "from agents.email_agent import get_gmail_service; get_gmail_service()"
```
Откроется браузер → войди → разреши доступ → закрой окно.

### 6. Запусти сервер
```bash
uvicorn main:app --reload --port 8000
```

Сервер запущен на `http://localhost:8000` ✅

---

## Проверка что всё работает

Открой в браузере:
```
http://localhost:8000/health
```
Должно вернуть: `{"status": "online", "message": "JARVIS is running"}`

Документация API:
```
http://localhost:8000/docs
```

---

## Тесты агентов

### Текстовые команды (WebSocket)
```bash
python3 -c "
import asyncio, websockets, json

async def test():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        print(await ws.recv())
        await ws.send(json.dumps({'text': 'create a bug ticket for login issue'}))
        print(await ws.recv())
        await ws.send(json.dumps({'text': 'show my open tickets'}))
        print(await ws.recv())
        await ws.send(json.dumps({'text': 'find best practices for REST API security'}))
        print(await ws.recv())
        await ws.send(json.dumps({'text': 'show my unread emails'}))
        print(await ws.recv())

asyncio.run(test())
"
```

### Голосовая команда (Speechmatics)
```bash
# 1. Запись голоса (5 секунд) — говори сразу после запуска
sox -d -r 16000 -c 1 test_audio.wav trim 0 5

# 2. Отправка на сервер
python3 -c "
import httpx, asyncio

async def test_voice():
    with open('test_audio.wav', 'rb') as f:
        audio = f.read()
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            'http://localhost:8000/voice',
            files={'file': ('audio.wav', audio, 'audio/wav')}
        )
        data = response.json()
        print(f'Transcript: {data[\"transcript\"]}')
        print(f'JARVIS: {data[\"response\"]}')

asyncio.run(test_voice())
"
```

---

## Структура проекта

```
jarvis-core/
├── main.py                 — FastAPI + WebSocket + голосовой endpoint
├── orchestrator.py         — роутер, определяет какой агент вызвать
├── agents/
│   ├── jira_agent.py       — создаёт/листит тикеты в Jira
│   ├── email_agent.py      — читает/драфтит письма Gmail
│   ├── meeting_agent.py    — summary встречи + тикеты в Jira
│   └── research_agent.py   — веб поиск + суммаризация
├── services/
│   ├── gemini.py           — LLM (Featherless / Qwen 72B) + intent detection
│   └── speechmatics.py     — speech-to-text
├── credentials.json        — Google OAuth (не коммитить!)
├── token.json              — Gmail токен (не коммитить!)
├── .env                    — API ключи (не коммитить!)
└── requirements.txt
```

---

## Поддерживаемые команды

| Команда | Intent | Агент |
|---|---|---|
| "create a bug ticket for X" | create_jira_ticket | Jira |
| "show my open tickets" | list_jira_tickets | Jira |
| "show my unread emails" | read_emails | Email |
| "send email to X about Y" | send_email | Email |
| "meeting summary: ..." | meeting_summary | Meeting |
| "find best practices for X" | research | Research |
| Всё остальное | general_chat | LLM |

---

## Следующие шаги

- [ ] Деплой на AMD Cloud
- [ ] Web интерфейс (React)
- [ ] macOS Swift приложение
- [ ] iOS приложение
- [ ] Тест голоса (Speechmatics)
