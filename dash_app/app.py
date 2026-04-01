import os
import requests

from dash import Dash, html, dcc, Input, Output, State


# =========================
# Config
# =========================
BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")


# =========================
# API Helpers
# =========================
def start_conversation():
    res = requests.post(f"{BASE_URL}/start", timeout=60)
    res.raise_for_status()
    return res.json()


def send_message(session_id, message):
    payload = {"session_id": session_id, "message": message}
    res = requests.post(f"{BASE_URL}/message", json=payload, timeout=60)
    res.raise_for_status()
    return res.json()


# =========================
# App
# =========================
app = Dash(__name__)
app.title = "Chat Assistant"

app.layout = html.Div(
    [
        dcc.Store(id="session-store"),
        dcc.Store(id="chat-store", data=[]),
        dcc.Store(id="pending-message"),
        dcc.Store(id="processing-trigger"),

        html.Div(
            [
                html.Div(
                    [
                        html.Div("Chat Assistant", className="app-title"),
                        html.Div("FastAPI-backed chat", className="app-subtitle"),
                    ],
                    className="header-left",
                ),
                html.Button("Restart", id="restart-btn", n_clicks=0, className="restart-btn"),
            ],
            className="topbar",
        ),

        html.Div(id="chat-window", className="chat-window"),

        html.Div(
            [
                dcc.Textarea(
                    id="user-input",
                    placeholder="Type a message… (Enter to send, Shift+Enter for newline)",
                    className="chat-input",
                    value="",
                ),
                html.Button("Send", id="send-btn", n_clicks=0, className="send-btn"),
            ],
            className="composer",
        ),

        html.Div(
            "Press Enter to send • Shift+Enter for newline • Restart starts a fresh session",
            className="footer-note",
        ),

        html.Div(id="scroll-anchor", style={"display": "none"}),
    ],
    className="page",
)


# =========================
# Start / Restart conversation
# =========================
@app.callback(
    Output("session-store", "data"),
    Output("chat-store", "data"),
    Input("restart-btn", "n_clicks"),
    prevent_initial_call=False,
)
def start_or_restart(n_clicks):
    try:
        data = start_conversation()
        return data["session_id"], [
            {"role": "assistant", "message": data["message"], "kind": "welcome"}
        ]
    except Exception as e:
        return None, [{"role": "assistant", "message": f"Error starting session: {e}", "kind": "error"}]


