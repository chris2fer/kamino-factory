
import os
from time import sleep

import boto3
from botocore.exceptions import ClientError


MOCK_ACCOUNT_ID = os.getenv('mock_account_id')
REQUIRED_EMAIL_SUFFIX = 'hotmail.com' # Account email addresses must end with this.
MAX_ACCOUNT_NAME_LENGTH = 50            # 50 is AWS max length


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


def event_handler(event, context):

    if not validate_request(event=event):
        print("Request failed validation")

    print(event)

