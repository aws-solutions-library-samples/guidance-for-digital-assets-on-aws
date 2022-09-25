import json
import boto3
import datetime
import os

client = boto3.client('sns')

TOPIC_ARNS = json.loads(os.getenv("COPILOT_SNS_TOPIC_ARNS"))


def importByDateWorker(date):
    msg = {"method": "importByDate", "date": date}
    data = json.dumps(msg)
    print("import:%s" % data)
    response = client.publish(
        TopicArn=TOPIC_ARNS["ethTopic"],
        Message=data
    )
    print(response)


def lambda_handler(event, context):
    d = datetime.date.today()
    d = d+datetime.timedelta(days=-1)
    dStr = '%s-%02d-%02d' % (d.year, d.month, d.day)
    print(dStr)

    importByDateWorker(dStr)

    return {
        'statusCode': 200,
        'body': 'ok'
    }
