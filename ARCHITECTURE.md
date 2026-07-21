# CareAnchor Architecture

## System Overview

CareAnchor is a production-ready healthcare AI assistant built on modern cloud infrastructure, using Codex and GPT-5.6 models for clinical intelligence and LangGraph for agent orchestration.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  ChatPanel    │  │ MessageBubble│  │   Dashboard         │   │
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
│  │  REST API     │  │  WebSocket   │  │  Profile API        │   │
│  │  /api/chat    │  │  /ws/chat/id │  │  /profile/*         │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────────────────┘   │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LangGraph Agent Orchestration               │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │    │
│  │  │Extract  │→ │ Memory  │→ │ Safety  │→ │ Respond  │  │    │
│  │  │Clinical │  │ Update  │  │ Check   │  │ (GPT-    │  │    │
│  │  │Data     │  │         │  │         │  │  5.6)    │  │    │
│  │  │(Codex)  │  │         │  │         │  │          │  │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Alibaba      │  │  SQLite/     │  │  Interrupt Controller│   │
│  │ OpenRouter   │  │  PostgreSQL  │  │  (State Machine)     │   │
│  │ (Codex/      │  │  (Clinical   │  │                      │   │
│  │  GPT-5.6)    │  │   Profiles)  │  │                      │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Alibaba Cloud ECS                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  Nginx       │  │  Docker      │  │  Safety Events      │   │
│  │  Reverse     │  │  Compose     │  │  Database           │   │
│  │  Proxy       │  │  Stack       │  │                      │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Flow

### 1. Message Reception
- User sends message via WebSocket
- Backend receives and creates session context

### 2. Clinical Data Extraction (Codex)
- Natural language → structured JSON
- Extracts: vitals, medications, symptoms, care plans
- Intelligent forgetting: skips chitchat

### 3. Memory Update
- Deep merge with existing profile
- Preserves historical data
- Updates timestamps

### 4. Safety Check
- Monitors vital sign thresholds
- Detects emergency keywords
- Calculates compound risk scores
- Three severity tiers: INFO, WARN, CRITICAL

### 5. Response Generation (GPT-5.6)
- Severity-aware prompts
- Profile-aware context
- Real-time token streaming
- WebSocket delivery

## Data Flow

```
User Input → WebSocket → Agent Graph → Codex → Safety Check
                                          ↓
                                    Memory Store ← Clinical Profile
                                          ↓
                                    GPT-5.6 Response → WebSocket → User
                                          ↓
                                    (If Critical) → Webhook → Clinician
```

## Technology Stack

### Backend
- **Runtime**: Python 3.12+
- **Framework**: FastAPI (async)
- **Agent Framework**: LangGraph
- **AI Models**: 
  - Codex (clinical extraction)
  - GPT-5.6 (response generation)
- **AI Provider**: OpenRouter
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **WebSocket**: Native FastAPI WebSocket
- **Testing**: Pytest (122 tests)

### Frontend
- **Framework**: React 19 + TanStack Start
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui
- **State**: TanStack Query
- **Auth**: Supabase Auth
- **Build**: Vite

### Infrastructure
- **Cloud**: Alibaba Cloud ECS
- **Container**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **SSL**: Let's Encrypt (if configured)

## Security

- All vitals data encrypted in transit (WebSocket + HTTPS)
- Authentication via Supabase
- Rate limiting on webhook notifications
- Audit trail for all safety events
- State machine prevents duplicate alerts

## Scalability

- Async Python for high concurrency
- WebSocket for real-time streaming
- SQLite for development, PostgreSQL for production
- Docker containers for easy horizontal scaling
- Nginx load balancing ready

## Monitoring

- Health check endpoint: `/health`
- Alibaba Cloud verification: `/alibaba/runtime`
- Application logs via Docker
- Safety event database audit trail
- WebSocket connection tracking
