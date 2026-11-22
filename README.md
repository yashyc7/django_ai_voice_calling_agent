# AI Voice Calling Agent

A Django project that makes an outbound phone call using **Twilio**, talks to the person using a **LangGraph** conversation flow, and saves the answers to an Excel file.

Right now the agent collects three details from the person on the call: **name**, **age** and **weight (kg)**.

## How it works

1. You open `/initiate_call/?to=<phone number>`. Django asks Twilio to call that number.
2. When the person picks up, Twilio sends a request to the `/voice/` webhook.
3. The webhook runs the LangGraph flow and reads the next message out loud (Amazon Polly voice `Polly.Joanna`).
4. Twilio listens to the person's speech (`en-IN`, speech recognition) and posts the text back to `/voice/`.
5. The graph moves to the next question. At the end, the answers are saved to `user_data.xlsx` and the call is hung up.

### Conversation flow (`ai_voice_calling/graph.py`)

```
start -> ask_name -> ask_age -> ask_weight -> save_data -> END
```

- The state (`name`, `age`, `weight`, `current_step`, `user_input`, `messages`) is kept per call using the Twilio `CallSid` as the LangGraph `thread_id`.
- `MemorySaver` is the checkpointer, and the graph pauses (`interrupt_before`) before every question node so it can wait for the caller's reply.
- If the caller says nothing, the same question is asked again.

> Note: this version is a scripted question flow. It does not call an LLM yet, so the flow is easy to extend with LLM nodes later.

## Project structure

```
core/                    Django project settings, urls, asgi/wsgi
ai_voice_calling/
  graph.py               LangGraph conversation flow
  views.py               voice_webhook (TwiML) and initiate_call
  utils.py               save_to_excel() using openpyxl
user_data.xlsx           Saved answers (Name, Age, Weight)
requirements.txt
```

## Endpoints

| URL | What it does |
|-----|--------------|
| `/voice/` | Twilio webhook. Returns TwiML (say, gather speech, hang up) |
| `/initiate_call/?to=+91XXXXXXXXXX` | Starts an outbound call to the given number |

## Setup

### Requirements

- Python 3.10+
- A [Twilio](https://www.twilio.com/) account with a voice-enabled phone number
- [ngrok](https://ngrok.com/) (or any public HTTPS URL) so Twilio can reach your local server

### Steps

1. Clone and install:
   ```bash
   git clone https://github.com/yashyc7/django_ai_voice_calling_agent.git
   cd django_ai_voice_calling_agent
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root:
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
   ```
3. Start ngrok and copy the HTTPS URL:
   ```bash
   ngrok http 8000
   ```
4. Open `ai_voice_calling/views.py` and set `NGROK_URL` to your ngrok URL. It is hardcoded right now, so this step is required every time the ngrok URL changes.
5. Run migrations and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
6. Trigger a call:
   ```
   http://localhost:8000/initiate_call/?to=+91XXXXXXXXXX
   ```
   If you do not pass `to`, a default number written in `views.py` is used. Change it to your own number.

If your Twilio account is a trial account, you can only call numbers you have verified in the Twilio console.

## Tech stack

Python, Django, LangGraph, LangChain, Twilio Programmable Voice, openpyxl, python-dotenv

## Known limitations / ideas for next steps

- `NGROK_URL` and the default phone number are hardcoded in `views.py`. Move them to `.env`.
- `MemorySaver` keeps state in memory only, so state is lost when the server restarts. Use a persistent checkpointer for production.
- No validation on age and weight (any speech text is accepted).
- `initiate_call` and `voice_webhook` have no authentication or Twilio signature check, and `DEBUG = True` with `ALLOWED_HOSTS = ['*']` is for development only.
- Add LLM-powered nodes (for example lead qualification) on top of the current flow.
