import datetime
import requests
from langgraph.graph import StateGraph
from pydantic import BaseModel
import dateparser
from datetime import datetime, timedelta
import re

# ✅ Define conversational agent state
class AgentState(BaseModel):
    user_input: str = ""
    intent: str = ""
    response: str = ""

# ✅ Node 1: Parse user input to determine intent
def parse_intent(state: AgentState) -> AgentState:
    text = state.user_input.lower()

    if "book" in text or "schedule" in text:
        state.intent = "book"
    elif "free" in text or "available" in text or "meeting" in text:
        state.intent = "check"
    else:
        state.intent = "unknown"

    return state

# ✅ Node 2: Check availability by hitting the FastAPI backend
def check_calendar(state: AgentState) -> AgentState:
    try:
        print("📞 Calling /availability...")
        res = requests.get("http://localhost:8000/availability")
        if res.status_code == 200:
            busy_slots = res.json().get("busy_slots", [])
            if busy_slots:
                state.response = f"Here are your busy slots:\n{busy_slots}"
            else:
                state.response = "You're fully available in the next 2 days!"
        else:
            state.response = f"Error: Received status code {res.status_code}"
    except Exception as e:
        state.response = f"❌ Failed to fetch calendar: {str(e)}"
    return state

# ✅ Node 3: Book a meeting using FastAPI backend
# def book_slot(state: AgentState) -> AgentState:
#     try:
#         print("📞 Calling /book...")
#         res = requests.post("http://localhost:8000/book")
#         data_json = res.json()

#         # ✅ Check for eventLink or error
#         if "eventLink" in data_json:
#             state.response = f"✅ Meeting booked! Link: {data_json['eventLink']}"
#         elif "error" in data_json:
#             state.response = f"❌ Booking failed: {data_json['error']}"
#         else:
#             state.response = f"❌ Unexpected response: {data_json}"
#     except Exception as e:
#         state.response = f"❌ Failed to book meeting: {str(e)}"
#     return state

def extract_datetime_phrase(text):
    pattern = r"(tomorrow.*?\d{1,2}(:\d{2})?\s?(AM|PM)?)|(today.*?\d{1,2}(:\d{2})?\s?(AM|PM)?)|(on\s.*?\d{1,2}(:\d{2})?\s?(AM|PM)?)"

    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        return match.group()
    return text  # fallback to full text

def book_slot(state: AgentState) -> AgentState:
    try:
        print("📞 Calling /book...")
        print("🧠 User said:", state.user_input)

        time_phrase = extract_datetime_phrase(state.user_input)
        print("🕒 Extracted time phrase:", time_phrase)
        
        # Extract datetime from input
        parsed_datetime = dateparser.parse(
            time_phrase,
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()}
        )
        print("📅 Parsed datetime:", parsed_datetime)

        if not parsed_datetime:
            state.response = (
                "❌ I couldn't understand the date/time.\n"
                "Try rephrasing like 'Book a meeting tomorrow at 3 PM'."
            )
            return state

        # Create 30-minute meeting
        start_time = parsed_datetime.isoformat()
        end_time = (parsed_datetime + timedelta(minutes=30)).isoformat()

        payload = {
            "summary": "Meeting with TailorTalk",
            "start": start_time,
            "end": end_time
        }

        print("📤 Sending payload:", payload)
        res = requests.post("http://localhost:8000/book", json=payload)
        data_json = res.json()

        if "eventLink" in data_json:
            state.response = (
                f"✅ Meeting booked for {parsed_datetime.strftime('%A at %I:%M %p')}!\n"
                f"🔗 Link: {data_json['eventLink']}"
            )
        else:
            state.response = f"⚠️ Failed to book: {data_json.get('error', 'Unknown error')}"

    except Exception as e:
        state.response = f"❌ Booking error: {str(e)}"

    return state


# ✅ Node 4: Handle unknown messages
def unknown(state: AgentState) -> AgentState:
    state.response = (
        "Sorry, I didn't understand that. "
        "Try something like 'check my availability' or 'book a meeting'."
    )
    return state

# ✅ Build LangGraph state machine
graph = StateGraph(AgentState)

# Add processing nodes
graph.add_node("parse_intent", parse_intent)
graph.add_node("check_calendar", check_calendar)
graph.add_node("book_slot", book_slot)
graph.add_node("unknown", unknown)

# Set entry point
graph.set_entry_point("parse_intent")

# Route to next step based on intent
def route_intent(state: AgentState):
    if state.intent == "check":
        return "check_calendar"
    elif state.intent == "book":
        return "book_slot"
    else:
        return "unknown"

graph.add_conditional_edges("parse_intent", route_intent)

# Define finish points
graph.set_finish_point("check_calendar")
graph.set_finish_point("book_slot")
graph.set_finish_point("unknown")

# Compile the graph
runnable_graph = graph.compile()
