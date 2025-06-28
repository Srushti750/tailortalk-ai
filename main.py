from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import datetime
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from fastapi.responses import JSONResponse
from fastapi import Request
import streamlit as st
import json
from google_auth_oauthlib.flow import InstalledAppFlow

app = FastAPI()

# Scopes define the level of access
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Save the token after first login
TOKEN_PICKLE = "token.pickle"

# Load credentials
def get_credentials():
    creds = None
    # 🔁 Load credentials from secrets instead of a file
    credentials_raw = st.secrets["GOOGLE_CREDENTIALS"]
    credentials_dict = json.loads(credentials_raw)
    flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PICKLE, "wb") as token:
        pickle.dump(creds, token)
    return creds

@app.get("/")
def root():
    return {"message": "TailorTalk Calendar API is running!"}

# 1️⃣ CHECK AVAILABILITY
@app.get("/availability")
def check_availability():
    try:
        print("📞 /availability called")
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.datetime.utcnow().isoformat() + "Z"
        end = (datetime.datetime.utcnow() + datetime.timedelta(days=2)).isoformat() + "Z"
        print(f"⏰ Time range: {now} - {end}")

        events_result = service.events().list(
            calendarId="primary", timeMin=now, timeMax=end,
            singleEvents=True, orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        busy_times = [event["start"].get("dateTime", event["start"].get("date")) for event in events]

        print("✅ Busy slots:", busy_times)
        return {"busy_slots": busy_times}
    except Exception as e:
        print("❌ Error:", e)
        return {"error": str(e)}


# 2️⃣ BOOK A MEETING
# @app.post("/book")
# def book_meeting():
#     try:
#         print("📞 /book called")
#         creds = get_credentials()
#         service = build("calendar", "v3", credentials=creds)

#         event = {
#             "summary": "Meeting with TailorTalk",
#             "start": {"dateTime": "2025-06-27T10:00:00+05:30", "timeZone": "Asia/Kolkata"},
#             "end": {"dateTime": "2025-06-27T10:30:00+05:30", "timeZone": "Asia/Kolkata"},
#         }

#         created_event = service.events().insert(calendarId="primary", body=event).execute()
#         return {"status": "booked", "eventLink": created_event.get("htmlLink")}

#     except Exception as e:
#         print("❌ Error in /book:", str(e))
#         return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/book")
async def book_meeting(req: Request):
    try:
        body = await req.json()
        summary = body.get("summary", "Meeting with TailorTalk")
        start_time = body.get("start")
        end_time = body.get("end")

        print("📞 /book with start:", start_time, "end:", end_time)

        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
        }

        event = service.events().insert(calendarId="primary", body=event).execute()
        return {"status": "booked", "eventLink": event.get("htmlLink")}

    except Exception as e:
        print("❌ Error in /book:", str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)