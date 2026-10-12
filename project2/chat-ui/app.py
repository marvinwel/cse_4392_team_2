

import streamlit as st

import streamlit.components.v1 as components

from pathlib import Path

from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

from html import escape

import base64

import re
import os
import requests

LANGCHAIN_API_URL = os.getenv("LANGCHAIN_API_URL", "http://13.59.53.151:8001")

# ==========================================

# PAGE CONFIGURATION

# ==========================================

st.set_page_config(

    page_title="UTA | Team 2 AI Advisor",

    page_icon="🎓",

    layout="wide",

    initial_sidebar_state="expanded"

)

UTA_LOGO = Path(__file__).parent / "assets" / "uta-logo.png"

# ==========================================

# GLOBAL CSS

# ==========================================

st.markdown("""

<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stApp"] {

    font-family: Inter, Arial, sans-serif;

}

[data-testid="stAppViewContainer"] {

    background: #ffffff;

}

[data-testid="stHeader"] {

    height: 0;

    background: transparent;

}

[data-testid="stToolbar"] {

    display: none;

}

.block-container {

    padding: 0 1.65rem 1.5rem !important;

    max-width: 100% !important;

}

/* SIDEBAR */

[data-testid="stSidebar"] {

    background: #f8fbff;

    border-right: 1px solid #e3eaf3;

    min-width: 245px !important;

    max-width: 245px !important;

}

[data-testid="stSidebar"] .block-container {

    padding: 1.15rem .85rem !important;

}

[data-testid="stSidebar"] button {

    text-align: left;

    justify-content: flex-start;

    border: 0;

    box-shadow: none;

    background: transparent;

    color: #17243a;

    font-weight: 550;

    min-height: 47px;

    border-radius: 10px;

    font-size: 14px;

}

[data-testid="stSidebar"] button:hover {

    background: #e7f1ff;

    color: #005ac5;

}

[data-testid="stSidebar"] button[kind="primary"] {

    background: #e2efff;

    color: #0057c5;

    font-weight: 700;

}

[data-testid="stSidebar"] button:disabled {

    color: #17243a;

    opacity: 1;

}

.sidebar-note {

    color: #8291a6;

    font-size: 11px;

    padding: 14px 6px;

    line-height: 1.5;

}

/* UTA HEADER */

.st-key-uta_header {

    position: sticky;

    top: 0;

    z-index: 1000;

    background: white;

}

.topbar {

    height: 86px;

    margin: 0 -1.65rem 24px;

    padding: 0 25px;

    background: linear-gradient(105deg, #07478c, #06356e);

    color: white;

    display: flex;

    align-items: center;

    gap: 18px;

}

.uta-logo {

    font-size: 39px;

    font-weight: 800;

    letter-spacing: -3px;

    color: white;

    line-height: 1;

}

.uta-star {

    color: #f59b36;

    font-size: 25px;

    vertical-align: middle;

    margin-left: -3px;

}

.brand-name {

    font-size: 24px;

    font-weight: 750;

    line-height: 1.2;

}

.brand-sub {

    font-size: 14px;

    color: #bcd5f4;

    margin-top: 3px;

}

.student-name {

    text-align: right;

    color: #e8f2ff;

    font-size: 14px;

    font-weight: 600;

    padding-top: 12px;

    white-space: nowrap;

}

.st-key-logout button {

    background: #0064D9 !important;

    color: white !important;

    border: 1px solid #0064D9 !important;

    border-radius: 8px !important;

    font-weight: 700 !important;

    min-height: 42px !important;

    margin-top: 19px !important;

}

.st-key-logout button:hover {

    background: #004AAB !important;

}

.st-key-logout button p {

    color: white !important;

}

/* CHAT HEADING */

.headline {

    font-size: 26px;

    font-weight: 800;

    color: #111c31;

    margin-bottom: 5px;

}

.subtitle {

    font-size: 14px;

    color: #60718b;

    margin-bottom: 15px;

}

.rule {

    border-top: 1px solid #dfe6ef;

    margin: 12px 0 20px;

}

/* CHAT INPUT */

[data-testid="stBottom"],

[data-testid="stBottom"] > div,

[data-testid="stBottomBlockContainer"] {

    background: #07478c !important;

}

[data-testid="stBottom"] {

    z-index: 100;

}

[data-testid="stChatInput"],

[data-testid="stChatInput"] > div,

[data-testid="stChatInput"] form {

    background: white !important;

    border-radius: 11px !important;

}

[data-testid="stChatInput"] {

    border: 1px solid #0064D9 !important;

}

[data-testid="stChatInput"] textarea {

    background: white !important;

    color: #17243a !important;

    font-family: Inter, Arial, sans-serif;

}

[data-testid="stChatInput"] textarea::placeholder {

    color: #8291a6 !important;

}

[data-testid="stChatInputSubmitButton"] button {

    background: #0064D9 !important;

    color: white !important;

    border-radius: 8px !important;

}

[data-testid="stChatInputSubmitButton"] svg {

    color: white !important;

    stroke: white !important;

}

/* SUGGESTION BUTTONS */

[class*="st-key-suggestion_"] button,

.st-key-refresh_chat button {

    background: #e9f3ff !important;

    color: #0657bd !important;

    border: 1px solid #d4e7ff !important;

    border-radius: 9px !important;

    min-height: 43px !important;

    font-size: 12px !important;

    font-weight: 600 !important;

}

[class*="st-key-suggestion_"] button:hover,

.st-key-refresh_chat button:hover {

    background: #d8eaff !important;

}

@media (max-width: 900px) {

    .brand-name { font-size: 17px; }

    .brand-sub { font-size: 11px; }

    .topbar { gap: 10px; padding: 0 12px; }

    .uta-logo { font-size: 30px; }

    .student-name { font-size: 12px; }

}


/* Responsive chat layout: fill the available viewport instead of a fixed 500px. */
.st-key-chat_area {
    min-height: 0;
    margin-bottom: 0 !important;
}
.st-key-chat_area iframe {
    display: block;
    width: 100% !important;
    height: clamp(220px, calc(100dvh - 300px), 1200px) !important;
    border: 0;
}
/* Streamlit wraps component iframes in fixed-height elements; resize those too. */
.st-key-chat_area [data-testid="stElementContainer"]:has(iframe),
.st-key-chat_area [data-testid="stCustomComponentV1"]:has(iframe) {
    height: clamp(220px, calc(100dvh - 300px), 1200px) !important;
    min-height: 0 !important;
}
/* Quick prompts remain above the chat input as viewport size changes. */
.st-key-quick_actions {
    position: fixed;
    bottom: 85px;
    left: calc(245px + 1.65rem);
    right: 1.65rem;
    z-index: 90;
    background: rgba(255, 255, 255, 0.97);
    padding: 6px 0;
}
.st-key-quick_actions [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap;
    gap: 6px !important;
}
.st-key-quick_actions [data-testid="column"] {
    min-width: 135px !important;
    flex: 1 1 135px !important;
}
.st-key-quick_actions [data-testid="column"]:last-child {
    min-width: 48px !important;
    flex: 0 0 48px !important;
}
@media (max-width: 900px) {
    .st-key-quick_actions {
        left: 1rem;
        right: 1rem;
    }
    .st-key-chat_area iframe,
    .st-key-chat_area [data-testid="stElementContainer"]:has(iframe),
    .st-key-chat_area [data-testid="stCustomComponentV1"]:has(iframe) {
        height: clamp(220px, calc(100dvh - 340px), 1200px) !important;
    }
}
@media (max-width: 600px) {
    .block-container { padding-left: .8rem !important; padding-right: .8rem !important; }
    .st-key-quick_actions { bottom: 84px; left: .8rem; right: .8rem; }
    .st-key-quick_actions [data-testid="column"] { min-width: 110px !important; }
    .st-key-chat_area iframe,
    .st-key-chat_area [data-testid="stElementContainer"]:has(iframe),
    .st-key-chat_area [data-testid="stCustomComponentV1"]:has(iframe) {
        height: clamp(200px, calc(100dvh - 390px), 1200px) !important;
    }
}

</style>

""", unsafe_allow_html=True)

