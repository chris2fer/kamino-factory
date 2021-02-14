import json

def process_event(event):
    print(event)

def receiver(event, context):
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }
    
    process_event(event)

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

