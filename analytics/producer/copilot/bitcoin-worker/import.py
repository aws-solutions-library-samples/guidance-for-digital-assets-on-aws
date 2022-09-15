import json
import os
import sys
from datetime import datetime

import awswrangler as wr
import boto3

from worker import *

app = os.environ['COPILOT_APPLICATION_NAME']
envName = os.environ['COPILOT_ENVIRONMENT_NAME']

btc_endpoint = os.environ['BTC_ENDPOINT'].split(':')
host = btc_endpoint[0]
rpcPort = int(btc_endpoint[1])

print("host=%s,port=%s" % (host, rpcPort))

deliveryBlocks = 'blocks'
deliveryTransactions = 'transactions'

rpc_user = os.environ['RPC_USER']
rpc_password = os.environ['RPC_PASSWORD']

SCHEMA_VERSION = os.environ['SCHEMA_VERSION']
PREFIX = SCHEMA_VERSION+'/btc'

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='/copilot/applications/'+app+'/'+envName +
                              '/public-blockchain-data-s3bucket', WithDecryption=True)
BUCKET = parameter['Parameter']['Value']

s3_client = boto3.client('s3')

TOPIC_ARNS = json.loads(os.getenv("COPILOT_SNS_TOPIC_ARNS"))
print("TOPIC_ARNS=%s" % TOPIC_ARNS)
client = boto3.client('sns')


def importBlockWorker(number):
    msg = {"method": "importBlockByNumber", "number": number}
    data = json.dumps(msg)
    response = client.publish(
        TopicArn=TOPIC_ARNS["btcTopic"],
        Message=data
    )
    print("res=%s" % response)


def importBlockLocal(n):
    local = False
    if local:
        importBlock(n)
    else:
        importBlockWorker(n)


def importMissingBlocks(block_count):
    print("importMissingBlocks")
    path = PREFIX+'/'+deliveryBlocks
    bList = []
    flag = False

    paginator = s3_client.get_paginator('list_objects')
    operation_parameters = {'Bucket': BUCKET,
                            'Prefix': path}
    page_iterator = paginator.paginate(**operation_parameters)
    for page in page_iterator:
        if 'Contents' in page:
            for object in page['Contents']:
                pref = object['Key']
                f = '/'.join(pref.split('/')[:-1])
                if f not in bList:
                    bList.append(f)

    bList.sort()
    print(len(bList))

    l = 0
    n = 0
    load = False
    startDate = None

    while l < len(bList):
        b = bList[l]
        dStr = (b.split('/')[-1:][0]).split('=')[-1:][0]
        print("date=%s" % (b))
        if startDate is None or dStr >= startDate:
            d = wr.s3.read_parquet('s3://'+BUCKET+'/'+b, dataset=True)

            blocksArray = d['number'].unique()
            blocks = []
            for x in blocksArray:
                blocks.append(int(x))
            blocks.sort()
            if load:
                n = blocks[0]
                load = False
                print("set initial block:%s" % n)

            bt = b.replace('blocks', 'transactions')

            dt = None
            dt2 = None
            try:
                dt = wr.s3.read_parquet('s3://'+BUCKET+'/'+bt, dataset=True)
                dt2 = dt.groupby("block_number")["txid"].count()
            except Exception as e:
                print(e)

            a = blocks[0]

            while a <= blocks[len(blocks)-1]:
                print('check block:%s' % a)
                while n < a:
                    print("import missing block:%s" % n)
                    importBlockLocal(n)
                    n = n+1

                if a in blocks:
                    b1 = d.loc[d['number'] == a]
                    rs = b1.shape[0]
                    if rs == 0:
                        bOrig = getblock(getblockhash(a), 1)
                        bTime = bOrig['time']
                        bTimeObj = datetime.fromtimestamp(bTime)
                        bDateStr = str(bTimeObj.year)+'-'+('%02d' % bTimeObj.month)+'-'+('%02d' % bTimeObj.day)

                        if bDateStr == dStr:
                            importBlockLocal(a)
                    elif rs > 1:
                        print("duplicate block")
                        sys.exit(1)
                    else:
                        bRec = b1.iloc[0]
                        reImport = False
                        if 'date' not in bRec or bRec['date'] != dStr:
                            print("REIMPORT needed: date not set")
                            reImport = True
                        else:
                            print(bRec['date'])
                        if dt2 is not None:
                            b2 = dt2.loc[a]
                            txc = b2.item()
                            print("count compare:tx=%s block=%s" % (txc, bRec['transaction_count']))
                            if txc != bRec['transaction_count']:
                                reImport = True
                        else:
                            reImport = True
                        if reImport:
                            print("REIMPORT needed: importBlock (tx=%s block=%s):%s" %
                                  (txc, bRec['transaction_count'], n))
                            sys.exit(1)
                else:
                    importBlockLocal(a)
                a = a+1
                n = n+1
        l = l+1

    while n <= block_count:
        print("import new:%s" % n)
        importBlockLocal(n)
        n = n+1


print("start")
block_count = getblockcount()
print("block_count=%s" % block_count)
importMissingBlocks(block_count)
print("complete")