# ==========================================

# CHAT STATE

# ==========================================

WELCOME = (

    "Hello! I’m your UTA CSE AI Advisor (Team 2).\n\n"

    "I can help you with course information, prerequisites, "

    "schedule conflicts, and degree planning.\n\n"

    "How can I help you today?"

)

def timestamp_now():

    return datetime.now(ZoneInfo("America/Chicago")).strftime("%I:%M %p")

def new_chat():

    st.session_state.pop("pending_requests", None)
    st.session_state.messages = [

        {

            "role": "assistant",

            "content": WELCOME,

            "timestamp": timestamp_now()

        }

    ]

if "messages" not in st.session_state:

    new_chat()

if "signed_out_preview" not in st.session_state:

    st.session_state.signed_out_preview = False

# ==========================================

# CHAT HELPERS

# ==========================================

def render_message_text(content):
    """Render chat messages without unnecessary blank lines."""
    content = escape(str(content))

    # Remove extra blank lines
    content = re.sub(r"\n\s*\n+", "\n", content)

    # Convert Markdown bold to HTML bold
    content = re.sub(
        r"\*\*(.+?)\*\*",
        r"<strong>\1</strong>",
        content,
        flags=re.DOTALL
    )
    return content.replace("\n", "<br>")


def get_advisor_avatar():

    """

    Embed the UTA logo directly into the chat iframe.

    """

    if UTA_LOGO.exists():

        encoded = base64.b64encode(

            UTA_LOGO.read_bytes()

        ).decode("utf-8")

        return (

            '<img src="data:image/png;base64,'

            + encoded

            + '" alt="UTA Advisor" />'

        )

    return "🎓"

