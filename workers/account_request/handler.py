
import os
from time import sleep
import json

import boto3
from botocore.exceptions import ClientError


MOCK_ACCOUNT_ID = os.getenv('mock_account_id')
REQUIRED_EMAIL_SUFFIX = 'hotmail.com' # Account email addresses must end with this.
MAX_ACCOUNT_NAME_LENGTH = 50            # 50 is AWS max length
FACTORY_EVENT_BUS = os.getenv('FACTORY_BUS')
FACTORY_EVENT_SOURCE = f"{os.getenv('FACTORY_EVENT_SOURCE', 'factory')}.accounts"

def validate_email(email: str, force=False) -> bool:
    if '@' in email:
        user,domain = email.split('@')
        if domain.lower().endswith(REQUIRED_EMAIL_SUFFIX) or force :
            print('Email is valid')
            return True
    print('Email is not valid')
    return False


def validate_name(name: str, force=False) -> bool:
    if isinstance(name, str):
        if len(name) <= MAX_ACCOUNT_NAME_LENGTH:
            return True
        else:
            print('Account Name exceeds the Max Length')
    return False


def validate_request(event: dict) -> bool:
    
    if event['detail-type'] != 'factoryNewAccountRequest':
        return False

    if not isinstance(event['detail'], dict):
        print("Factory Request is not dict object")
        raise Exception

    request_keys = event['detail'].keys()
    if not set(['email', 'alias', 'region', 'environment']).issubset(set(request_keys)):
        print("Factory request is incomplete.")
        raise Exception

    if not validate_email(event['detail']['email']):
        print("Email request is not valid")
        raise Exception

    return True

def send_event(event):
    client = boto3.Session().client('events')

    items=[
        {
            'Detail': json.dumps(event),
            'DetailType': 'factoryAccountCreated',
            'Resources': [],
            'Source': f"{FACTORY_EVENT_SOURCE}.accountCreated",
            'EventBusName': FACTORY_EVENT_BUS
        }
    ]
    try:
        print(f"Sending to: {items[0]['EventBusName']}")
        print(f"Sending event as source: {items[0]['Source']}")
        client.put_events(Entries=items)
    except ClientError as e:
        print(e)

def event_handler(event, context):

    if not validate_request(event=event):
        print("Request failed validation")
        return event
    
    print("  WOULD RUN BOTO CLIENT TO CREATE ACCOUNT")
    send_event(event)
    return event

