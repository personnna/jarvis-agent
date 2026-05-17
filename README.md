# JARVIS — Just A Rather Very Intelligent System

> *"I built JARVIS because I can't organize my life."*

JARVIS is a personal AI operating system inspired by Marvel's Iron Man. Voice-first, multi-platform, and genuinely intelligent — it doesn't just answer questions, it thinks ahead, plans autonomously, and acts before you ask.

**Live Demo:** [jarvis-ai.xyz](http://jarvis-ai.xyz)  
**Backend API:** [140.82.58.192:8000/docs](http://140.82.58.192:8000/docs)

---

## The Problem

I missed important work calls. I double-booked meetings with friends. I was always the person who said *"oh wait, I actually have something at that time."*

Not because I didn't care. Because I couldn't keep everything in my head at once.

So I built JARVIS.

---

## What JARVIS Does

### 🎙️ Voice-First Interface
Speak naturally. JARVIS listens, understands, and acts — no tapping, no typing required. Powered by Speechmatics for accurate transcription across multiple languages.

### 🧠 Multi-Step Autonomous Planning
Ask one question. JARVIS does the work of four.

> *"Prepare me for my team meeting"*

JARVIS autonomously:
1. Checks your Google Calendar for the meeting time
2. Pulls open Jira tickets to discuss
3. Reads recent emails from your team
4. Generates a smart briefing with action items and risks

This is not a chatbot. This is a planning agent.

### 🔔 Proactive Intelligence
JARVIS speaks first — without being asked.
- *"You have a meeting in 15 minutes"*
- *"Urgent email from AI WEEK 2026: your QR code is ready"*
- *"Leave in 25 minutes to arrive on time"*

### 📅 Conflict Detection
> *"Can I meet a friend at 3 PM?"*  
> *"You'll be late to your meeting by 18 minutes."*

JARVIS analyzes your calendar, calculates travel time, and gives you a real answer.

### 🌤️ Predictive Planning
> *"Can I go to Venice tomorrow?"*  
> *"Yes — it's sunny, 24°C. But leave before 12:15 to make it back for your 3 PM."*

### 💾 Long-Term Memory
JARVIS remembers you across sessions via PostgreSQL. After a restart:
> *"Hi! Of course I remember you, Yeldana."*

### 🔄 Self-Correction
When something fails, JARVIS retries with exponential backoff and alternative approaches — silently, without bothering you.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI / LLM | Groq (llama-3.3-70b-versatile) |
| Intent Detection | Groq (llama-3.1-8b-instant) |
| Speech-to-Text | Speechmatics API |
| Agent Orchestration | LangGraph + custom planner |
| Backend | FastAPI + WebSocket |
| Database | PostgreSQL (asyncpg) |
| Web Frontend | React |
| iOS App | SwiftUI |
| watchOS App | SwiftUI + AVSpeechSynthesizer |
| Deployment | Vultr VM (Ubuntu 22.04) |

---

## Architecture

```
User (Voice/Text)
       ↓
   WebSocket
       ↓
  Orchestrator
  ├── Intent Detection (small model, fast)
  ├── Complexity Check → Simple or Complex?
  │
  ├── Simple Request → Direct Agent
  │   ├── Jira Agent
  │   ├── Gmail Agent
  │   ├── Calendar Agent
  │   ├── Weather Agent
  │   ├── Research Agent
  │   └── Conflict Detection Agent
  │
  └── Complex Request → LangGraph Planner
      ├── Step 1: Analyze and Plan
      ├── Step 2: Execute agents sequentially
      ├── Step 3: Gather data
      └── Step 4: Generate smart briefing

  Proactive Monitor (background)
  ├── Every 1 min: Check upcoming meetings
  ├── Every 1 min: Calculate departure time
  └── Every 5 min: Check urgent emails

  PostgreSQL Memory
  ├── Conversation history
  ├── User profile (learns over time)
  └── Usage patterns
```

---

## Platforms

### 🌐 Web App
Full-featured chat interface with Arc Reactor animation, real-time agent badges, and Life Dashboard showing weather, schedule, and Jira tasks.

### 📱 iOS App (SwiftUI)
Native iPhone app with push-to-talk voice input, real-time WebSocket connection, and a full Life Dashboard tab.

### ⌚ watchOS App
Apple Watch app — tap to speak, JARVIS responds. The most natural way to interact.

---

## Live Demo Workflows

1. **Meeting Prep** — *"Prepare me for my team meeting"* → Calendar + Jira + Gmail + Smart Briefing
2. **Travel Planning** — *"Can I go to Venice tomorrow?"* → Calendar + Weather → specific recommendation
3. **Conflict Detection** — *"Can I meet a friend at 3 PM?"* → detects conflicts, suggests alternatives
4. **Proactive Alert** — JARVIS notifies you about urgent emails without being asked
5. **Voice Ticket Creation** — *"Create a critical bug for payment system"* → Jira ticket + contextual warnings
6. **Departure Alert** — *"Leave in 25 minutes"* — automatic travel time calculation

---

## Deployment

**Server:** Vultr Cloud Compute (Frankfurt)  
**OS:** Ubuntu 22.04  
**Process Manager:** Supervisor (auto-restart)  
**Web Server:** Nginx (reverse proxy)  

```bash
git clone https://github.com/personnna/jarvis-agent
cd jarvis-agent/jarvis-core
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Hackathon

Built for **lablab.ai AI Agent Olympics Hackathon 2026** (Milan, Italy)

**Tracks targeted:**
- Intelligent Reasoning (multi-step autonomous planning)
- Enterprise Utility (Jira, Gmail, Calendar integrations)
- Multimodal (voice + text + visual dashboard)
- Vultr Cloud Deployment

---

*Built solo by **Yeldana Kadenova** — iOS developer, Mestre, Italy.*

*"I needed it. And now I use it every day."*