@st.cache_resource
def get_request_executor():
    # Shared worker pool; no Streamlit UI calls inside worker threads.
    return ThreadPoolExecutor(max_workers=4)


def ask_langchain(prompt):
    try:
        api_response = requests.post(
            f"{LANGCHAIN_API_URL.rstrip('/')}/chat",
            json={"message": prompt},
            timeout=120,
        )
        api_response.raise_for_status()
        data = api_response.json()
        return data.get("answer") or "The AI Advisor did not return an answer."
    except requests.exceptions.RequestException:
        return "I'm having trouble connecting to the AI Advisor backend. Please try again shortly."
    except ValueError:
        return "The AI Advisor returned an invalid response."


def reply_to(prompt):
    """Display a message immediately and process each request independently."""
    st.session_state.messages.append({
        "role": "user", "content": prompt, "timestamp": timestamp_now()
    })
    st.session_state.messages.append({
        "role": "assistant", "content": "", "timestamp": "", "loading": True
    })
    index = len(st.session_state.messages) - 1
    future = get_request_executor().submit(ask_langchain, prompt)
    if "pending_requests" not in st.session_state:
        st.session_state.pending_requests = []
    st.session_state.pending_requests.append({"future": future, "index": index})


# ==========================================

with st.sidebar:

    st.markdown(

        '<div style="font-weight:800;color:#074d9c;'

        'font-size:18px;padding:10px 8px 20px">'

        '🎓 Team 2 AI Advisor</div>',

        unsafe_allow_html=True

    )

    st.button(

        "💬   Chat Advisor",

        key="chat_nav",

        type="primary",

        use_container_width=True

    )

    for label in (

        "🎓   Degree Planner",

        "📖   Course Search",

        "📊   My Progress",

        "🗓️   Schedule Check",

        "👤   My Profile"

    ):

        st.button(

            label,

            disabled=True,

            use_container_width=True

        )

    st.divider()

    st.button(

        "＋   New Chat",

        on_click=new_chat,

        use_container_width=True

    )

    st.markdown(

        '<div class="sidebar-note">'

        'Chat UI • Cognito login '

        'will be connected later; AI backend is connected.'

        '</div>',

        unsafe_allow_html=True

    )

# ==========================================

# UTA HEADER

# ==========================================

