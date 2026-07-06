# CareAnchor

An autonomous post-discharge clinical assistant that uses LangGraph agent orchestration, Alibaba Cloud Model Studio (Qwen), and real-time WebSocket streaming to monitor patient vitals, detect safety threshold breaches, and trigger human-in-the-loop interrupts with webhook notifications.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Safety System](#safety-system)
- [Testing](#testing)
- [License](#license)

---

## Overview

CareAnchor is a healthcare AI assistant designed to bridge the gap between hospital discharge and home recovery. After a patient is discharged, there is a critical window where complications can arise but clinical oversight is limited. CareAnchor fills this gap by providing continuous, intelligent monitoring through a conversational interface that:

1. **Extracts clinical data** from patient conversations using Qwen-Plus
2. **Maintains a persistent clinical profile** (vitals, medications, symptoms, care plan)
3. **Monitors safety thresholds** in real-time with severity-tiered alerts
4. **Triggers human-in-the-loop interrupts** when critical conditions are detected
5. **Notifies clinicians** via webhook when immediate intervention is required

---

## Problem Statement

Post-discharge complications affect approximately 15-20% of patients within 30 days of leaving the hospital. Common issues include:

- Medication non-adherence
- Missed follow-up appointments
- Unrecognized worsening of vital signs
- Delayed recognition of emergency symptoms

Current solutions rely on periodic phone calls or generic discharge instructions, leaving significant gaps in patient monitoring.

---

## Solution

CareAnchor provides an always-available clinical companion that:

- **Converses naturally** with patients about their recovery
- **Tracks clinical data** across sessions, building a comprehensive patient profile
- **Detects dangerous patterns** using configurable vital sign thresholds and symptom keyword matching
- **Escalates appropriately** with three severity tiers: INFO, WARN, and CRITICAL
- **Maintains audit trails** of all safety events in PostgreSQL

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  ChatPanel    │  │ MessageBubble│  │ ClinicalMemoryViewer│   │
│  └──────┬───────┘  └──────────────┘  └─────────────────────┘   │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │useAgentChat  │──── WebSocket ────► ws://host/ws/chat/{id}   │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  REST API     │  │  WebSocket   │  │  Health Check       │   │
│  │  /api/chat    │  │  /ws/chat/id │  │  /health            │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────────────────┘   │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LangGraph Agent Orchestration               │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │    │
│  │  │Extract  │→ │ Memory  │→ │ Safety  │→ │ Respond  │  │    │
│  │  │Clinical │  │ Update  │  │ Check   │  │ (Normal/ │  │    │
│  │  │Data     │  │         │  │         │  │ Interrupt)│  │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Qwen Cloud   │  │  PostgreSQL  │  │  Interrupt Controller│   │
│  │ (DashScope)  │  │  (Clinical   │  │  (State Machine)     │   │
│  │              │  │   Profiles)  │  │                      │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Alibaba Cloud ECS                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  Nginx       │  │  Docker      │  │  Safety Events      │   │
│  │  Reverse     │  │  Compose     │  │  PostgreSQL Table    │   │
│  │  Proxy       │  │  Stack       │  │                      │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

### Clinical Data Extraction
- Uses Qwen-Plus with structured JSON extraction
- Intelligent forgetting: skips non-clinical messages (chitchat detection)
- Extracts vitals, medications, symptoms, and care plan details

### Safety Threshold System
- **Severity Tiers**: INFO, WARN, CRITICAL
- **Vital Monitoring**: Systolic/Diastolic BP, Heart Rate, SpO2, Temperature, Respiratory Rate
- **Keyword Detection**: 11 critical/warn symptom patterns (chest pain, breathing difficulty, suicidal ideation, stroke symptoms, etc.)
- **Compound Risk Scoring**: Multiple borderline values increase risk score beyond individual thresholds

### Human-in-the-Loop Interrupts
- **State Machine**: NORMAL → PENDING_ACKNOWLEDGMENT → ACKNOWLEDGED/ESCALATED → RESOLVED
- **Rate Limiting**: Configurable cooldown between webhook notifications (default: 5 minutes)
- **Acknowledgment Tracking**: Records who acknowledged and when
- **Persistent Audit Trail**: All safety events stored in PostgreSQL

### Real-time Streaming
- WebSocket connection for token-by-token response delivery
- Node-level progress events (extract → memory → safety → respond)
- Agent state badges in UI (thinking, analyzing, responding)

### Clinical Memory Viewer
- Real-time vital signs grid with danger highlighting
- Medications and symptoms tracking
- Safety event history with severity indicators

---

## Tech Stack

### Backend
- **Framework**: FastAPI with async/await
- **Agent Orchestration**: LangGraph (dual compiled graphs)
- **LLM Provider**: Alibaba Cloud Model Studio (Qwen-Plus for extraction, Qwen-Max for response)
- **Database**: PostgreSQL with asyncpg
- **HTTP Client**: httpx for webhook notifications

### Frontend
- **Framework**: React 19 with TanStack Start
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (Radix primitives)
- **State Management**: TanStack Query
- **WebSocket**: Custom hook with typed event stream

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx
- **Cloud Provider**: Alibaba Cloud ECS
- **AI Services**: Alibaba Cloud Model Studio (DashScope)

---

## Project Structure

```
care-companion-ai/
├── backend/
│   ├── agents/
│   │   ├── graph.py              # LangGraph agent orchestration
│   │   ├── clinical_responder.py # Qwen-Max response generation
│   │   ├── memory_refiner.py     # Qwen-Plus clinical extraction
│   │   └── tools.py              # Safety threshold checking
│   ├── api/
│   │   ├── routes.py             # REST endpoints
│   │   ├── websocket.py          # WebSocket handler
│   │   └── models.py             # Pydantic models
│   ├── core/
│   │   ├── safety.py             # Safety threshold logic
│   │   ├── interrupt.py          # Interrupt state machine
│   │   ├── memory_store.py       # PostgreSQL CRUD
│   │   └── qwen_client.py        # Alibaba Cloud API client
│   ├── db/
│   │   └── postgres.py           # Database schema & pool
│   ├── tests/                    # Pytest test suite
│   ├── config.py                 # Settings from env vars
│   ├── main.py                   # FastAPI app entry point
│   ├── Dockerfile                # Multi-stage Docker build
│   └── requirements.txt          # Python dependencies
├── src/
│   ├── components/
│   │   ├── chat-panel.tsx        # Chat interface
│   │   ├── message-bubble.tsx    # Message display
│   │   └── clinical-memory-viewer.tsx  # Vitals sidebar
│   ├── hooks/
│   │   └── use-agent-chat.ts     # WebSocket hook
│   ├── lib/
│   │   └── agent.ts              # Agent event types
│   └── routes/
│       └── __root.tsx            # App root
├── deploy/
│   ├── nginx.conf                # Nginx configuration
│   ├── ecs-setup.sh              # ECS bootstrap script
│   ├── verify-alibaba.sh         # Alibaba Cloud verification
│   └── .env.ecs                  # Environment template
├── alibaba_cloud_config.py       # Hackathon proof file
├── docker-compose.yml            # Production stack
└── package.json                  # Frontend dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 16+
- Alibaba Cloud Model Studio API key

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Saya2003/Care-Anchor.git
cd Care-Anchor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export DASHSCOPE_API_KEY="your-api-key"
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/careanchor"

# Start the backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DASHSCOPE_API_KEY` | Alibaba Cloud Model Studio API key | (required) |
| `QWEN_PLUS_MODEL` | Model for clinical extraction | `qwen-plus` |
| `QWEN_MAX_MODEL` | Model for response generation | `qwen-max` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/careanchor` |
| `ALERT_WEBHOOK_URL` | Webhook for safety alerts | (optional) |
| `ESCALATION_COOLDOWN_SECONDS` | Minimum seconds between webhook calls | `300` |
| `SYSTOLIC_BP_WARN_MAX` | Systolic BP warning threshold | `160` |
| `SYSTOLIC_BP_CRIT_MAX` | Systolic BP critical threshold | `180` |
| `HEART_RATE_WARN_MIN/MAX` | Heart rate warning range | `50-110` |
| `HEART_RATE_CRIT_MIN/MAX` | Heart rate critical range | `40-140` |
| `SP_O2_WARN_MIN` | SpO2 warning threshold | `94` |
| `SP_O2_CRIT_MIN` | SpO2 critical threshold | `90` |
| `TEMPERATURE_WARN_MAX` | Temperature warning threshold | `38.0` |
| `TEMPERATURE_CRIT_MAX` | Temperature critical threshold | `39.5` |

---

## Deployment

### Docker Compose (Local/Production)

```bash
# Build and start all services
docker-compose up --build -d

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Alibaba Cloud ECS

```bash
# On your ECS instance
chmod +x deploy/ecs-setup.sh
./deploy/ecs-setup.sh

# Verify deployment
chmod +x deploy/verify-alibaba.sh
./deploy/verify-alibaba.sh
```

---

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/sessions` | Create a new session |
| `GET` | `/api/sessions/{id}` | Get session details |
| `POST` | `/api/chat` | Send message (full graph) |
| `GET` | `/health` | Health check |
| `GET` | `/alibaba/runtime` | Alibaba Cloud verification |

### WebSocket

Connect to `ws://host/ws/chat/{session_id}` for real-time streaming.

**Events received:**
- `session_init` — Initial session data
- `node_start` — Agent node started
- `node_end` — Agent node completed
- `safety_result` — Safety check results
- `token` — Response token
- `done` — Response complete

**Events sent:**
- `{ "message": "user message" }` — Send patient message

---

## Safety System

### Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| `INFO` | Normal readings | Continue conversation |
| `WARN` | Elevated vitals (e.g., BP 160-180) | Monitor closely, recheck in 1-2 hours |
| `CRITICAL` | Dangerous readings (e.g., BP >180) | Immediate emergency attention required |

### Interrupt States

```
NORMAL → PENDING_ACKNOWLEDGMENT → ACKNOWLEDGED → RESOLVED
                    ↓
                ESCALATED
```

### Webhook Payload

```json
{
  "session_id": "uuid",
  "severity": "critical",
  "alerts": ["Systolic BP (185) exceeds critical maximum (180)"],
  "message": "Patient reports chest pain"
}
```

---

## Testing

```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run specific test file
python -m pytest backend/tests/test_safety.py -v

# Run with coverage
python -m pytest backend/tests/ --cov=backend
```

**Test Coverage:**
- Safety module: 40 tests (thresholds, severity tiers, compound risk)
- Interrupt controller: 35 tests (state machine, rate limiting)
- Tools: 15 tests (deep merge, safety checks)
- Graph: 10 tests (routing, orchestration nodes)
- Clinical responder: 22 tests (prompt generation, model settings)

---

## License

MIT License

---

## Acknowledgments

- Built for the Alibaba Cloud hackathon
- Uses Alibaba Cloud Model Studio (DashScope) for Qwen model inference
- Deployed on Alibaba Cloud ECS
- UI components from shadcn/ui
- Agent orchestration with LangGraph
