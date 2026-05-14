import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    conn = await get_connection()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_context (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS agent_logs (
                id SERIAL PRIMARY KEY,
                session_id TEXT,
                intent TEXT,
                input TEXT,
                output TEXT,
                steps JSONB,
                duration_ms INTEGER,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        print("[DB] Tables created successfully")
    finally:
        await conn.close()

async def save_message(session_id: str, role: str, content: str, intent: str = None):
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO conversations (session_id, role, content, intent) VALUES ($1, $2, $3, $4)",
            session_id, role, content, intent
        )
    finally:
        await conn.close()

async def get_history(session_id: str, limit: int = 10) -> list:
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            "SELECT role, content FROM conversations WHERE session_id=$1 ORDER BY created_at DESC LIMIT $2",
            session_id, limit
        )
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    finally:
        await conn.close()

async def save_context(key: str, value: str):
    conn = await get_connection()
    try:
        await conn.execute(
            """INSERT INTO user_context (key, value, updated_at)
               VALUES ($1, $2, NOW())
               ON CONFLICT (key) DO UPDATE SET value=$2, updated_at=NOW()""",
            key, value
        )
    finally:
        await conn.close()

async def get_context(key: str) -> str:
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT value FROM user_context WHERE key=$1", key)
        return row["value"] if row else None
    finally:
        await conn.close()

async def log_agent(session_id: str, intent: str, input_text: str, output: str, steps: list, duration_ms: int, success: bool):
    conn = await get_connection()
    try:
        import json
        await conn.execute(
            """INSERT INTO agent_logs (session_id, intent, input, output, steps, duration_ms, success)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            session_id, intent, input_text, output, json.dumps(steps), duration_ms, success
        )
    finally:
        await conn.close()
