

import os
import logging
import json
import re
import datetime
from time import sleep

import boto3
from botocore.exceptions import ClientError

from aws_helpers import find_account_by_email
from common_helpers import save_pipeline_state
from common_helpers import jenkins_logger as log 


DRY_RUN = os.getenv('ci_env', 'dev').lower() != 'prod'
MOCK_ACCOUNT_ID = os.getenv('mock_account_id')
REQUIRED_EMAIL_SUFFIX = 'bloomberg.com' # Account email addresses must end with this.
MAX_ACCOUNT_NAME_LENGTH = 50            # 50 is AWS max length

organizations = boto3.Session().client('organizations')

#####  ORIGINAL FUNCTIONS #######
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


def request_account_create(name: str, email: str, force=False, dryrun=DRY_RUN) -> dict:
    # We do not want to actually create an AWS account unless this is a real run
    if DRY_RUN:
        print("DRY RUN IS SET")
        return {
            'CreateAccountStatus': {
                'Id': MOCK_ACCOUNT_ID,
                'State': 'SUCCEEDED'
            }
        }
    if validate_email(email, force) and validate_name(name, force):
        try:
            resp = organizations.create_account(
                Email=email,
                AccountName=name,
            )
            return resp
        except Exception:
            print(Exception.message)
            pass

    else:
        print("Invalid Arguments")
        exit(1)


def wait_for_account_creation(operation_id: str, email: str) -> dict:
    print('Waiting for Account Creation Request to complete')
    if DRY_RUN:
        return {'State': 'SUCCEEDED', 'AccountName': 'DRY_RUN_TEST', 'AccountId': '999999999999'}

    sleep(5)
    resp = organizations.describe_create_account_status(CreateAccountRequestId=operation_id)

    if resp.get('CreateAccountStatus'):
        status = resp.get('CreateAccountStatus')
        state = status['State']
        if state == 'IN_PROGRESS':
            print('{"status": "Waiting"}')
            resp = wait_for_account_creation(resp['CreateAccountStatus']['Id'])
        elif state == 'SUCCEEDED':
            print('Wait complete. Account Created')
            return resp['CreateAccountStatus']
        elif state == 'FAILED':
            print(f'{{"status": "FAILED", "reason": "{status["FailureReason"]}"}}')
            return resp['CreateAccountStatus']
    return resp
### END ORIGINAL FUNCTIONS #######

def validate_request(event: dict) -> bool:
    
    if event['detail-type'] != 'factoryNewAccountRequest':
        return False

    if set(['email', 'alias', 'region', ''])

def event_handler(event, context):


    print(event)


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", "-n", help="Basic Name for the new account")
    parser.add_argument("--alias", "-a", help="AWS Account alias")
    parser.add_argument("--email", "-e", help="Email address for the account")
    parser.add_argument("--jira", "-j", help="Jira story id", default='Not Provided')
    parser.add_argument("--force", "-f", help="Override validations", default='No')
    args = parser.parse_args()

    FORCE = args.force == 'Yes'

    create_result = request_account_create(email=args.email, name=args.name, force=args.force)

    wait_result = wait_for_account_creation(operation_id=create_result['CreateAccountStatus']['Id'], email=args.email)
    
    if wait_result['State'] == 'FAILED' and wait_result['FailureReason'] == 'EMAIL_ALREADY_EXISTS' and FORCE:

        print(f"Existing account Found for Email {args.email} and force overide is present")
        account = find_account_by_email(org=organizations, email=args.email)

        # Make sure email address and account name match for an existing account
        if account['Name'] != args.name:
            print(f"Existing account with email {args.email} does not match the name provided")
            print(f"Existing account name is \'{account['Name']}\' and provided is \'{args.name}\' ")
            print(f"Existing account number is {account['Id']}")
            wait_result['State'] = 'FAILED'
        else:
            wait_result['State'] = 'SUCCEEDED'
            wait_result['AccountId'] = account['Id']

    if not wait_result.get('AccountId'):
        wait_result['AccountId'] = 'Create_Failed'
        exit(1)

    account_id = wait_result['AccountId']
    print('##-----------------')
    print('## New Account Info  ')
    print(f'##  Account ID: {account_id}')
    try:
        save_pipeline_state(
            {
                "accountId": account_id,
                "accountAlias": args.alias,
                "accountName": args.name,
                "accountEmail": args.email,
                "jiraId": args.jira,
                "dryrun": str(DRY_RUN),
            }
        )
    except Exception as e:
        print(e.message)
        print("Could not record state")
