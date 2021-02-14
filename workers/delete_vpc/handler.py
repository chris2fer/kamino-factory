#!/usr/bin/env python

"""
Author: Christopher Dearie
Copyright: Dearie Labs
Title: Factory Delete Default VPC
Description: Deletes the default vpc in each region
"""

import os
import copy

import boto3
import botocore.exceptions


class DeleterWorker(object):
    def __init__(self,profileName=None, billing_arn=None, dryRun=False, region='us-west-2'):
        self.session = boto3.Session(profile_name=profileName, region_name=region)
        self.dryRun = dryRun

        billing_credentials = self.session.client('sts').assume_role(
            RoleArn=billing_arn,
            RoleSessionName='billing')['Credentials']

        # use Billing Creds to create a Team Session
        self.billing_session = boto3.Session(aws_access_key_id=billing_credentials['AccessKeyId'],
                                          aws_secret_access_key=billing_credentials['SecretAccessKey'],
                                          aws_session_token=billing_credentials['SessionToken'])

        self.billing_sts = self.billing_session.client('sts', region_name=region)
        self.billing_ec2 = self.billing_session.client('ec2', region_name=region)

    def raise_error(self, event, error_message):
        error = event['Attributes']['StateMachine']['Error']
        error['Raised'] = True
        error['ErrorMessage'] = error_message

    def handle_message(self, event):

        account = event['Body']['team_account_number']
        print(account)
        role_arn = "arn:aws:iam::{0}:role/LinkedPayerAccountRole".format(account)

        try:
            team_creds = self.billing_sts.assume_role(RoleArn=role_arn, RoleSessionName='team')[
                'Credentials']
        except:
            return self.raise_error(event,'Unable to assume LinkedPayerRole')

        regions = []
        # if region is given in event, limit to single region. Otherwise loop through all
        if 'regions' in event['Body'] and event['Body']['regions']:
            regions = event['Body']['regions']
        else:
            # Collect All Regions
            res = self.billing_ec2.describe_regions()['Regions']

            for r in res:
                regions.append(r['RegionName'])

        objects_deleted = 0
        # Loop through region list
        for r in regions:

            # build ec2 client for current region
            print("Region set to: {0}".format(r))
            ec2 = boto3.client('ec2', aws_access_key_id=team_creds["AccessKeyId"],
                              aws_secret_access_key=team_creds["SecretAccessKey"],
                              aws_session_token=team_creds["SessionToken"],
                               region_name=r)
            try:
                resp = ec2.describe_account_attributes(AttributeNames=['default-vpc'])
                attributes = resp['AccountAttributes']
            except:
                return self.raise_error(event, 'Unable to describe account attribues')

            for attribute in attributes:

                if attribute['AttributeName'] != 'default-vpc':
                    continue
                vpc_id = attribute['AttributeValues'][0]['AttributeValue']

            if vpc_id == 'none':
                print('result: no default vpc')
                continue

            # Internet Gateway
            gw_filters = [{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            rsp = ec2.describe_internet_gateways(Filters=gw_filters)
            igw = rsp.get('InternetGateways', [])

            if igw:
                try:
                    status = ec2.detach_internet_gateway(
                        InternetGatewayId=igw[0]['InternetGatewayId'],
                        VpcId=vpc_id, DryRun=self.dryRun)
                    print(status)
                    status = ec2.delete_internet_gateway(
                        InternetGatewayId=igw[0]['InternetGatewayId'], DryRun=self.dryRun)
                    print(status)
                    objects_deleted += 1
                except botocore.exceptions.ClientError as e:
                    if not self.dryRun:
                        return self.raise_error(event=event,error_message=e)
                    else:
                        print("Dry Run: Delete IGW {0}".format(igw[0]['InternetGatewayId']))

            #subnets
            subnet_filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
            rsp = ec2.describe_subnets(Filters=subnet_filters)
            subs = rsp.get('Subnets', [])
            if subs:
                try:
                    for sub in subs:
                        status = ec2.delete_subnet(SubnetId=sub['SubnetId'], DryRun=self.dryRun)
                        objects_deleted += 1
                except botocore.exceptions.ClientError as e:
                    if not self.dryRun:
                        return self.raise_error(event=event,error_message=e)
                    else:
                        print("Dry Run: Delete Subnet: {0}".format(sub['SubnetId']))

            # VPC
            try:
                status = ec2.delete_vpc(VpcId=vpc_id, DryRun=self.dryRun)
                objects_deleted += 1
            except botocore.exceptions.ClientError as e:
                if not self.dryRun:
                    return self.raise_error(event=event,error_message=e)
                else:
                    print("Dry Run: Delete VPC: {0}".format(vpc_id))


def lambda_handler(event, context):
    #Test
    if event.get('test', False):
        billing_role_arn = os.environ['billing_role_arn']
        delete_worker = DeleterWorker(billing_arn=billing_role_arn)
        event.update({'deletevpc_test': {'delete_worker': delete_worker.dryRun}})
        return event

    # Create Event copy
    delete_event = copy.deepcopy(event)

    # Pull billing role arn from Env Vars
    try:
        billing_role_arn = os.environ['billing_role_arn']
    except:
       raise Exception("Billing Role Env Var not found")

    delete_worker = DeleterWorker(billing_arn=billing_role_arn)
    delete_worker.handle_message(delete_event)

    return delete_event


if __name__ == '__main__':
    event = {
        'Attributes': {
            'EventName': 'NewTeam',
            'EventVersion': 1,
            'GUID': 'welcometothejungle',
            'StateMachine': {
                'Valid': True,
                "Error": {
                    "Raised": False,
                    "ErrorMessage": ""
                }
            }
        },
        'Body': {
            'totes': 'brah',
            'team_account_number': '244211622104',
            'regions': []
        }
    }

    delete_event = copy.deepcopy(event)

    # Pull billing role arn from Env Vars
    try:
        billing_role_arn = os.environ['billing_role_arn']
    except:
       raise Exception("Billing Role Env Var not found")
