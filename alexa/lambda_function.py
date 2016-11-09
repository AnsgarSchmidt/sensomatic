from __future__ import print_function
import requests
import socket
import json
import urllib2

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def get_welcome_response():
    session_attributes = {}
    card_title         = "Welcome"
    speech_output      = """
                         Willkommen auf der <say-as interpret-as=\"spell-out\">USS</say-as> Horizon.
                         Ich kann zum Beispiel das Licht im wohnzimmer, kueche, esstisch, flur, ansiraum, tiffyraum, badezimmer
                         an und ausschalten."""
    reprompt_text      = "Ja genau. Herzlich willkommen auf der <say-as interpret-as=\"spell-out\">USS</say-as> Horizon"
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title         = "Session Ended"
    speech_output      = "Schoenen Weiterflug"
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def on_session_started(session_started_request, session):
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    return get_welcome_response()

def handle_light(intent, session):

    session_attributes = {}
    reprompt_text      = None

    print(intent)
    print(session)

    if intent.get('slots', {}) and "room" in intent.get('slots', {}):
        room               = intent['slots']['room']['value']
        state              = intent['slots']['state']['value']
        speech_output      = "Du hast den Raum " + room + " ausgesucht. Ich schalte das Licht dort."
        should_end_session = True

        passwd = ""
        with open('passwd.txt', 'r') as myfile:
            passwd = myfile.read().replace('\n', '')
        command   = "light"
        url       = "http://aws.23-5.eu:2342/api/v1.0/command"
        data      = {"command" : command, "value" : state, "room": room, "pass": passwd}
        print(requests.post(url, data).content)

    else:
        speech_output      = "Es wurde kein Raum ausgesucht."
        should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def on_intent(intent_request, session):

    print("on_intent requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])

    intent      = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "light":
        return handle_light(intent, session)
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] + ", sessionId=" + session['sessionId'])

def lambda_handler(event, context):
    print("event.session.application.applicationId=" + event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']}, event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
