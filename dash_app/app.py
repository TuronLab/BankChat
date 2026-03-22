import os
import requests
from dash import Dash, html, dcc, Input, Output, State, ctx

# =========================
# Config
# =========================
BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

# =========================
# Helpers
# =========================
def start_conversation():
    res = requests.post(f"{BASE_URL}/start")
    res.raise_for_status()
    return res.json()


def send_message(session_id, message):
    payload = {
        "session_id": session_id,
        "message": message
    }
    res = requests.post(f"{BASE_URL}/message", json=payload)
    res.raise_for_status()
    return res.json()


# =========================
# App
# =========================
app = Dash(__name__)

app.layout = html.Div([
    html.H2("💬 Chat App"),

    # Store session + messages
    dcc.Store(id="session-store"),
    dcc.Store(id="chat-store", data=[]),

    # Chat window
    html.Div(id="chat-window", style={
        "border": "1px solid #ccc",
        "padding": "10px",
        "height": "400px",
        "overflowY": "auto",
        "marginBottom": "10px"
    }),

    # Input
    dcc.Input(id="user-input", type="text", style={"width": "70%"}),
    html.Button("Send", id="send-btn", n_clicks=0),

    html.Br(), html.Br(),

    # Restart
    html.Button("🔄 Restart Conversation", id="restart-btn", n_clicks=0)
])


# =========================
# Start / Restart conversation
# =========================
@app.callback(
    Output("session-store", "data"),
    Output("chat-store", "data"),
    Input("restart-btn", "n_clicks"),
    prevent_initial_call=False
)
def start_or_restart(n_clicks):
    data = start_conversation()

    session_id = data["session_id"]
    message = data["message"]

    chat = [
        {"role": "assistant", "message": message}
    ]

    return session_id, chat


# =========================
# Send message
# =========================
@app.callback(
    Output("chat-store", "data", allow_duplicate=True),
    Input("send-btn", "n_clicks"),
    State("user-input", "value"),
    State("session-store", "data"),
    State("chat-store", "data"),
    prevent_initial_call=True
)
def handle_message(n_clicks, user_input, session_id, chat):
    if not user_input:
        return chat

    # Add user message
    chat.append({"role": "user", "message": user_input})

    # Call API
    data = send_message(session_id, user_input)

    # Add assistant response
    chat.append({"role": "assistant", "message": data["message"]})

    return chat


# =========================
# Render chat
# =========================
@app.callback(
    Output("chat-window", "children"),
    Input("chat-store", "data")
)
def render_chat(chat):
    elements = []

    for msg in chat:
        if msg["role"] == "user":
            style = {
                "textAlign": "right",
                "margin": "5px",
                "padding": "8px",
                "backgroundColor": "#DCF8C6",
                "borderRadius": "8px"
            }
        else:
            style = {
                "textAlign": "left",
                "margin": "5px",
                "padding": "8px",
                "backgroundColor": "#F1F0F0",
                "borderRadius": "8px"
            }

        elements.append(html.Div(msg["message"], style=style))

    return elements


# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(debug=True)