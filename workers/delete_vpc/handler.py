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


# class DeleterWorker(object):
#     def __init__(self, profileName=None, billing_arn=None, dryRun=False, region='us-east-1'):
        
#         self.target_account_id = target_account_id
#         self.target_role = target_role
#         self.target_account_role = f"arn:aws:iam::{target_account_id}:role/{target_role}"
#         self.session = boto3.Session()
#         self.dryRun = dryRun

#         self.billing_sts = self.billing_session.client('sts', region_name=region)
#         self.billing_ec2 = self.billing_session.client('ec2', region_name=region)

#     def handle_message(self, event):

 
#         factory_request = event['detail']

#         try:
#             team_creds = self.billing_sts.assume_role(RoleArn=role_arn, RoleSessionName='team')[
#                 'Credentials']
#         except:
#             return self.raise_error(event,'Unable to assume LinkedPayerRole')


#         res = self.billing_ec2.describe_regions()['Regions']
#         regions = [r['RegionName'] for r in res]

#         for r in regions:

#             print("Region set to: {0}".format(r))
#             ec2 = boto3.client('ec2', region_name=r)
#             try:
#                 resp = ec2.describe_account_attributes(AttributeNames=['default-vpc'])
#                 attributes = resp['AccountAttributes']
#             except:
#                 return self.raise_error(event, 'Unable to describe account attribues')

#             for attribute in attributes:

#                 if attribute['AttributeName'] != 'default-vpc':
#                     continue
#                 vpc_id = attribute['AttributeValues'][0]['AttributeValue']

#             if vpc_id == 'none':
#                 print('result: no default vpc')
#                 continue

#             # Internet Gateway
#             gw_filters = [{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
#             rsp = ec2.describe_internet_gateways(Filters=gw_filters)
#             igw = rsp.get('InternetGateways', [])

#             if igw:
#                 try:
#                     status = ec2.detach_internet_gateway(
#                         InternetGatewayId=igw[0]['InternetGatewayId'],
#                         VpcId=vpc_id, DryRun=self.dryRun)
#                     print(status)
#                     status = ec2.delete_internet_gateway(
#                         InternetGatewayId=igw[0]['InternetGatewayId'], DryRun=self.dryRun)
#                     print(status)
#                     objects_deleted += 1
#                 except botocore.exceptions.ClientError as e:
#                     if not self.dryRun:
#                         return self.raise_error(event=event,error_message=e)
#                     else:
#                         print("Dry Run: Delete IGW {0}".format(igw[0]['InternetGatewayId']))

#             #subnets
#             subnet_filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}]
#             rsp = ec2.describe_subnets(Filters=subnet_filters)
#             subs = rsp.get('Subnets', [])
#             if subs:
#                 try:
#                     for sub in subs:
#                         status = ec2.delete_subnet(SubnetId=sub['SubnetId'], DryRun=self.dryRun)
#                         objects_deleted += 1
#                 except botocore.exceptions.ClientError as e:
#                     if not self.dryRun:
#                         return self.raise_error(event=event,error_message=e)
#                     else:
#                         print("Dry Run: Delete Subnet: {0}".format(sub['SubnetId']))

#             # VPC
#             try:
#                 status = ec2.delete_vpc(VpcId=vpc_id, DryRun=self.dryRun)
#                 objects_deleted += 1
#             except botocore.exceptions.ClientError as e:
#                 if not self.dryRun:
#                     return self.raise_error(event=event,error_message=e)
#                 else:
#                     print("Dry Run: Delete VPC: {0}".format(vpc_id))

def process_event(event):

    regions = [r['RegionName'] for r in boto3.Session().client('ec2').describe_regions()['Regions']]

    for region in regions:
        print(region)


def lambda_handler(event, context):

    print(event)
    process_event(event)
    return event
