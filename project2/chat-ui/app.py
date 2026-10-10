
import streamlit as st
import streamlit.components.v1 as components

from pathlib import Path
from datetime import datetime
from html import escape
import base64
import re


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
    return datetime.now().strftime("%I:%M %p")


def new_chat():
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
    """
    Safely format basic Markdown for HTML chat bubbles.
    """
    content = escape(content)

    content = re.sub(
        r"\*\*(.*?)\*\*",
        r"<strong>\1</strong>",
        content,
        flags=re.DOTALL
    )

    content = content.replace("\n", "<br>")

    return content


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


def reply_to(prompt):
    """
    Add the student message and a preview response.
    Replace the preview response with LangChain later.
    """
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": timestamp_now()
    })

    response = (
        "**Advisor:** Your message was received. "
        "Once the LangChain backend is connected, "
        "I’ll be able to answer your question."
       # "**Your question:** " + prompt
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "timestamp": timestamp_now()
    })


# ==========================================
# SIDEBAR
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
        'Chat UI • Cognito login and AI backend '
        'will be connected later.'
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

    chat_items = []

    advisor_avatar = get_advisor_avatar()

    for msg in st.session_state.messages:

        role = msg["role"]
        content = render_message_text(msg["content"])
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
        height=500,
        scrolling=False
    )

    # ==========================================
    # SUGGESTION BUTTONS
    # ==========================================

    st.markdown(
        '<div style="height:8px"></div>',
        unsafe_allow_html=True
    )

    cols = st.columns(
        [1.15, 1.2, 1.35, 0.4],
        gap="small"
    )

    suggestions = [
        "Can I take this course?",
        "What are the prerequisites?",
        "Show available sections"
    ]

    for i, (col, suggestion) in enumerate(
        zip(cols[:3], suggestions)
    ):

        with col:

            if st.button(
                suggestion,
                key=f"suggestion_{i}",
                use_container_width=True
            ):
                reply_to(suggestion)
                st.rerun()

    with cols[3]:

        if st.button(
            "↻",
            key="refresh_chat",
            use_container_width=True,
            help="Start a new chat"
        ):
            new_chat()
            st.rerun()

    # ==========================================
    # CHAT INPUT
    # ==========================================

    if prompt := st.chat_input(
        "Type your message here..."
    ):

        reply_to(prompt)

        st.rerun()
