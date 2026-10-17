
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

    initial_sidebar_state="collapsed",

)

UTA_LOGO = Path(__file__).parent / "assets" / "uta-logo.png"

# Custom login uses Cognito USER_PASSWORD_AUTH, not Streamlit OIDC st.login().
# Passwords are passed directly to Cognito over HTTPS and are not persisted.
import hashlib
import hmac
import time
import boto3
import jwt
from botocore.exceptions import ClientError, BotoCoreError
import json


@st.cache_resource
def get_cognito_secrets():
    client = boto3.client(
        "secretsmanager",
        region_name="us-east-2"
    )

    response = client.get_secret_value(
        SecretId="uta-ai-advisor/cognito"
    )

    return json.loads(response["SecretString"])


COGNITO_REGION = "us-east-2"
COGNITO_POOL_ID = "us-east-2_eM4o9bwmk"
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}"

cognito_secrets = get_cognito_secrets()

COGNITO_CLIENT_ID = cognito_secrets["client_id"]
COGNITO_CLIENT_SECRET = cognito_secrets["client_secret"]

LOGIN_BACKGROUND = Path(__file__).parent / "assets" / "uta-login-campus.jpg"

@st.cache_resource
def cognito_client():
    return boto3.client("cognito-idp", region_name=COGNITO_REGION)

@st.cache_resource
def jwt_keys():
    return jwt.PyJWKClient(f"{COGNITO_ISSUER}/.well-known/jwks.json")

