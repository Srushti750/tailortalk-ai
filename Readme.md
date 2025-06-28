# TailorTalk AI – Calendar Assistant

TailorTalk is a conversational AI assistant that helps users check Google Calendar availability and book meetings naturally.

## Features

- Natural language interface (LangGraph)
- Real-time availability via Google Calendar API
- Seamless meeting booking via FastAPI
- Friendly chat UI with Streamlit

## Tech Stack

- FastAPI (backend API)
- LangGraph + Pydantic (agent logic)
- Streamlit (UI)
- Google Calendar API (integration)

## Setup Instructions

1. **Clone the repo and navigate to the folder**
2. **Create a virtual environment**

- python -m venv myenv
- myenv\Scripts\activate # Windows

- source myenv/bin/activate # macOS/Linux

3. **Install dependencies**

- pip install -r requirements.txt

4. **Google Calendar Setup**
- Enable Google Calendar API on [Google Cloud Console](https://console.cloud.google.com/)
- Download `credentials.json` and place it in the root folder
- On first run, it will open a browser to authenticate and create `token.pickle`

5. **Run FastAPI backend**

- uvicorn main:app --reload

6. **Run Streamlit UI**

- streamlit run ui_streamlit.py

7. **Chat Examples**
- "Do I have any meetings tomorrow?"
- "Book a meeting at 3 PM"
- "Am I free today afternoon?"

---

## Note
- Do not share `credentials.json` publicly.
- `token.pickle` can be deleted to reset auth.

## Author
Srushti Kulkarni  