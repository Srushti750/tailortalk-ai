import datetime
import pickle
from typing import TypedDict, Annotated, Literal, Optional
import dateparser
import requests
import re

from langgraph.graph import StateGraph
from pydantic import BaseModel
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import streamlit as st
import json
from datetime import timedelta

# ---- Auth Constants ----
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PICKLE = "token.pickle"

# ---- Load credentials from Streamlit secrets ----
def get_credentials():
    creds = None
    credentials_raw = st.secrets["GOOGLE_CREDENTIALS"]
    credentials_dict = json.loads(credentials_raw)
    flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PICKLE, "wb") as token:
        pickle.dump(creds, token)

    return creds

# ---- Core Logic to Check Availability ----
def check_calendar_availability():
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + "Z"
    end = (datetime.datetime.utcnow() + datetime.timedelta(days=2)).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    busy_times = [event["start"].get("dateTime", event["start"].get("date")) for event in events]
    return busy_times

# ---- Core Logic to Book Meeting ----
def book_meeting(start_time_iso, end_time_iso, summary="Meeting with TailorTalk"):
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": summary,
        "start": {"dateTime": start_time_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time_iso, "timeZone": "Asia/Kolkata"},
    }

    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return created_event.get("htmlLink")

# ---- LangGraph State ----
class AgentState(BaseModel):
    user_input: str
    intent: Optional[Literal["check", "book"]] = None
    response: Optional[str] = None

class AgentStateGraph(TypedDict):
    state: AgentState

# ---- Intent Parsing ----
def parse_intent(data: AgentStateGraph) -> AgentStateGraph:
    state = data["state"]
    user_input = state.user_input.lower()
    if "book" in user_input or "schedule" in user_input:
        state.intent = "book"
    elif "free" in user_input or "available" in user_input or "meeting" in user_input:
        state.intent = "check"
    else:
        state.intent = None
        state.response = "❌ I couldn't understand your intent. Try asking about availability or booking."
    return {"state": state}

# ---- Utility: Extract time phrase from sentence ----
def extract_datetime_phrase(text):
    pattern = r"(tomorrow.*?\d{1,2}(:\d{2})?\s?(AM|PM)?)|(today.*?\d{1,2}(:\d{2})?\s?(AM|PM)?)|(on\s.*?\d{1,2}(:\d{2})?\s?(AM|PM)?)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group() if match else text

# ---- Check Logic ----
def check_availability(state: AgentState) -> AgentState:
    try:
        busy_slots = check_calendar_availability()
        state.response = "❌ You are busy at:\n" + "\n".join(f"• {slot}" for slot in busy_slots) if busy_slots else "✅ You are free! No meetings scheduled."
    except Exception as e:
        state.response = f"❌ Failed to fetch calendar: {str(e)}"
    return state  # Return the modified state object

# ---- Book Logic ----
def book_slot(state: AgentState) -> AgentState:
    try:
        time_phrase = extract_datetime_phrase(state.user_input)
        parsed_datetime = dateparser.parse(
            time_phrase,
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.datetime.now()}
        )

        if not parsed_datetime:
            state.response = "❌ I couldn't understand the date/time. Please say something like 'Book tomorrow at 3 PM'"
            return state

        start_time = parsed_datetime.isoformat()
        end_time = (parsed_datetime + timedelta(minutes=30)).isoformat()
        link = book_meeting(start_time, end_time)

        state.response = f"✅ Meeting booked for {parsed_datetime.strftime('%A at %I:%M %p')}!\n🔗 Link: {link}"
    except Exception as e:
        state.response = f"❌ Booking error: {str(e)}"
    return state

# ---- Fallback ----
def handle_unknown(state: AgentState) -> AgentState:
    state.response = "❌ Sorry, I couldn't process that. Try asking about meetings or bookings."
    return state

# ---- Graph Setup ----
builder = StateGraph(AgentStateGraph)
builder.add_node("intent", parse_intent)
builder.set_entry_point("intent")

builder.add_conditional_edges(
    "intent",
    lambda x: x["state"].intent,
    {
        "check": "check",
        "book": "book",
        None: "fallback"
    },
)

builder.add_node("check", check_availability)
builder.add_node("book", book_slot)
builder.add_node("fallback", handle_unknown)
builder.add_edge("check", "fallback")
builder.add_edge("book", "fallback")

graph = builder.compile()
runnable_graph = graph
