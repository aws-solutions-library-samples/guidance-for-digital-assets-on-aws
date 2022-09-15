import json
import os
from datetime import datetime

import awswrangler as wr
import boto3
import requests

from initblocks import *
from worker import *

app = os.environ['COPILOT_APPLICATION_NAME']
envName = os.environ['COPILOT_ENVIRONMENT_NAME']

SCHEMA_VERSION = os.environ['SCHEMA_VERSION']
PREFIX = SCHEMA_VERSION+'/eth'

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='/copilot/applications/'+app+'/'+envName +
                              '/public-blockchain-data-s3bucket', WithDecryption=True)
BUCKET = parameter['Parameter']['Value']

TOPIC_ARNS = json.loads(os.getenv("COPILOT_SNS_TOPIC_ARNS"))

client = boto3.client('sns')
s3_client = boto3.client('s3')

eth_endpoint = os.environ['ETH_ENDPOINT'].split(':')
ETH_HOST = eth_endpoint[0]
ETH_PORT = int(eth_endpoint[1])


def rpc_erigon(data):
    serverURL = 'http://' + str(ETH_HOST)+":" + str(ETH_PORT)+'/'
    headers = {'content-type': "application/json"}
    payload = data
    c = 0
    res = None
    while c < 5 and res is None:
        try:
            response = requests.post(serverURL, headers=headers, data=payload)
            res = response.json()
        except Exception as e:
            print(e)
            c = c+1
            print('sleep')
            time.sleep(c)
    return res


def getBlockByNumber(block):
    i = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": [hex(block), True], "id": 1}
    data = json.dumps(i)
    r = rpc_erigon(data)
    return r['result']


def blockNumber():
    i = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    data = json.dumps(i)
    r = rpc_erigon(data)
    n = int(r['result'], 16)
    return n


def importBlockWorker(number):
    msg = {"method": "importBlockByNumber", "number": number}
    data = json.dumps(msg)
    response = client.publish(
        TopicArn=TOPIC_ARNS["ethTopic"],
        Message=data
    )


def importByDateWorker(date):
    msg = {"method": "importByDate", "date": date}
    data = json.dumps(msg)
    response = client.publish(
        TopicArn=TOPIC_ARNS["ethTopic"],
        Message=data
    )


def importBlockLocal(n):
    print("importBlock:%s" % n)
    local = False
    if local:
        importBlock(n)
    else:
        importBlockWorker(n)


def importByDateLocal(n):
    print("importByDateLocal:%s" % n)
    local = True
    if local:
        importByDate(n)
    else:
        importByDateWorker(n)


def reimport():
    sDate = datetime.date(2015, 7, 30)

    eDate = datetime.date.today()+datetime.timedelta(days=-1)
    print("sDate=%s,eDate=%s")

    while sDate <= eDate:
        sDateStr = '%s-%02d-%02d' % (sDate.year, sDate.month, sDate.day)
        print('sDateStr=%s' % sDateStr)
        importByDateLocal(sDateStr)
        sDate = sDate+datetime.timedelta(days=1)


print('start')
reimport()
print('complete')
