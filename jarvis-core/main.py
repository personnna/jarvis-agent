from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import process_message
from services.speechmatics import transcribe_audio
from proactive import proactive_loop, register_client, unregister_client
import json
import asyncio

app = FastAPI(title="JARVIS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(proactive_loop())
    print("[JARVIS] Proactive monitor started")

@app.get("/health")
async def health():
    return {"status": "online", "message": "JARVIS is running"}

@app.post("/mode/{mode}")
async def switch_mode(mode: str):
    import orchestrator
    if mode == "demo":
        orchestrator.DEMO_MODE = True
        return {"mode": "demo"}
    elif mode == "live":
        orchestrator.DEMO_MODE = False
        return {"mode": "live"}
    return {"error": "Invalid mode"}

@app.get("/mode")
async def get_mode():
    import orchestrator
    return {"mode": "demo" if orchestrator.DEMO_MODE else "live"}

@app.post("/voice")
async def voice_endpoint(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    transcript = await transcribe_audio(audio_bytes)
    if transcript.startswith("Error") or transcript.startswith("Speechmatics"):
        return {"transcript": transcript, "response": transcript}
    result = await process_message(transcript)
    return {"transcript": transcript, "response": result["message"]}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    register_client(websocket)
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "JARVIS online. How can I help?"
    }))
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            text = msg.get("text", "")
            print(f"[USER] {text}")
            result = await process_message(text)
            await websocket.send_text(json.dumps(result))
    except WebSocketDisconnect:
        unregister_client(websocket)
        print("Client disconnected")


@app.post("/proactive/test")
async def test_proactive():
    from proactive import notify_all
    await notify_all("You have a team meeting in 15 minutes. Open tickets: JAR-19, JAR-20. Check your emails!", "calendar_alert")
    return {"status": "sent"}

@app.on_event("startup")
async def startup_event():
    from database import init_db
    await init_db()
    asyncio.create_task(proactive_loop())
    print("[JARVIS] Proactive monitor started")