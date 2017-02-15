# -*- coding: utf-8 -*-

import logging
import requests
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

device = {
            "applianceId": "",
            "manufacturerName": "Ansi",
            "modelName": "Ansi",
            "version": "1",
            "friendlyName": "",
            "friendlyDescription": "",
            "isReachable": True,
            "actions": [],
            "additionalApplianceDetails": {
                "extraDetail1": "This device is brought to you by HAL"
            }
         }

def requestDevices():
    with open('passwd.txt', 'r') as myfile:
        passwd = myfile.read().replace('\n', '')
        url    = "http://a0bb8378.ngrok.io/api/v1.0/discovery"
        data   = {"pass": passwd}
        try:
            return json.loads(requests.post(url, data).content)
        except Exception as e:
            print e

def sendAction(event):
    with open('passwd.txt', 'r') as myfile:
        passwd = myfile.read().replace('\n', '')
        url    = "http://a0bb8378.ngrok.io/api/v1.0/action"
        data   = {"pass": passwd, "event": json.dumps(event)}
        print "XXXXXXXXXXXXXXXXXXXXXX"
        print json.dumps(data)
        print "XXXXXXXXXXXXXXXXXXXXXX"
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

        devices = []

        for d in requestDevices():
            a = device.copy()
            a['applianceId'] = d['id']
            a['friendlyName'] = d['name']
            a['friendlyDescription'] = d['description']
            a['actions'] = d['actions']
            devices.append(a)

        payload = {
            "discoveredAppliances": devices
        }

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

    sendAction(event)

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