# =========================
# 1) Add user message immediately
# =========================
@app.callback(
    Output("chat-store", "data", allow_duplicate=True),
    Output("pending-message", "data"),
    Output("user-input", "value"),
    Input("send-btn", "n_clicks"),
    State("user-input", "value"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def add_user_message(n_clicks, user_input, chat):
    if not user_input or not user_input.strip():
        return chat, None, ""

    chat = chat or []
    clean_message = user_input.strip()
    chat.append({"role": "user", "message": clean_message})

    return chat, clean_message, ""


# =========================
# 2) Show typing indicator
# =========================
@app.callback(
    Output("chat-store", "data", allow_duplicate=True),
    Output("processing-trigger", "data"),
    Input("pending-message", "data"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def show_typing(pending_message, chat):
    if not pending_message:
        return chat, None

    chat = chat or []
    chat.append({"role": "assistant", "message": "Typing…", "kind": "typing"})
    return chat, pending_message


# =========================
# 3) Call API and replace typing
# =========================
@app.callback(
    Output("chat-store", "data", allow_duplicate=True),
    Input("processing-trigger", "data"),
    State("session-store", "data"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def process_message(trigger, session_id, chat):
    if not trigger:
        return chat

    chat = chat or []

    try:
        data = send_message(session_id, trigger)
        response = data["message"]

        if chat and chat[-1].get("kind") == "typing":
            chat[-1] = {"role": "assistant", "message": response}
        else:
            chat.append({"role": "assistant", "message": response})

    except Exception as e:
        error_text = f"Error: {e}"
        if chat and chat[-1].get("kind") == "typing":
            chat[-1] = {"role": "assistant", "message": error_text, "kind": "error"}
        else:
            chat.append({"role": "assistant", "message": error_text, "kind": "error"})

    return chat


# =========================
# Render chat
# =========================
@app.callback(
    Output("chat-window", "children"),
    Input("chat-store", "data"),
)
def render_chat(chat):
    if not chat:
        return []

    elements = []

    for msg in chat:
        is_user = msg["role"] == "user"
        kind = msg.get("kind", "")

        if is_user:
            row_class = "message-row user"
            bubble_class = "bubble bubble-user"
        else:
            row_class = "message-row assistant"
            bubble_class = "bubble bubble-assistant"

            if kind == "welcome":
                bubble_class += " bubble-welcome"
            elif kind == "typing":
                bubble_class += " bubble-typing"
            elif kind == "error":
                bubble_class += " bubble-error"

        elements.append(
            html.Div(
                html.Div(msg["message"], className=bubble_class),
                className=row_class,
            )
        )

    return elements


# =========================
# Auto-scroll to bottom
# =========================
app.clientside_callback(
    """
    function(children) {
        const chat = document.querySelector('.chat-window');
        if (chat) {
            chat.scrollTop = chat.scrollHeight;
        }
        return '';
    }
    """,
    Output("scroll-anchor", "children"),
    Input("chat-window", "children"),
)


# =========================
# Keyboard handling:
# Enter sends, Shift+Enter inserts newline
# =========================
app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        :root {
            --bg1: #eef2ff;
            --bg2: #f8fafc;
            --panel: rgba(255, 255, 255, 0.78);
            --border: rgba(148, 163, 184, 0.25);
            --text: #0f172a;
            --muted: #64748b;
            --user: #2563eb;
            --assistant: #ffffff;
            --assistant-border: #e2e8f0;
            --shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
        }

        * { box-sizing: border-box; }

        html, body, #react-entry-point {
            height: 100%;
            margin: 0;
        }

        body {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background:
                radial-gradient(circle at top left, rgba(99, 102, 241, 0.20), transparent 28%),
                radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 22%),
                linear-gradient(180deg, var(--bg1), var(--bg2));
            color: var(--text);
        }

        .page {
            height: 100vh;
            width: 90%;
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            padding: 16px;
            gap: 12px;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: var(--shadow);
            flex: 0 0 auto;
        }

        .header-left {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .app-title {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .app-subtitle {
            font-size: 13px;
            color: var(--muted);
        }

        .restart-btn {
            border: 1px solid rgba(37, 99, 235, 0.18);
            background: rgba(255, 255, 255, 0.9);
            color: #1d4ed8;
            font-weight: 700;
            border-radius: 999px;
            padding: 10px 16px;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.08);
        }

        .restart-btn:hover {
            transform: translateY(-1px);
            background: #ffffff;
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.12);
        }

        .chat-window {
            flex: 1 1 auto;
            min-height: 0;
            overflow-y: auto;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            background: var(--panel);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 28px;
            box-shadow: var(--shadow);
        }

        .message-row {
            display: flex;
            width: 100%;
        }

        .message-row.user {
            justify-content: flex-end;
        }

        .message-row.assistant {
            justify-content: flex-start;
        }

        .bubble {
            max-width: min(78%, 760px);
            padding: 13px 16px;
            border-radius: 22px;
            line-height: 1.5;
            font-size: 15px;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
        }

        .bubble-user {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            border-bottom-right-radius: 6px;
        }

        .bubble-assistant {
            background: var(--assistant);
            color: #0f172a;
            border: 1px solid var(--assistant-border);
            border-bottom-left-radius: 6px;
        }

        .bubble-welcome {
            background: linear-gradient(135deg, #f8fafc, #eff6ff);
            border-color: #dbeafe;
        }

        .bubble-typing {
            opacity: 0.82;
            font-style: italic;
        }

        .bubble-error {
            background: #fff1f2;
            border-color: #fecdd3;
            color: #9f1239;
        }

        .composer {
            flex: 0 0 auto;
            display: flex;
            gap: 12px;
            align-items: stretch;
            padding: 14px;
            background: rgba(255, 255, 255, 0.80);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(12px);
        }

        .chat-input {
            flex: 1 1 auto;
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 18px;
            padding: 12px 14px;
            font-size: 15px;
            outline: none;
            line-height: 1.45;
            font-family: inherit;
            resize: none;
            min-height: 46px;
            max-height: 180px;
            overflow-y: auto;
            background: rgba(255, 255, 255, 0.96);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }

        .chat-input:focus {
            border-color: rgba(37, 99, 235, 0.55);
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
        }

        .send-btn {
            border: none;
            border-radius: 18px;
            padding: 0 22px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            font-size: 15px;
            font-weight: 800;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
            box-shadow: 0 14px 24px rgba(37, 99, 235, 0.22);
            min-width: 106px;
        }

        .send-btn:hover {
            transform: translateY(-1px);
            filter: brightness(1.03);
            box-shadow: 0 16px 28px rgba(37, 99, 235, 0.28);
        }

        .footer-note {
            flex: 0 0 auto;
            text-align: center;
            font-size: 12px;
            color: var(--muted);
            padding-bottom: 2px;
        }

        @media (max-width: 720px) {
            .page {
                padding: 10px;
                gap: 10px;
            }

            .topbar,
            .composer {
                border-radius: 20px;
            }

            .topbar,
            .composer {
                flex-direction: column;
                align-items: stretch;
            }

            .restart-btn,
            .send-btn {
                width: 100%;
                min-height: 46px;
            }

            .bubble {
                max-width: 90%;
            }
        }
    </style>

    <script>
        // Enter sends. Shift+Enter makes a newline.
        document.addEventListener("keydown", function (e) {
            const target = e.target;
            if (!target || target.id !== "user-input") return;

            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const btn = document.getElementById("send-btn");
                if (btn) btn.click();
            }
        });

        // Auto-grow textarea up to a max height.
        document.addEventListener("input", function (e) {
            const target = e.target;
            if (!target || target.id !== "user-input") return;

            if (target.tagName === "TEXTAREA") {
                target.style.height = "auto";
                target.style.height = Math.min(target.scrollHeight, 180) + "px";
            }
        });
    </script>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(
        host=os.getenv("DASH_HOST", "0.0.0.0"),
        port=os.getenv("DASH_PORT", 8050),
        debug=bool(os.getenv("DEBUG_DASH", False))
    )