with st.container(key="uta_header"):

    header_left, header_user, header_logout = st.columns(

        [7, 1.45, 1.25],

        gap="small"

    )

    with header_left:

        st.markdown(

            '<div class="topbar" style="margin-right:-12px">'

            '<div class="uta-logo">'

            'UTA<span class="uta-star">★</span>'

            '</div>'

            '<div>'

            '<div class="brand-name">Team 2 AI Advisor</div>'

            '<div class="brand-sub">'

            'Computer Science Academic Advisor'

            '</div>'

            '</div>'

            '</div>',

            unsafe_allow_html=True

        )

    with header_user:

        st.markdown(

            '<div class="topbar" '

            'style="margin-left:-16px;margin-right:-12px;'

            'padding:0 5px;justify-content:center">'

            '<div class="student-name">'

            '👤 &nbsp;Student ▾'

            '</div>'

            '</div>',

            unsafe_allow_html=True

        )

    with header_logout:

        if st.button(

            "⇥  Logout",

            key="logout",

            type="primary",

            use_container_width=True

        ):

            new_chat()

            st.session_state.signed_out_preview = True

            st.rerun()

# ==========================================

# MAIN CONTENT

# ==========================================

if st.session_state.signed_out_preview:

    st.info(

        "Logout clicked. This is a UI preview; "

        "Amazon Cognito authentication is not connected yet."

    )

    if st.button("Return to chat preview"):

        st.session_state.signed_out_preview = False

        st.rerun()

