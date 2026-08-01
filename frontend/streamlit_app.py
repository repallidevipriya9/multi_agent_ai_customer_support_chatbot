"""
NovaAssist — Streamlit chat frontend (dark dashboard UI).

Uses a fixed left column (not collapsible sidebar) so webhook URL is always visible.
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR / "assets" / "agents"
load_dotenv(APP_DIR / ".env")

DEFAULT_WEBHOOK = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/customer-support"
    #3"https://laughing-succotash-xrwxqp57v9p434vw-5678.app.github.dev/webhook/customer-support",
)
REQUEST_TIMEOUT = int(os.getenv("N8N_TIMEOUT_SEC", "120"))

AGENT_FILES = {
    "router": "router",
    "order_status": "order",
    "return_refund": "returns",
    "product_query": "product",
    "general_faq": "faq",
    "fallback": "assistant",
    "synthesizer": "synthesizer",
    "assistant": "assistant",
    "user": "user",
}

AGENT_META = {
    "router": {"name": "Router", "role": "Directs queries to the right agent", "accent": "#22C55E", "icon": "🔀"},
    "order_status": {"name": "Order Agent", "role": "Tracks orders & shipments", "accent": "#3B82F6", "icon": "📦"},
    "return_refund": {"name": "Returns Agent", "role": "Handles refunds & exchanges", "accent": "#F97316", "icon": "↩️"},
    "product_query": {"name": "Product Agent", "role": "Product info & specs", "accent": "#14B8A6", "icon": "🛍️"},
    "general_faq": {"name": "FAQ Agent", "role": "Answers common questions", "accent": "#A855F7", "icon": "❓"},
    "fallback": {"name": "Assistant", "role": "Clarifies unclear requests", "accent": "#64748B", "icon": "💬"},
    "synthesizer": {"name": "Synthesizer", "role": "Polishes the final response", "accent": "#EC4899", "icon": "✨"},
}

SUGGESTIONS = [
    ("📦", "Where is order ORD-1003?"),
    ("↩️", "I want a refund for ORD-1003"),
    ("🛍️", "Is Google Chromecast good for a 4K TV?"),
    ("📋", "What is your return window?"),
]

FEATURES = [
    ("🕐", "Always On", "24/7 Support"),
    ("✨", "Smart Routing", "Right agent, fast"),
    ("🔒", "Secure & Private", "Your data is safe"),
    ("👥", "Multi-Agent AI", "Specialized help"),
]


def resolve_avatar(key: str) -> Path:
    stem = AGENT_FILES.get(key, "assistant")
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg"):
        path = ASSETS / f"{stem}{ext}"
        if path.exists():
            return path
    return ASSETS / "assistant.svg"


def resolve_bot_icon() -> Path:
    # Prefer clean vector icon matching sample UI
    for name in ("bot.svg", "bot.png", "assistant.svg", "assistant.png"):
        path = ASSETS / name
        if path.exists():
            return path
    return ASSETS / "assistant.svg"


FALLBACK_AVATAR_SVG = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" '
        b'viewBox="0 0 64 64"><circle cx="32" cy="32" r="32" fill="#334155"/>'
        b'<text x="32" y="42" font-size="26" text-anchor="middle" fill="#F1F5F9" '
        b'font-family="sans-serif">AI</text></svg>'
    ).decode("ascii")
)


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return FALLBACK_AVATAR_SVG
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp {
  background: linear-gradient(180deg, #0B1220 0%, #0F172A 55%, #111827 100%) !important;
  color: #E5E7EB !important;
}

#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
header[data-testid="stHeader"] { background: transparent !important; }

.block-container {
  padding-top: 1.6rem !important;
  padding-bottom: 1.2rem !important;
  max-width: 1280px !important;
}

[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"] {
  background: #0F172A !important;
  border-top: 1px solid rgba(148,163,184,0.12) !important;
}

/* Hide unused default sidebar */
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

div[data-testid="stTextInput"] input {
  color: #0F172A !important;
  -webkit-text-fill-color: #0F172A !important;
  background: #F8FAFC !important;
  border-radius: 10px !important;
}

.panel {
  background: #070B14;
  border: 1px solid rgba(148,163,184,0.16);
  border-radius: 18px;
  padding: 1rem 0.95rem 1.1rem;
}
.section-label {
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  color: #818CF8 !important;
  margin: 0.9rem 0 0.4rem !important;
}
.conn-box {
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(129,140,248,0.4);
  border-radius: 12px;
  padding: 0.65rem 0.7rem 0.45rem;
  margin-bottom: 0.5rem;
}
.agent-line {
  display: flex; gap: 0.6rem; align-items: center; padding: 0.35rem 0;
}
.agent-badge {
  width: 32px; height: 32px; border-radius: 50%;
  display: grid; place-items: center; color: #fff; font-size: 0.85rem; flex-shrink: 0;
}
.agent-line b { display:block; font-size:0.82rem; color:#F1F5F9; }
.agent-line small { display:block; font-size:0.7rem; color:#94A3B8; }

.feat-box {
  background: rgba(30,41,59,0.9);
  border: 1px solid rgba(148,163,184,0.16);
  border-radius: 14px;
  padding: 0.85rem 0.5rem;
  text-align: center;
  min-height: 92px;
}
.feat-box .ic { font-size: 1.15rem; }
.feat-box .t { font-size: 0.82rem; font-weight: 700; color: #F1F5F9; margin-top: 0.25rem; }
.feat-box .s { font-size: 0.7rem; color: #94A3B8; }

.hero-wrap { text-align: center; padding: 0.4rem 0 0.85rem; }
.hero-bot {
  width: 88px; height: 88px; margin: 0 auto 0.85rem;
  border-radius: 24px; overflow: hidden;
  display: grid; place-items: center;
  background: #0F172A;
  border: 2px solid rgba(167, 139, 250, 0.65);
  box-shadow: 0 0 32px rgba(167, 139, 250, 0.4);
}
.hero-bot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.hero-title { font-size: 1.65rem; font-weight: 800; color: #F8FAFC; margin: 0; }
.hero-title span {
  background: linear-gradient(90deg,#60A5FA,#A78BFA);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { color: #94A3B8; margin: 0.35rem 0 0; font-size: 0.92rem; }

.status-pill {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.3rem 0.7rem; border-radius: 999px;
  background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.3);
  color: #86EFAC; font-size: 0.76rem; font-weight: 600;
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: #22C55E; box-shadow: 0 0 8px #22C55E; }
.user-chip {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.28rem 0.65rem; border-radius: 999px;
  background: rgba(30,41,59,0.95); border: 1px solid rgba(148,163,184,0.2);
  color: #E2E8F0; font-size: 0.78rem; font-weight: 600;
}
.route-pill {
  display: inline-block; margin: 0.35rem 0 0.65rem;
  padding: 0.25rem 0.65rem; border-radius: 999px;
  background: rgba(99,102,241,0.15); border: 1px solid rgba(129,140,248,0.35);
  color: #C7D2FE; font-size: 0.74rem; font-weight: 600;
}
.footer-note { text-align: center; color: #64748B; font-size: 0.74rem; margin-top: 0.7rem; }

[data-testid="stChatMessage"] {
  background: rgba(30,41,59,0.92) !important;
  border: 1px solid rgba(148,163,184,0.16) !important;
  border-radius: 16px !important;
}
[data-testid="stChatMessage"] * { color: #F8FAFC !important; }
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] {
  color: #A5B4FC !important; -webkit-text-fill-color: #A5B4FC !important;
}

[data-testid="stChatInput"] textarea,
div[data-testid="stChatInputContainer"] textarea {
  border-radius: 16px !important;
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  caret-color: #818CF8 !important;
  background: #1E293B !important;
  border: 1px solid rgba(148,163,184,0.28) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8 !important;
}

.stButton > button {
  border-radius: 12px !important;
  border: 1px solid rgba(148,163,184,0.2) !important;
  background: rgba(30,41,59,0.95) !important;
  color: #F1F5F9 !important;
  font-weight: 600 !important;
}
.stButton > button:hover {
  border-color: rgba(129,140,248,0.55) !important;
  background: rgba(49,46,129,0.4) !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "webhook_url" not in st.session_state:
        st.session_state.webhook_url = DEFAULT_WEBHOOK
    if "last_intent" not in st.session_state:
        st.session_state.last_intent = None
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = "guest"
    if "_pending_prompt" not in st.session_state:
        st.session_state._pending_prompt = None


def call_n8n(message: str, webhook_url: str) -> Dict[str, Any]:
    payload = {
        "message": message,
        # n8n's chat-oriented nodes (e.g. "generate sql query") often read
        # $('Webhook').item.json.chatInput directly, so send it alongside
        # "message" to avoid "No prompt specified" / undefined errors.
        "chatInput": message,
        # Send both cases so the workflow works regardless of which key
        # a node's expression (e.g. Simple Memory's Session ID) expects.
        "session_id": st.session_state.session_id,
        "sessionId": st.session_state.session_id,
        "customer_id": st.session_state.get("customer_id", "guest"),
        "customerId": st.session_state.get("customer_id", "guest"),
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        if not resp.text.strip():
            return {
                "reply": (
                    "n8n returned an empty response. Open the workflow's execution "
                    "log — a node (e.g. **Simple Memory**) likely errored before "
                    "reaching the Respond node."
                ),
                "intent": "fallback",
                "error": "empty_response",
            }
        try:
            data = resp.json()
        except ValueError:
            preview = resp.text.strip()[:300]
            return {
                "reply": (
                    "n8n returned a non-JSON response, which usually means a node "
                    f"errored mid-workflow. Raw response: {preview}"
                ),
                "intent": "fallback",
                "error": "invalid_json",
            }
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict):
            return {"reply": str(data), "intent": "fallback", "error": None}
        reply = (
            data.get("reply")
            or data.get("output")
            or data.get("text")
            or data.get("message")
            or json.dumps(data)
        )
        return {
            "reply": reply,
            "intent": data.get("intent") or data.get("agent") or "synthesizer",
            "error": None,
        }
    except requests.exceptions.ConnectionError:
        return {
            "reply": (
                "I couldn't reach n8n. Make sure the workflow is **Active** and the "
                "Production Webhook URL on the left is correct."
            ),
            "intent": "fallback",
            "error": "connection",
        }
    except requests.exceptions.Timeout:
        return {
            "reply": "The support agents took too long to reply. Try again in a moment.",
            "intent": "fallback",
            "error": "timeout",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "reply": f"Something went wrong talking to n8n: {exc}",
            "intent": "fallback",
            "error": str(exc),
        }


def avatar_for_intent(intent: Optional[str]) -> str:
    key = intent if intent in AGENT_FILES else "assistant"
    return str(resolve_avatar(key))


def clear_conversation() -> None:
    st.session_state.messages = []
    st.session_state.last_intent = None
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state._pending_prompt = None


def render_left_panel() -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### ✦ NovaAssist")
    st.caption("AI-Powered Customer Support")

    st.markdown('<p class="section-label">Connection</p>', unsafe_allow_html=True)
    st.markdown('<div class="conn-box">', unsafe_allow_html=True)
    st.text_input(
        "n8n Webhook URL",
        key="webhook_url",
        help="Production URL must contain /webhook/ (not /webhook-test/). Workflow must be Active.",
        placeholder="https://....app.github.dev/webhook/support-chat",
    )
    st.text_input("Customer ID (optional)", key="customer_id")
    st.caption(f"Session: `{st.session_state.session_id[:12]}…`")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🗑  Clear Conversation", use_container_width=True, key="btn_clear"):
        clear_conversation()
        st.rerun()

    st.markdown('<p class="section-label">Agent Roster</p>', unsafe_allow_html=True)
    for key in (
        "router",
        "order_status",
        "return_refund",
        "product_query",
        "general_faq",
        "synthesizer",
    ):
        meta = AGENT_META[key]
        st.markdown(
            f"""
