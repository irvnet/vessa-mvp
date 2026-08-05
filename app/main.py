import logging
import subprocess
import sys
from collections import Counter
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from datetime import datetime

from app.agent import generate_checkin
from app.bootstrap import build_compiled_agent, get_memory_store
from app.config import ROOT, SQLITE_DB_PATH, get_allowed_origins
from app.eval_persistence import load_eval_summaries
from app.profile import CareContext, get_profile
from app.reminders import (
    CAREGIVER_NOTIFICATIONS,
    acknowledge,
    create_reminder,
    delete_reminder,
    effective_status,
    list_reminders,
    update_reminder,
)
from app.scheduler import companion_thread_id, proactive_message, start_scheduler
from app.summary import get_or_refresh_daily_summary
from app.visibility import list_events, status_badge, todays_events
from app.voice import synthesize, transcribe

logger = logging.getLogger(__name__)

# Single hardcoded receiver for now — matches app/profile.py's sample profile.
DEFAULT_CONTEXT = CareContext(care_team_id="team-rose", receiver_id="rose-1")

CHAT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Vessa</title>
  <style>
    :root { font-family: system-ui, sans-serif; color: #2d2418; background: #faf3e8; }
    body { margin: 0; max-width: 720px; margin-inline: auto; min-height: 100dvh; display: flex; flex-direction: column; }
    header { padding: 1rem; background: #8a5a3b; color: #fff; }
    header h1 { margin: 0; font-size: 1.2rem; }
    header p { margin: .25rem 0 0; font-size: .85rem; opacity: .9; }
    #messages { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: .75rem; }
    .msg { padding: .75rem 1rem; border-radius: .75rem; max-width: 92%; line-height: 1.45; white-space: pre-wrap; }
    .user { align-self: flex-end; background: #f3e4cf; }
    .bot { align-self: flex-start; background: #fff; border: 1px solid #e8dcc8; }
    form { display: flex; gap: .5rem; padding: .75rem; background: #fff; border-top: 1px solid #e8dcc8; }
    input { flex: 1; padding: .75rem; border: 1px solid #d8c9ac; border-radius: .5rem; font-size: 1rem; }
    button { padding: .75rem 1rem; background: #8a5a3b; color: #fff; border: none; border-radius: .5rem; font-size: 1rem; }
    button:disabled { opacity: .6; }
    button.secondary { background: #d8c9ac; color: #4a3d24; }
    footer { font-size: .75rem; color: #8a7d68; padding: .5rem 1rem 1rem; text-align: center; }
    #caregiver { border-top: 8px solid #e8dcc8; padding: 1rem; background: #fff; }
    #caregiver h2 { margin: 0 0 .75rem; font-size: 1rem; color: #8a5a3b; }
    #reminder-form { padding: 0; border: none; margin-bottom: .75rem; }
    #reminder-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: .4rem; }
    #reminder-list li { padding: .5rem .75rem; border-radius: .5rem; background: #faf3e8; font-size: .9rem; display: flex; justify-content: space-between; gap: .5rem; }
    .status { font-size: .75rem; padding: .1rem .5rem; border-radius: 1rem; white-space: nowrap; }
    .status-pending { background: #e8dcc8; color: #6b5a3f; }
    .status-delivered { background: #d7e6d0; color: #3f6b2e; }
    .status-acknowledged { background: #cfe0e8; color: #2e5b6b; }
    .status-missed { background: #f0d0d0; color: #7a2e2e; }
    #today { border-top: 8px solid #e8dcc8; padding: 1rem; background: #fff; }
    #today-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; }
    #today-header h2 { margin: 0; font-size: 1rem; color: #8a5a3b; }
    .badge { font-size: .8rem; padding: .25rem .6rem; border-radius: 1rem; font-weight: 600; }
    .badge-ok { background: #d7e6d0; color: #3f6b2e; }
    .badge-attention { background: #f0d0d0; color: #7a2e2e; }
    #today-timeline { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: .35rem; }
    #today-timeline li { display: flex; gap: .5rem; align-items: baseline; font-size: .88rem; padding: .35rem .5rem; border-radius: .4rem; }
    #today-timeline li.concern { background: #fbeaea; color: #7a2e2e; }
    .event-time { margin-left: auto; color: #8a7d68; font-size: .75rem; white-space: nowrap; }
  </style>
</head>
<body>
  <header>
    <h1>Vessa</h1>
    <p>Talking with Rose's companion — dev test surface, not the real UI</p>
  </header>
  <div id="messages"></div>
  <form id="chat-form">
    <input id="input" type="text" placeholder="Hi Rose, how are you?" autocomplete="off" required />
    <button type="submit">Send</button>
    <button type="button" class="secondary" id="nudge-btn" title="Trigger a check-in now instead of waiting for the scheduler">🔔 Nudge now</button>
  </form>
  <footer>This is one ongoing conversation — reloading resumes it. Vessa also checks in on her own every couple of minutes (the real scheduler); "Nudge now" triggers one on demand.</footer>

  <section id="today">
    <div id="today-header">
      <h2><span id="today-name"></span> · Today</h2>
      <span id="today-status" class="badge"></span>
    </div>
    <ul id="today-timeline"></ul>
  </section>

  <section id="caregiver">
    <h2>Care Team (caregiver view — dev test)</h2>
    <form id="reminder-form">
      <input id="reminder-subject" type="text" placeholder="Take morning vitamins" autocomplete="off" required style="flex: 2;" />
      <input id="reminder-due" type="datetime-local" required />
      <button type="submit">Add</button>
    </form>
    <ul id="reminder-list"></ul>
  </section>

  <script>
    const threadId = "__THREAD_ID__";
    const messages = document.getElementById("messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("input");
    const nudgeBtn = document.getElementById("nudge-btn");
    let knownCount = 0;

    function addMsg(text, role) {
      const el = document.createElement("div");
      el.className = "msg " + role;
      el.textContent = text;
      messages.appendChild(el);
      messages.scrollTop = messages.scrollHeight;
    }

    async function loadHistory() {
      const res = await fetch(`/history?thread_id=${threadId}`);
      const data = await res.json();
      for (const m of data) addMsg(m.content, m.role);
      knownCount = data.length;
    }
    loadHistory();

    async function pollForUpdates() {
      try {
        const res = await fetch(`/poll?thread_id=${threadId}&known_count=${knownCount}`);
        const data = await res.json();
        for (const m of data.new_messages) addMsg(m.content, m.role);
        knownCount = data.total;
      } catch (err) {
        // transient poll errors are not worth surfacing to the user
      }
    }

    const todayName = document.getElementById("today-name");
    const todayStatus = document.getElementById("today-status");
    const todayTimeline = document.getElementById("today-timeline");

    async function loadToday() {
      const res = await fetch("/today");
      const data = await res.json();
      todayName.textContent = data.name;
      todayStatus.textContent = data.status === "ok" ? "🟢 OK" : "⚠️ Needs attention";
      todayStatus.className = "badge badge-" + data.status;

      todayTimeline.innerHTML = "";
      for (const e of data.events) {
        const li = document.createElement("li");
        if (e.is_concern) li.className = "concern";
        const time = new Date(e.at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
        const icon = e.is_concern ? "⚠️" : e.type === "reminder_acknowledged" ? "✓" : "•";
        li.innerHTML = `<span>${icon}</span><span>${e.summary}</span><span class="event-time">${time}</span>`;
        todayTimeline.appendChild(li);
      }
    }
    loadToday();

    setInterval(() => {
      pollForUpdates();
      loadToday();
    }, 15000);

    nudgeBtn.addEventListener("click", async () => {
      nudgeBtn.disabled = true;
      try {
        await fetch(`/checkin?thread_id=${threadId}`);
        await pollForUpdates();
        await loadToday();
      } finally {
        nudgeBtn.disabled = false;
      }
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      addMsg(text, "user");
      const btn = form.querySelector("button");
      btn.disabled = true;
      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ thread_id: threadId, message: text }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Request failed");
        addMsg(data.response, "bot");
        knownCount += 2; // the human turn we added + this bot reply — keep poll in sync
        await loadToday();
      } catch (err) {
        addMsg("Error: " + err.message, "bot");
      } finally {
        btn.disabled = false;
        input.focus();
      }
    });

    const reminderForm = document.getElementById("reminder-form");
    const reminderSubject = document.getElementById("reminder-subject");
    const reminderDue = document.getElementById("reminder-due");
    const reminderList = document.getElementById("reminder-list");

    async function loadReminders() {
      const res = await fetch("/reminders");
      const data = await res.json();
      reminderList.innerHTML = "";
      for (const r of data) {
        const li = document.createElement("li");
        const due = new Date(r.due_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" });
        li.innerHTML = `<span>${r.subject} — due ${due}</span><span class="status status-${r.status}">${r.status}</span>`;
        reminderList.appendChild(li);
      }
    }
    loadReminders();

    reminderForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = reminderForm.querySelector("button");
      btn.disabled = true;
      try {
        await fetch("/reminders", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subject: reminderSubject.value, due_at: reminderDue.value }),
        });
        reminderSubject.value = "";
        reminderDue.value = "";
        await loadReminders();
        await loadToday();
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


class ReminderRequest(BaseModel):
    subject: str = Field(min_length=1)
    due_at: str = Field(min_length=1)  # ISO, e.g. from a datetime-local input


class ReminderView(BaseModel):
    id: str
    subject: str
    due_at: str
    status: str


class MessageView(BaseModel):
    role: str
    content: str


class PollResponse(BaseModel):
    total: int
    new_messages: list[MessageView]


def serialize_messages(messages) -> list[MessageView]:
    """Human/AI turns only — mid-loop tool traffic and tool-call-only AI messages
    (no content yet) are internal, not something the receiver should see."""
    views = []
    for m in messages:
        if m.type == "human":
            views.append(MessageView(role="user", content=str(m.content)))
        elif m.type == "ai" and not getattr(m, "tool_calls", None) and m.content:
            views.append(MessageView(role="bot", content=str(m.content)))
    return views


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Vessa...")
    app.state.agent = build_compiled_agent()
    logger.info("Ready. Companion profile: %s", get_profile(DEFAULT_CONTEXT.care_team_id).name)
    app.state.scheduler = start_scheduler(
        app.state.agent, get_memory_store(), [DEFAULT_CONTEXT.care_team_id]
    )
    yield
    app.state.scheduler.shutdown(wait=False)


app = FastAPI(title="Vessa", lifespan=lifespan)

# The real Next.js frontend runs on a separate dev server (port 3000) and calls
# this API directly — local dev only, tighten before any real deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    thread_id = companion_thread_id(DEFAULT_CONTEXT.care_team_id)
    return CHAT_HTML.replace("__THREAD_ID__", thread_id)


@app.get("/history", response_model=list[MessageView])
def history(thread_id: str) -> list[MessageView]:
    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    return serialize_messages(state.values.get("messages", []))


@app.get("/poll", response_model=PollResponse)
def poll(thread_id: str, known_count: int = 0) -> PollResponse:
    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")
    state = agent.get_state({"configurable": {"thread_id": thread_id}})
    views = serialize_messages(state.values.get("messages", []))
    new_messages = views[known_count:] if len(views) > known_count else []
    return PollResponse(total=len(views), new_messages=new_messages)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/checkin", response_model=ChatResponse)
def checkin(thread_id: str) -> ChatResponse:
    """Vessa speaks first — generates a proactive opening and seeds it into the
    thread's checkpointed state so a follow-up reply has coherent context."""
    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")

    store = get_memory_store()
    text = generate_checkin(DEFAULT_CONTEXT.care_team_id, store=store)

    config = {"configurable": {"thread_id": thread_id}}
    # Tagged like a scheduler push so the two are indistinguishable downstream —
    # otherwise a manual nudge wouldn't hold off the job firing seconds later.
    agent.update_state(config, {"messages": [proactive_message(text)]})

    return ChatResponse(response=text)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")

    config = {"configurable": {"thread_id": req.thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        config,
        context=DEFAULT_CONTEXT,
    )
    return ChatResponse(response=result["messages"][-1].content)


# --- Caregiver / Care Team side (thin — plain REST, no agent needed yet) ---


@app.post("/reminders", response_model=ReminderView)
def add_reminder(req: ReminderRequest) -> ReminderView:
    store = get_memory_store()
    due_at = datetime.fromisoformat(req.due_at)
    reminder = create_reminder(store, DEFAULT_CONTEXT.care_team_id, req.subject, due_at)
    return ReminderView(
        id=reminder.id, subject=reminder.subject, due_at=reminder.due_at, status=reminder.status
    )


@app.get("/reminders", response_model=list[ReminderView])
def get_reminders() -> list[ReminderView]:
    store = get_memory_store()
    reminders = list_reminders(store, DEFAULT_CONTEXT.care_team_id)
    return [
        ReminderView(
            id=r.id, subject=r.subject, due_at=r.due_at, status=effective_status(r)
        )
        for r in reminders
    ]


@app.put("/reminders/{reminder_id}", response_model=ReminderView)
def edit_reminder(reminder_id: str, req: ReminderRequest) -> ReminderView:
    store = get_memory_store()
    due_at = datetime.fromisoformat(req.due_at)
    try:
        reminder = update_reminder(
            store, DEFAULT_CONTEXT.care_team_id, reminder_id, subject=req.subject, due_at=due_at
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return ReminderView(
        id=reminder.id, subject=reminder.subject, due_at=reminder.due_at,
        status=effective_status(reminder),
    )


@app.delete("/reminders/{reminder_id}")
def remove_reminder(reminder_id: str) -> dict:
    store = get_memory_store()
    delete_reminder(store, DEFAULT_CONTEXT.care_team_id, reminder_id)
    return {"status": "deleted"}


@app.post("/reminders/{reminder_id}/acknowledge", response_model=ReminderView)
def mark_reminder_acknowledged(reminder_id: str) -> ReminderView:
    store = get_memory_store()
    try:
        reminder = acknowledge(store, DEFAULT_CONTEXT.care_team_id, reminder_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return ReminderView(
        id=reminder.id, subject=reminder.subject, due_at=reminder.due_at, status=reminder.status
    )


@app.get("/notifications")
def get_notifications() -> list[dict]:
    return CAREGIVER_NOTIFICATIONS.get(DEFAULT_CONTEXT.care_team_id, [])


class EventView(BaseModel):
    type: str
    summary: str
    at: str
    is_concern: bool


class TodayView(BaseModel):
    name: str
    status: str
    summary: str
    events: list[EventView]


@app.get("/today", response_model=TodayView)
def today() -> TodayView:
    store = get_memory_store()
    events = todays_events(store, DEFAULT_CONTEXT.care_team_id)
    return TodayView(
        name=get_profile(DEFAULT_CONTEXT.care_team_id).name,
        status=status_badge(events),
        summary=get_or_refresh_daily_summary(store, DEFAULT_CONTEXT.care_team_id, events),
        events=[
            EventView(type=e.type, summary=e.summary, at=e.at, is_concern=e.is_concern) for e in events
        ],
    )


# --- Proof surface — makes safety/quality provable in-app, not just in a
# terminal or LangSmith, so a demo-day question can be answered live. ---

EVAL_SUITES = ("safety", "grounding", "memory", "reminders")


@app.get("/proof/eval-results")
def get_eval_results() -> dict:
    return load_eval_summaries()


@app.post("/proof/run-eval")
def run_eval(suite: str = "all") -> dict:
    suites = EVAL_SUITES if suite == "all" else (suite,)
    if any(s not in EVAL_SUITES for s in suites):
        raise HTTPException(status_code=400, detail=f"suite must be one of {EVAL_SUITES} or 'all'")

    errors: dict[str, str] = {}
    for s in suites:
        try:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / f"eval_{s}.py")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            errors[s] = "timed out after 180s"
            continue
        if proc.returncode != 0:
            errors[s] = proc.stderr[-500:]

    results = load_eval_summaries()
    for s, err in errors.items():
        results.setdefault(s, {})["last_run_error"] = err
    return results


@app.get("/proof/guardrail-activity")
def get_guardrail_activity() -> dict:
    store = get_memory_store()
    events = list_events(store, DEFAULT_CONTEXT.care_team_id)
    guardrail_events = [e for e in events if e.type.startswith("guardrail_")]
    counts = Counter(e.type for e in guardrail_events)
    recent = sorted(guardrail_events, key=lambda e: e.at, reverse=True)[:10]
    return {
        "counts": dict(counts),
        "recent": [
            {"type": e.type, "summary": e.summary, "at": e.at, "is_concern": e.is_concern}
            for e in recent
        ],
    }


@app.get("/proof/health")
def get_proof_health() -> dict:
    scheduler = getattr(app.state, "scheduler", None)
    return {
        "sqlite_reachable": SQLITE_DB_PATH.exists(),
        "sqlite_path": str(SQLITE_DB_PATH),
        "scheduler_running": scheduler is not None and scheduler.running,
    }


# --- Voice I/O — a thin shell around the guarded /chat: speech-to-text in,
# text-to-speech out. The transcript is sent through the SAME agent, so nothing
# bypasses the guardrails/memory/grounding (see app/voice.py). ---


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1)


@app.post("/voice/transcribe")
def voice_transcribe(file: UploadFile = File(...)) -> dict:
    audio = file.file.read()
    try:
        return {"text": transcribe(audio, filename=file.filename or "audio.webm")}
    except Exception as e:  # a too-short/empty clip shouldn't 500 — let the user just type
        logger.warning("Transcription failed: %s", e)
        return {"text": ""}


@app.post("/voice/speak")
def voice_speak(req: SpeakRequest) -> Response:
    return Response(content=synthesize(req.text), media_type="audio/mpeg")