else:

    st.markdown(

        '<div class="headline">'

        'Chat with Your AI Advisor'

        '</div>'

        '<div class="subtitle">'

        'Ask questions about courses, prerequisites, '

        'schedules, or degree planning.'

        '</div>'

        '<div class="rule"></div>',

        unsafe_allow_html=True

    )

    # ==========================================

    # BUILD CHAT MESSAGES

    # ==========================================

    @st.fragment(run_every="1s")
    def render_chat():
        remaining = []
        for pending in st.session_state.get("pending_requests", []):
            if not pending["future"].done():
                remaining.append(pending)
                continue
            try:
                answer = pending["future"].result()
            except Exception:
                answer = "The AI Advisor encountered an unexpected error. Please try again."
            index = pending["index"]
            if index < len(st.session_state.messages) and st.session_state.messages[index].get("loading"):
                st.session_state.messages[index] = {
                    "role": "assistant",
                    "content": answer,
                    "timestamp": timestamp_now(),
                }
        st.session_state.pending_requests = remaining

        chat_items = []

        advisor_avatar = get_advisor_avatar()

        for msg in st.session_state.messages:

            role = msg["role"]

            content = render_message_text(msg["content"])
            if msg.get("loading"):
                content = '<span class="typing-indicator"><span></span><span></span><span></span></span>' 

            timestamp = escape(msg.get("timestamp", ""))

            if role == "user":

                chat_items.append(f"""

                    <div class="message-row user-row">

                        <div class="message-group">

                            <div class="bubble user-bubble">

                                {content}

                            </div>

                            <div class="timestamp user-time">

                                {timestamp}

                            </div>

                        </div>

                        <div class="avatar user-avatar">

                            👤

                        </div>

                    </div>

                """)

            else:

                chat_items.append(f"""

                    <div class="message-row assistant-row">

                        <div class="avatar assistant-avatar">

                            {advisor_avatar}

                        </div>

                        <div class="message-group">

                            <div class="bubble assistant-bubble">

                                {content}

                            </div>

                            <div class="timestamp assistant-time">

                                {timestamp}

                            </div>

                        </div>

                    </div>

                """)

        chat_html = "\n".join(chat_items)

        # ==========================================

        # SCROLLABLE CHAT WITH AUTO-SCROLL

        # ==========================================

        components.html(

            f"""

            <!DOCTYPE html>

            <html>

            <head>

            <meta charset="UTF-8">

            <style>
                .typing-indicator {{
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                    height: 22px;
                }}
                .typing-indicator span {{
                    width: 7px;
                    height: 7px;
                    background: #8291a6;
                    border-radius: 50%;
                    animation: typing 1.2s infinite ease-in-out;
                }}
                .typing-indicator span:nth-child(2) {{ animation-delay: .2s; }}
                .typing-indicator span:nth-child(3) {{ animation-delay: .4s; }}
                @keyframes typing {{
                    0%, 60%, 100% {{ transform: translateY(0); opacity: .4; }}
                    30% {{ transform: translateY(-5px); opacity: 1; }}
                }}


                * {{

                    box-sizing: border-box;

                }}

                html, body {{

                    margin: 0;

                    padding: 0;

                    height: 100%;

                    overflow: hidden;

                    font-family: Inter, Arial, sans-serif;

                    background: white;

                }}

                #chat-container {{

                    height: 100vh;

                    overflow-y: auto;

                    overflow-x: hidden;

                    padding: 12px 10px 20px 0;

                    scrollbar-width: thin;

                    scrollbar-color: #a8bdd6 transparent;

                    scroll-behavior: auto;

                }}

                .message-row {{

                    display: flex;

                    align-items: flex-start;

                    gap: 12px;

                    margin-bottom: 20px;

                    width: 100%;

                }}

                .user-row {{

                    justify-content: flex-end;

                }}

                .assistant-row {{

                    justify-content: flex-start;

                }}

                .message-group {{

                    max-width: 55%;

                    min-width: 0;

                }}

                .bubble {{

                    padding: 13px 17px;

                    border-radius: 13px;

                    font-size: 14px;

                    line-height: 1.6;

                    overflow-wrap: anywhere;

                }}

                .user-bubble {{

                    background: #0064D9;

                    color: white;

                }}

                .assistant-bubble {{

                    background: #F0F3F8;

                    color: #17243A;

                }}

                .avatar {{

                    width: 36px;

                    height: 36px;

                    flex-shrink: 0;

                    display: flex;

                    align-items: center;

                    justify-content: center;

                    font-size: 23px;

                }}

                .assistant-avatar img {{

                    width: 32px;

                    height: 32px;

                    object-fit: contain;

                    border-radius: 50%;

                }}

                .timestamp {{

                    color: #8291a6;

                    font-size: 11px;

                    margin-top: 5px;

                    line-height: 1.4;

                }}

                .user-time {{

                    text-align: right;

                }}

                .assistant-time {{

                    text-align: left;

                }}

                @media (max-width: 700px) {{

                    .message-group {{

                        max-width: 80%;

                    }}

                }}

            </style>

            </head>

            <body>

                <div id="chat-container">

                    {chat_html}

                    <div id="chat-bottom"></div>

                </div>

                <script>

                    function scrollToBottom() {{

                        const chat = document.getElementById(

                            "chat-container"

                        );

                        if (chat) {{

                            chat.scrollTop = chat.scrollHeight;

                        }}

                    }}

                    // Scroll as soon as the component renders.

                    scrollToBottom();

                    window.addEventListener(

                        "load",

                        scrollToBottom

                    );

                    requestAnimationFrame(

                        scrollToBottom

                    );

                    setTimeout(scrollToBottom, 100);

                    setTimeout(scrollToBottom, 300);

                </script>

            </body>

            </html>

            """,

            height=650,

            scrolling=False

        )

        # ==========================================

        # SUGGESTION BUTTONS

        # ==========================================


    with st.container(key="chat_area"):
        render_chat()

    # with st.container(key="quick_actions"):
    #     cols = st.columns(

    #     [1.15, 1.2, 1.35, 0.4],

    #     gap="small"

    # )

    #     suggestions = [

    #         "Can I take this course?",

    #         "What are the prerequisites?",

    #         "Show available sections"

    #     ]

    #     for i, (col, suggestion) in enumerate(

    #         zip(cols[:3], suggestions)

    #     ):

    #         with col:

    #             if st.button(

    #                 suggestion,

    #                 key=f"suggestion_{i}",


    #                 use_container_width=True

    #             ):

    #                 reply_to(suggestion)

    #                 st.rerun()

    #     with cols[3]:

    #         if st.button(

    #             "↻",

    #             key="refresh_chat",

    #             use_container_width=True,

    #             help="Start a new chat"

    #         ):

    #             new_chat()

    #             st.rerun()




    # ==========================================

    # CHAT INPUT

    # ==========================================

    if prompt := st.chat_input(

        "Type your message here...",

        disabled=False

    ):

        reply_to(prompt)

        st.rerun()