def secret_hash(username):
    digest = hmac.new(
        COGNITO_CLIENT_SECRET.encode("utf-8"),
        (username + COGNITO_CLIENT_ID).encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("ascii")

def verify_identity(id_token):
    key = jwt_keys().get_signing_key_from_jwt(id_token).key
    claims = jwt.decode(
        id_token,
        key,
        algorithms=["RS256"],
        audience=COGNITO_CLIENT_ID,
        issuer=COGNITO_ISSUER,
        options={"require": ["exp", "iat", "iss", "sub", "aud"]},
    )
    if claims.get("token_use") != "id":
        raise ValueError("Unexpected Cognito token type")
    return claims

def complete_sign_in(auth_result, username):
    claims = verify_identity(auth_result["IdToken"])
    access_token = auth_result["AccessToken"]
    display_name = claims.get("name") or claims.get("nickname") or username
    # GetUser returns user attributes when the token has Cognito's user-admin scope.
    try:
        user = cognito_client().get_user(AccessToken=access_token)
        attrs = {x["Name"]: x["Value"] for x in user.get("UserAttributes", [])}
        display_name = attrs.get("name") or attrs.get("nickname") or display_name
    except (ClientError, BotoCoreError):
        pass
    st.session_state["cognito_auth"] = {
        "sub": claims["sub"],
        "username": username,
        "display_name": display_name,
        "id_token": auth_result["IdToken"],
        "access_token": access_token,
        "refresh_token": auth_result.get("RefreshToken"),
        "expires_at": time.time() + int(auth_result.get("ExpiresIn", 3600)) - 30,
    }

def sign_out():
    auth = st.session_state.get("cognito_auth") or {}
    if auth.get("refresh_token"):
        try:
            cognito_client().revoke_token(
                Token=auth["refresh_token"],
                ClientId=COGNITO_CLIENT_ID,
                ClientSecret=COGNITO_CLIENT_SECRET,
            )
        except (ClientError, BotoCoreError):
            pass
    for key in ("cognito_auth", "messages", "pending_requests", "cognito_challenge"):
        st.session_state.pop(key, None)
    st.rerun()

def show_login():
    if LOGIN_BACKGROUND.exists():
        encoded = base64.b64encode(LOGIN_BACKGROUND.read_bytes()).decode("ascii")
        background = f"url('data:image/jpeg;base64,{encoded}')"
    else:
        background = "linear-gradient(135deg,#063a83,#0064d9)"
    st.markdown(f"""
    <style>
      [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(100deg,rgba(0,33,83,.22),rgba(0,30,75,.48)), {background};
        background-position:center; background-size:cover;
      }}
      [data-testid="stHeader"], [data-testid="stToolbar"],
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{display:none!important;}}
      [data-testid="stMainBlockContainer"] {{max-width:560px!important;padding:3vh 20px!important;}}
      .login-brand {{text-align:center; margin:0 0 24px;}}
      .login-uta {{font-size:72px;font-weight:900;letter-spacing:-7px;color:#0056b8;line-height:1;}}
      .login-uta span {{font-size:39px;color:#ef8624;vertical-align:middle;letter-spacing:0;}}
      .login-title {{font-size:29px;font-weight:800;color:#12233b;margin:9px 0;}}
      .login-subtitle {{font-size:15px;color:#64748b;line-height:1.6;}}
      .login-footer {{font-size:12px;color:#64748b;text-align:center;margin-top:18px;}}
      [data-testid="stForm"] {{background:rgba(255,255,255,.98);padding:36px 42px 30px;
          border-radius:18px;border:1px solid #e0e6ef;box-shadow:0 18px 55px #001e4b55;}}
      [data-testid="stForm"] label {{font-weight:650;color:#1b2a41;}}
      [data-testid="stFormSubmitButton"] button {{background:#075dcc!important;color:white!important;
          border:none!important;min-height:50px!important;font-weight:750!important;border-radius:9px!important;}}
      [data-testid="stFormSubmitButton"] button:hover {{background:#004aab!important;}}

        /* White username and password fields (login only) */
    [data-testid="stForm"] div[data-baseweb="input"],
    [data-testid="stForm"] div[data-baseweb="base-input"],
    [data-testid="stForm"] div[data-baseweb="input"] > div {{
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        border-radius: 8px !important;
    }}
    [data-testid="stForm"] input {{
        background-color: #ffffff !important;
        color: #17253d !important;
        -webkit-text-fill-color: #17253d !important;
        caret-color: #17253d !important;
    }}
    [data-testid="stForm"] input::placeholder {{
        color: #8291a6 !important;
        -webkit-text-fill-color: #8291a6 !important;
    }}
    [data-testid="stForm"] input:-webkit-autofill {{
        -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
        -webkit-text-fill-color: #17253d !important;
    }}
    [data-testid="stForm"] div[data-baseweb="input"] button {{
        background-color: #ffffff !important;
        color: #17253d !important;
    }}
    [data-testid="stForm"] div[data-baseweb="input"] svg {{
        color: #17253d !important;
        fill: none !important;
    }}

      @media(max-width:600px) {{[data-testid="stForm"] {{padding:25px 18px;}}
          .login-uta {{font-size:58px;}}}}
    </style>""", unsafe_allow_html=True)
    with st.form("cognito_custom_login", clear_on_submit=True):
        st.markdown('<div class="login-brand"><div class="login-uta">UTA<span>★</span></div>'
                    '<div class="login-title">Team 2 AI Advisor</div>'
                    '<div class="login-subtitle">Your AI-powered academic advisor<br>for UTA Computer Science</div></div>', unsafe_allow_html=True)
        username = st.text_input("UT Arlington NetID or Username", placeholder="Enter your username", autocomplete="username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        st.markdown('<div class="login-footer">Secure student sign-in powered by Amazon Cognito</div>', unsafe_allow_html=True)
    if submitted:
        if not username.strip() or not password:
            st.error("Enter your username and password.")
            return
        username = username.strip()
        try:
            response = cognito_client().initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                ClientId=COGNITO_CLIENT_ID,
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                    "SECRET_HASH": secret_hash(username),
                },
            )
            if "AuthenticationResult" in response:
                complete_sign_in(response["AuthenticationResult"], username)
                st.rerun()
            else:
                st.error("This account requires an additional Cognito challenge (such as MFA or a password change). Use the Cognito managed login until that flow is implemented.")
        except cognito_client().exceptions.NotAuthorizedException:
            st.error("Incorrect username or password.")
        except cognito_client().exceptions.UserNotFoundException:
            st.error("Incorrect username or password.")
        except cognito_client().exceptions.InvalidParameterException:
            st.error("Cognito rejected the authentication request. Check that USER_PASSWORD_AUTH is enabled for this app client.")
        except (ClientError, BotoCoreError) as exc:
            st.error("Unable to sign in. Verify the Cognito app client configuration and AWS credentials.")
        except (jwt.PyJWTError, ValueError):
            st.error("Cognito returned an identity token that could not be verified.")

auth = st.session_state.get("cognito_auth")
if not auth or time.time() >= auth["expires_at"]:
    st.session_state.pop("cognito_auth", None)
    show_login()
    st.stop()

