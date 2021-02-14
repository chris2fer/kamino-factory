import boto3
import botocore.exceptions
import copy
import json
import logging
import uuid
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('sns')
account = boto3.client('sts').get_caller_identity().get('Account')
topic_name = 'FactoryEventPipeline'
topic_arn = 'arn:aws:sns:us-west-2:%s:%s' % (account, topic_name)
topic_arn = os.environ.get('sns_topic')

def lambda_handler(event, context):
    '''Parses JSON message from API Gateway.
    Adds GUID if message is unidentified.
    Publishes message with GUID to SNS topic.
    '''
    guid_event = copy.deepcopy(event)
    message = json.dumps(guid_event)

    logger.info('Received GUID event ' + message)
    
    # ensure event/request body is in schema format
    if 'Attributes' not in guid_event:
        logger.error('Bad Request: no Attributes found in event: ' + message)
        raise Exception('[BadRequest] no Attributes found in event')
    
    # add GUID if necessary
    attr = guid_event['Attributes']
    if 'GUID' not in attr:
        attr['GUID'] = str(uuid.uuid4())
    
    # post to SNS
    try:
        response = client.publish(TopicArn=topic_arn, Message=json.dumps(guid_event))
        logger.info('SNS response: ' + str(response))
    except botocore.exceptions.ClientError as e:
        logger.error('Error publishing to SNS: ' + str(e))
        raise Exception('[InternalServerError] ' + str(e))
    
    # log results
    guid = attr['GUID']
    logger.info('Published message to SNS topic with GUID ' + guid)
    
    return {"GUID": guid}
