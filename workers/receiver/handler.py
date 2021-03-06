
import os
import json
import uuid
from base64 import b64decode

import boto3
from botocore.exceptions import ClientError

FACTORY_EVENT_BUS = os.getenv('FACTORY_BUS')
FACTORY_EVENT_SOURCE = f"{os.getenv('FACTORY_EVENT_SOURCE', 'factory')}.requests"


def send_event(event):
    client = boto3.Session().client('events')

    items=[
        {
            'Detail': json.dumps(event),
            'DetailType': 'factoryNewAccountRequest',
            'Resources': [],
            'Source': f"{FACTORY_EVENT_SOURCE}.newAccountRequest",
            'EventBusName': FACTORY_EVENT_BUS
        }
    ]
    try:
        print(f"Sending to: {items[0]['EventBusName']}")
        print(f"Sending event as source: {items[0]['Source']}")
        client.put_events(Entries=items)
    except ClientError as e:
        print("Couldn't send event")
        print(e)

def process_event(event: str) -> dict:
    data = json.loads(event)
    
    if 'GUID' not in data.keys():
        data['GUID'] = str(uuid.uuid4())

    send_event(data)
    return data


def receiver(event, context):
    
    factory_event = b64decode(event['body']).decode('utf-8')
    res = process_event(factory_event)

    print(res)

    body = {
        "message": "Your factory request has been received successfully!",
        "GUID": res['GUID']
    }
    print(body)
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response