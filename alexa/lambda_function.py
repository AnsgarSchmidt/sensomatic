# -*- coding: utf-8 -*-

import logging
import requests
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def requestDevices():
    with open('passwd.txt', 'r') as myfile:
        passwd = myfile.read().replace('\n', '')
        url    = "https://6e0e0e97.ngrok.io/api/v1.0/discovery"
        data   = {"pass": passwd}
        try:
            return json.loads(requests.post(url, data).content)
        except Exception as e:
            print e

def sendAction(data):
    with open('passwd.txt', 'r') as myfile:
        passwd = myfile.read().replace('\n', '')
        url    = "https://6e0e0e97.ngrok.io/api/v1.0/action"
        data   = {"pass": passwd, "data": data}
        try:
            return json.loads(requests.post(url, data).content)
        except Exception as e:
            print e

def lambda_handler(event, context):
    logger.info('Logged Event:{}'.format(event))
    access_token = event['payload']['accessToken']

    logger.info('Request Header:{}'.format(event['header']))
    logger.info('Request Payload:{}'.format(event['payload']))

    if event['header']['namespace'] == 'Alexa.ConnectedHome.Discovery':
        return handleDiscovery(context, event)

    elif event['header']['namespace'] == 'Alexa.ConnectedHome.Control':
        return handleControl(context, event)

def handleDiscovery(context, event):
    payload = ''
    header = {
        "messageId": "GUIDGUIDGUIDGUID",
        "namespace": "Alexa.ConnectedHome.Discovery",
        "name": "DiscoverAppliancesResponse",
        "payloadVersion": "2"
    }

    if event['header']['name'] == 'DiscoverAppliancesRequest':
        payload = {
            "discoveredAppliances": [
                {
                    "applianceId": "sample-7",
                    "manufacturerName": "WORKORAMA",
                    "modelName": "WORKORAMA",
                    "version": "1",
                    "friendlyName": "WORKORAMA",
                    "friendlyDescription": "Thermostat by WORKORAMA",
                    "isReachable": True,
                    "actions": [
                        "setTargetTemperature",
                        "incrementTargetTemperature",
                        "decrementTargetTemperature"
                    ],
                    "additionalApplianceDetails": {
                        "extraDetail1": "This is a thermostat that is reachable"
                    }
                },
                {
                    "applianceId": "sample-2",
                    "manufacturerName": "Sample Manufacturer",
                    "modelName": "Sample Dimmer",
                    "version": "1",
                    "friendlyName": "Sample Dimmer",
                    "friendlyDescription": "Dimmer by Sample Manufacturer",
                    "isReachable": True,
                    "actions": [
                        "turnOn",
                        "turnOff",
                        "setPercentage",
                        "incrementPercentage",
                        "decrementPercentage"
                    ],
                    "additionalApplianceDetails": {
                        "extraDetail1": "This is a dimmer that is reachable"
                    }
                },
                {
                    "applianceId": "sample-3",
                    "manufacturerName": "Sample Manufacturer",
                    "modelName": "Sample Switch",
                    "version": "1",
                    "friendlyName": "Sample Switch",
                    "friendlyDescription": "Switch by Sample Manufacturer",
                    "isReachable": True,
                    "actions": [
                        "turnOn",
                        "turnOff"
                    ],
                    "additionalApplianceDetails": {
                        "extraDetail1": "This is a switch that is reachable"
                    }
                },
                {
                    "applianceId": "sample-4",
                    "manufacturerName": "Sample Manufacturer",
                    "modelName": "Sample Fan",
                    "version": "1",
                    "friendlyName": "Sample Fan",
                    "friendlyDescription": "Fan by Sample Manufacturer",
                    "isReachable": True,
                    "actions": [
                        "turnOn",
                        "turnOff",
                        "setPercentage",
                        "incrementPercentage",
                        "decrementPercentage"
                    ],
                    "additionalApplianceDetails": {
                        "extraDetail1": "This is a fan that is reachable"
                    }
                },
                {
                    "applianceId": "sample-5",
                    "manufacturerName": "Sample Manufacturer",
                    "modelName": "Sample Switch",
                    "version": "1",
                    "friendlyName": "Sample Switch Unreachable",
                    "friendlyDescription": "Switch by Sample Manufacturer",
                    "isReachable": False,
                    "actions": [
                        "turnOn",
                        "turnOff",
                    ],
                    "additionalApplianceDetails": {
                        "extraDetail1": "This is a switch that is not reachable and should show as offline in the Alexa app"
                    }
                }
            ]
        }

    payload = requestDevices()

    logger.info('Response Header:{}'.format(header))
    logger.info('Response Payload:{}'.format(payload))

    return {
        "header": header,
        "payload": payload
    }


def handleControl(context, event):
    payload = {}
    appliance_id = event['payload']['appliance']['applianceId']
    message_id   = event['header']['messageId']
    request_name = event['header']['name']

    response_name = ''
    if request_name == 'TurnOnRequest': response_name = 'TurnOnConfirmation'
    if request_name == 'TurnOffRequest': response_name = 'TurnOffConfirmation'
    if request_name == 'SetTargetTemperatureRequest':
        response_name = 'SetTargetTemperatureConfirmation'
        target_temperature = event['payload']['targetTemperature']['value']
        payload = {
            "targetTemperature": {
                "value": target_temperature
            },
            "temperatureMode": {
                "value": "AUTO"
            },
            "previousState": {
                "targetTemperature": {
                    "value": 21.0
                },
                "mode": {
                    "value": "AUTO"
                }
            }
        }
    if request_name == 'IncrementTargetTemperatureRequest':
        response_name = 'IncrementTargetTemperatureConfirmation'
        delta_temperature = event['payload']['deltaTemperature']['value']
        payload = {
            "previousState": {
                "mode": {
                    "value": "AUTO"
                },
                "targetTemperature": {
                    "value": 21.0
                }
            },
            "targetTemperature": {
                "value": 21.0 + delta_temperature
            },
            "temperatureMode": {
                "value": "AUTO"
            }
        }
    if request_name == 'DecrementTargetTemperatureRequest':
        response_name = 'DecrementTargetTemperatureConfirmation'
        delta_temperature = event['payload']['deltaTemperature']['value']
        payload = {
            "previousState": {
                "mode": {
                    "value": "AUTO"
                },
                "targetTemperature": {
                    "value": 21.0
                }
            },
            "targetTemperature": {
                "value": 21.0 - delta_temperature
            },
            "temperatureMode": {
                "value": "AUTO"
            }
        }
    if request_name == 'SetPercentageRequest': response_name = 'SetPercentageConfirmation'
    if request_name == 'IncrementPercentageRequest': response_name = 'IncrementPercentageConfirmation'
    if request_name == 'DecrementPercentageRequest': response_name = 'DecrementPercentageConfirmation'

    if appliance_id == 'sample-5':
        response_name = 'TargetOfflineError'
        payload = {}

    header = {
        "namespace": "Alexa.ConnectedHome.Control",
        "name": response_name,
        "payloadVersion": "2",
        "messageId": message_id
    }

    logger.info('Response Header:{}'.format(header))
    logger.info('Response Payload:{}'.format(payload))

    return {
        "header": header,
        "payload": payload
    }