<div class="agent-line">
  <div class="agent-badge" style="background:{meta['accent']}">{meta['icon']}</div>
  <div><b>{meta['name']}</b><small>{meta['role']}</small></div>
</div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_topbar() -> None:
    left, right = st.columns([2.2, 1])
    with left:
        st.markdown(
            '<div class="status-pill"><span class="dot"></span> All systems operational</div>',
            unsafe_allow_html=True,
        )
    with right:
        name = st.session_state.get("customer_id") or "Guest User"
        st.markdown(
            f'<div style="text-align:right;"><span class="user-chip">👤 {name}</span></div>',
            unsafe_allow_html=True,
        )


def render_welcome() -> None:
    bot_uri = image_data_uri(resolve_bot_icon())
    st.markdown(
        f"""
<div class="hero-wrap">
  <div class="hero-bot"><img src="{bot_uri}" alt="NovaAssist bot" /></div>
  <p class="hero-title">Hello! I'm <span>NovaAssist</span></p>
  <p class="hero-sub">Your AI support agent for orders, returns, products, and more.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for col, (icon, title, sub) in zip(cols, FEATURES):
        with col:
            st.markdown(
                f'<div class="feat-box"><div class="ic">{icon}</div>'
                f'<div class="t">{title}</div><div class="s">{sub}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.markdown("**Try asking about…**")
    c1, c2 = st.columns(2)
    for i, (icon, text) in enumerate(SUGGESTIONS):
        box = c1 if i % 2 == 0 else c2
        if box.button(f"{icon}  {text}", key=f"sug_{i}", use_container_width=True):
            st.session_state._pending_prompt = text
            st.rerun()


def render_messages() -> None:
    if st.session_state.last_intent:
        meta = AGENT_META.get(st.session_state.last_intent, AGENT_META["fallback"])
        st.markdown(
            f'<div class="route-pill">Last routed → {meta["icon"]} {meta["name"]}</div>',
            unsafe_allow_html=True,
        )
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar=avatar_for_intent("user")):
                st.markdown(msg["content"])
                if msg.get("time"):
                    st.caption(msg["time"])
        else:
            intent = msg.get("intent") or "assistant"
            with st.chat_message("assistant", avatar=avatar_for_intent(intent)):
                label = AGENT_META.get(intent, AGENT_META["fallback"])["name"]
                st.caption(f"Handled via · {label}")
                st.markdown(msg["content"])
                if msg.get("time"):
                    st.caption(msg["time"])


def handle_prompt(prompt: str) -> None:
    now = datetime.now().strftime("%I:%M %p").lstrip("0")
    st.session_state.messages.append({"role": "user", "content": prompt, "time": now})

    with st.chat_message("user", avatar=avatar_for_intent("user")):
        st.markdown(prompt)
        st.caption(now)

    with st.chat_message("assistant", avatar=avatar_for_intent("assistant")):
        with st.spinner("Agents collaborating…"):
            result = call_n8n(prompt, st.session_state.webhook_url)
        intent = result.get("intent") or "synthesizer"
        st.session_state.last_intent = intent
        label = AGENT_META.get(intent, AGENT_META["fallback"])["name"]
        reply_time = datetime.now().strftime("%I:%M %p").lstrip("0")
        st.caption(f"Handled via · {label}")
        st.markdown(result["reply"])
        st.caption(reply_time)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["reply"],
            "intent": intent,
            "time": reply_time,
        }
    )
    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="NovaAssist | AI Customer Support",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    init_state()

    left, right = st.columns([0.95, 2.15], gap="large")
    with left:
        render_left_panel()
    with right:
        render_topbar()
        if not st.session_state.messages:
            render_welcome()
        else:
            render_messages()
        st.markdown(
            '<p class="footer-note">🛡️ Powered by AI · Responses may take a few seconds</p>',
            unsafe_allow_html=True,
        )

    prompt = st.chat_input("I am a chat assistant. How can I help you?")
    if st.session_state._pending_prompt:
        prompt = st.session_state._pending_prompt
        st.session_state._pending_prompt = None
    if prompt:
        handle_prompt(prompt)


if __name__ == "__main__":
    main()
