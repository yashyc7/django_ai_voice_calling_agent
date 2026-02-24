from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.voice_response import VoiceResponse, Gather
from ai_voice_calling.graph import app as graph_app
from twilio.rest import Client
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

NGROK_URL = "https://58c2-2409-4090-a02d-1d-a4b5-77a7-a43b-9f5f.ngrok-free.app"

def get_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}

def get_last_message(result: dict) -> str:
    messages = result.get("messages", [])
    if messages:
        return messages[-1].content
    return "Hello!"

@csrf_exempt
def voice_webhook(request):
    try:
        session_id = request.POST.get('CallSid', 'default')
        user_input = request.POST.get('SpeechResult', '').strip()
        config = get_config(session_id)

        logger.info(f"Session: {session_id}, Input: '{user_input}'")

        state_snapshot = graph_app.get_state(config)
        is_first_call = (state_snapshot.values == {}) if state_snapshot else True

        response = VoiceResponse()

        if is_first_call:
            # ── First call: initialize and run until first interrupt ──
            result = graph_app.invoke(
                {
                    "name": "",
                    "age": "",
                    "weight": "",
                    "current_step": "start",
                    "user_input": "",
                    "messages": [],
                },
                config=config
            )
        else:
            # ── Subsequent calls: inject user input, then resume ──
            current_values = dict(state_snapshot.values)
            current_values["user_input"] = user_input

            graph_app.update_state(config, current_values)
            result = graph_app.invoke(None, config=config)

        current_step = result.get("current_step", "")
        message_text = get_last_message(result)

        logger.info(f"Step: {current_step}, Message: '{message_text}'")

        response.say(message_text, voice="Polly.Joanna")  # nicer voice

        if current_step != "__end__":
            gather = Gather(
                input='speech',
                action=f'{NGROK_URL}/voice/',
                method='POST',
                speech_timeout=3,
                speechModel='phone_call',
                language='en-IN'
            )
            response.append(gather)
            # Fallback if user says nothing
            response.redirect(f'{NGROK_URL}/voice/', method='POST')
        else:
            response.hangup()

        return HttpResponse(str(response), content_type='text/xml')

    except Exception as e:
        logger.exception(f"Error in voice_webhook: {e}")
        # Return a valid TwiML even on error so Twilio doesn't say "application error"
        response = VoiceResponse()
        response.say("We encountered a technical issue. Please try again later.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')


def initiate_call(request):
    to_phone = request.GET.get('to', '+917597197668')
    from_phone = os.getenv('TWILIO_PHONE_NUMBER', '')
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    call = client.calls.create(
        to=to_phone,
        from_=from_phone,
        url=f'{NGROK_URL}/voice/',
        method='POST'
    )
    return JsonResponse({'call_sid': call.sid})