student_display_name = auth["display_name"]
# NOTE: Frontend login is not backend authorization. FastAPI must validate
# a Cognito access token and map the verified sub to a student record before
# returning transcripts or other private student data.

# ==========================================

# GLOBAL CSS

# ==========================================

st.markdown("""

<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {

    /* Vertical space reserved at the bottom for the fixed chat input */

    --input-space: 96px;

}

html, body, [data-testid="stApp"] {

    font-family: Inter, Arial, sans-serif;

}

[data-testid="stAppViewContainer"] {

    background: #ffffff;

}

/* Native sidebar is unused: custom navigation rail below. */

[data-testid="stSidebar"],

[data-testid="stSidebarCollapsedControl"] { display: none !important; }

[data-testid="stHeader"] { height: 0 !important; background: transparent !important; }

[data-testid="stToolbar"] { display: none; }

/* ------------------------------------------

   FIXED APP SHELL

   Everything is exactly (viewport - input space) tall,

   so the fixed chat input always has room and is never clipped.

   Only the chat iframe scrolls.

   ------------------------------------------ */

html, body, [data-testid="stApp"],

[data-testid="stAppViewContainer"],

[data-testid="stMain"] {

    height: 100dvh !important;

    max-height: 100dvh !important;

    overflow: hidden !important;

}

[data-testid="stMain"] > div { overscroll-behavior: none; }

[data-testid="stMainBlockContainer"] {

    height: calc(100dvh - var(--input-space)) !important;

    max-height: calc(100dvh - var(--input-space)) !important;

    overflow: hidden !important;

    padding: 0 12px !important;

    max-width: 100% !important;

}

[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"],

[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"],

[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {

    height: calc(100dvh - var(--input-space)) !important;

    min-height: 0 !important;

}

[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {

    align-items: stretch !important;

    gap: 0 !important;

}

/* ------------------------------------------

   NAVIGATION RAIL

   ------------------------------------------ */

.st-key-nav_rail {

    position: relative !important;

    top: auto !important;

    height: calc(100dvh - var(--input-space)) !important;

    min-height: 0 !important;

    overflow-y: auto !important;

    background: #f8fafc !important;

    padding: 16px 8px !important;

    border-right: 1px solid #e5eaf0;

}

.st-key-nav_rail [data-testid="stButton"] button {

    width: 100%;

    border: 0;

    box-shadow: none;

    background: transparent;

    color: #17243a;

    min-height: 45px !important;

    font-size: 14px !important;

    border-radius: 9px;

    transition: background-color .15s ease;

}

.st-key-nav_rail [data-testid="stButton"] button:hover { background: #e7f1ff; color: #005ac5; }

.st-key-nav_rail [data-testid="stButton"] button:disabled { opacity: .7; color: #52657e; }

.st-key-nav_rail [data-testid="stButton"] button[kind="primary"] { background: #e2efff; color: #0057c5; }

.st-key-nav_rail [data-testid="stButton"] button p { white-space: nowrap; }

/* ------------------------------------------

   UTA HEADER

   (no negative margins, so nothing runs off-screen)

   ------------------------------------------ */

.st-key-uta_header {

    position: relative !important;

    top: auto !important;

    z-index: 10 !important;

    background: white;

}

.st-key-uta_header [data-testid="stHorizontalBlock"] {

    gap: 0 !important;

    align-items: flex-start !important;

}

.topbar {

    height: 86px;

    margin: 0 0 24px;

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

    white-space: nowrap;

}

.st-key-logout { padding-left: 14px; }

.st-key-logout button {

    background: #ffffff !important;

    color: #07478c !important;

    border: 1.5px solid #07478c !important;

    border-radius: 8px !important;

    font-weight: 600 !important;

    font-size: 14px !important;

    letter-spacing: .2px;

    min-height: 42px !important;

    margin-top: 22px !important;

    box-shadow: none !important;

    transition: background-color .15s ease, color .15s ease !important;

}

.st-key-logout button p { color: #07478c !important; transition: color .15s ease; }

.st-key-logout button:hover { background: #07478c !important; border-color: #07478c !important; }

.st-key-logout button:hover p { color: #ffffff !important; }

.st-key-logout button:focus-visible { outline: 2px solid #f59b36 !important; outline-offset: 2px; }

/* ------------------------------------------

   CHAT HEADING

   ------------------------------------------ */

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

/* ------------------------------------------

   CHAT AREA (iframe fills the space between heading and input)

   ------------------------------------------ */

.st-key-chat_area {
    min-height: 0 !important;
    overflow: hidden !important;
}

.st-key-chat_area iframe {
    display: block !important;
    width: 100% !important;
    height: calc(100dvh - 300px - var(--input-space)) !important;
    min-height: 150px !important;
    border: none !important;
}

/* ------------------------------------------

   CHAT INPUT (fixed to the bottom of the viewport)

   Left padding is set dynamically from Python

   based on whether the nav rail is expanded.

   ------------------------------------------ */

[data-testid="stBottom"] {

    position: fixed !important;

    bottom: 0 !important;

    left: 0 !important;

    right: 0 !important;

    z-index: 1000 !important;

    padding: 0 24px 0 112px !important;

    box-sizing: border-box !important;

    background: #07478c !important;

}

[data-testid="stBottom"] > div,

[data-testid="stBottomBlockContainer"] {

    background: #07478c !important;

}

[data-testid="stBottomBlockContainer"] {

    padding: 14px 0 !important;

    max-width: 100% !important;

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

/* ------------------------------------------

   RESPONSIVE

   ------------------------------------------ */

@media (max-width: 900px) {

    .brand-name { font-size: 17px; }

    .brand-sub { font-size: 11px; }

    .topbar { gap: 10px; padding: 0 12px; }

    .uta-logo { font-size: 30px; }

    .student-name { font-size: 12px; }

    .st-key-chat_area iframe,

    .st-key-chat_area [data-testid="stElementContainer"]:has(iframe),

    .st-key-chat_area [data-testid="stCustomComponentV1"]:has(iframe) {

        height: calc(100dvh - 320px - var(--input-space)) !important;

        max-height: calc(100dvh - 320px - var(--input-space)) !important;

    }

}

@media (max-width: 600px) {

    .st-key-chat_area iframe,

    .st-key-chat_area [data-testid="stElementContainer"]:has(iframe),

    .st-key-chat_area [data-testid="stCustomComponentV1"]:has(iframe) {

        height: calc(100dvh - 360px - var(--input-space)) !important;

        max-height: calc(100dvh - 360px - var(--input-space)) !important;

        min-height: 100px !important;

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

            "timestamp": timestamp_now(),

        }

    ]

if "messages" not in st.session_state:

    new_chat()

# ==========================================

# CHAT HELPERS

# ==========================================

def render_message_text(content):

    """Escape HTML, render bold, and avoid excessive blank lines."""

    content = escape(str(content))

    content = re.sub(r"\n[ \t]*\n+", "\n", content)
    content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content, flags=re.DOTALL)

    return content.replace("\n", "<br>")

def get_advisor_avatar():

    """Embed the UTA logo directly into the chat iframe."""

    if UTA_LOGO.exists():

        encoded = base64.b64encode(UTA_LOGO.read_bytes()).decode("utf-8")

        return '<img src="data:image/png;base64,' + encoded + '" alt="UTA Advisor" />'

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

# NAVIGATION RAIL + MAIN LAYOUT

# ==========================================

if "nav_expanded" not in st.session_state:

    st.session_state.nav_expanded = False  # start collapsed

expanded = st.session_state.nav_expanded

# Line the fixed chat input up with the main column in both nav states.

# Columns are 2.4/12 (20%) expanded or 0.65/12 (\~5.4%) collapsed.

nav_pct = 20 if expanded else 5.42

st.markdown(

    f"<style>[data-testid='stBottom'] {{ padding-left: calc({nav_pct}% + 12px) !important; }}</style>",

    unsafe_allow_html=True,

)

nav_col, main_col = st.columns(

    [2.4, 9.6] if expanded else [0.65, 11.35],

    gap="small",

    vertical_alignment="top",

)

with nav_col:

    with st.container(key="nav_rail"):

        if st.button(

            "◀  Collapse" if expanded else "☰",

            key="toggle_nav",

            help="Collapse sidebar" if expanded else "Expand sidebar",

            use_container_width=True,

        ):

            st.session_state.nav_expanded = not expanded

            st.rerun()

        if expanded:

            st.markdown("**🎓 Team 2 AI Advisor**")

        else:

            st.markdown(

                "<div style='text-align:center;font-size:23px'>🎓</div>",

                unsafe_allow_html=True,

            )

        if st.button(

            "💬  Chat Advisor" if expanded else "💬",

            key="chat_nav",

            type="primary",

            use_container_width=True,

            help="Chat Advisor",

        ):


            st.rerun()

        for label, icon in (

            ("Degree Planner", "🎓"),

            ("Course Search", "📖"),

            ("My Progress", "📊"),

            ("Schedule Check", "🗓️"),

            ("My Profile", "👤"),

        ):

            st.button(

                f"{icon}  {label}" if expanded else icon,

                key=f"nav_{label.lower().replace(' ', '_')}",

                disabled=True,

                use_container_width=True,

                help=f"{label} (coming soon)",

            )

        st.divider()

        if st.button(

            "✎  New Chat" if expanded else "✎",

            key="new_chat_nav",

            use_container_width=True,

            help="New Chat",

        ):

            new_chat()


            st.rerun()

        if expanded:

            st.caption("Signed in through Amazon Cognito.")

with main_col:

    # ==========================================

    # UTA HEADER

    # ==========================================

    with st.container(key="uta_header"):

        header_left, header_user, header_logout = st.columns([7, 1.45, 1.25], gap="small")

        with header_left:

            st.markdown(

                '<div class="topbar">'

                '<div class="uta-logo">UTA<span class="uta-star">★</span></div>'

                '<div>'

                '<div class="brand-name">Team 2 AI Advisor</div>'

                '<div class="brand-sub">Computer Science Academic Advisor</div>'

                '</div>'

                '</div>',

                unsafe_allow_html=True,

            )

        with header_user:

            st.markdown(

                '<div class="topbar" style="padding:0 5px;justify-content:center">'

                f'<div class="student-name">👤  {escape(str(student_display_name))}</div>'

                '</div>',

                unsafe_allow_html=True,

            )

        with header_logout:

            if st.button("Log out", key="logout", type="secondary", use_container_width=True):

                new_chat()

                sign_out()

    # ==========================================

    # MAIN CONTENT

    # ==========================================

    # Authenticated advisor interface
    if True:
        st.markdown(

            '<div class="headline">Chat with Your AI Advisor</div>'

            '<div class="subtitle">'

            'Ask questions about courses, prerequisites, schedules, or degree planning.'

            '</div>'

            '<div class="rule"></div>',

            unsafe_allow_html=True,

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

                                <div class="bubble user-bubble">{content}</div>

                                <div class="timestamp user-time">{timestamp}</div>

                            </div>

                            <div class="avatar user-avatar">👤</div>

                        </div>

                    """)

                else:

                    chat_items.append(f"""

                        <div class="message-row assistant-row">

                            <div class="avatar assistant-avatar">{advisor_avatar}</div>

                            <div class="message-group">

                                <div class="bubble assistant-bubble">{content}</div>

                                <div class="timestamp assistant-time">{timestamp}</div>

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

                    * {{ box-sizing: border-box; }}

                    html, body {{

                        margin: 0;

                        padding: 0;

                        height: 100%;

                        overflow: hidden;

                        font-family: Inter, Arial, sans-serif;

                        background: white;

                    }}

                    #chat-container {{

                        height: 100%;
                        min-height: 0;

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

                    .user-row {{ justify-content: flex-end; }}

                    .assistant-row {{ justify-content: flex-start; }}

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

                    .user-time {{ text-align: right; }}

                    .assistant-time {{ text-align: left; }}

                    @media (max-width: 700px) {{

                        .message-group {{ max-width: 80%; }}

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

                            const chat = document.getElementById("chat-container");

                            if (chat) {{

                                chat.scrollTop = chat.scrollHeight;

                            }}

                        }}

                        scrollToBottom();

                        window.addEventListener("load", scrollToBottom);

                        requestAnimationFrame(scrollToBottom);

                        setTimeout(scrollToBottom, 100);

                        setTimeout(scrollToBottom, 300);

                    </script>

                </body>

                </html>

                """,

                height=400,

                scrolling=False,

            )

        with st.container(key="chat_area"):

            render_chat()

# ==========================================

# CHAT INPUT

# Must be at the top level of the script (not inside a column/container)

# so Streamlit pins it to the bottom of the viewport.

# ==========================================

if auth:

    if prompt := st.chat_input("Type your message here...", disabled=False):

        reply_to(prompt)

        st.rerun()
