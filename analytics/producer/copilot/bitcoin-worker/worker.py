import copy
import json
import os
import threading
import time
import traceback
from datetime import datetime
from decimal import *
from http.server import BaseHTTPRequestHandler, HTTPServer

import awswrangler as wr
import boto3
import requests
from botocore.exceptions import ClientError
from dynamodb_json import json_util as jsondb
from pandas import json_normalize

btc_endpoint = os.environ['BTC_ENDPOINT'].split(':')
host = btc_endpoint[0]
rpcPort = int(btc_endpoint[1])

deliveryBlocks = 'blocks'
deliveryTransactions = 'transactions'

use_dynamodb = (os.environ['USE_DYNAMODB'] == 'true')

rpc_user = os.environ['RPC_USER']
rpc_password = os.environ['RPC_PASSWORD']

SCHEMA_VERSION = os.environ['SCHEMA_VERSION']
PREFIX = SCHEMA_VERSION+'/btc'

BUCKET = os.environ['S3_BUCKET']

s3_client = boto3.client('s3')

if use_dynamodb:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('btc_output')

COPILOT_QUEUE_URI = os.getenv("COPILOT_QUEUE_URI")

region = os.environ['AWS_REGION']
sqs_client = boto3.client("sqs", region_name=region)


def receive_queue_message():
    try:
        response = sqs_client.receive_message(QueueUrl=COPILOT_QUEUE_URI, WaitTimeSeconds=5, MaxNumberOfMessages=1)
    except ClientError:
        print('Could not receive the message from the - {}.'.format(
            COPILOT_QUEUE_URI))
        raise
    else:
        return response


def delete_queue_message(receipt_handle):
    try:
        response = sqs_client.delete_message(QueueUrl=COPILOT_QUEUE_URI,
                                             ReceiptHandle=receipt_handle)
    except ClientError:
        print('Could not delete the meessage from the - {}.'.format(
            COPILOT_QUEUE_URI))
        raise
    else:
        return response


def rpc(data):
    serverURL = 'http://' + str(host)+":" + str(rpcPort)+'/'
    headers = {'content-type': "application/json"}
    payload = json.dumps(data)
    c = 0
    res = None
    while c < 5 and res is None:
        try:
            response = requests.post(serverURL, headers=headers, data=payload, auth=(rpc_user, rpc_password))
            res = response.json()
        except Exception as e:
            print(e)
            c = c+1
            print('sleep')
            time.sleep(c)
    return res


def getblockcount():
    data = {"method": 'getblockcount', "params": [], "id": 1, "jsonrpc": "2.0"}
    r = rpc(data)
    return r['result']


def getblockhash(number):
    data = {"method": 'getblockhash', "params": [number], "id": 1, "jsonrpc": "2.0"}
    r = rpc(data)
    return r['result']


def getblock(hash, verbosity=1):
    data = {"method": 'getblock', "params": [hash, verbosity], "id": 1, "jsonrpc": "2.0"}
    r = rpc(data)
    return r['result']


def getrawtransaction(txid):
    data = {"method": 'getrawtransaction', "params": [txid, True], "id": 1, "jsonrpc": "2.0"}
    r = rpc(data)
    return r['result']


def lookupTxBatch(ids):
    d = {}
    sl = [ids[x:x+100] for x in range(0, len(ids), 100)]
    for sl1 in sl:
        batch_keys = {
            'btc_output': {
                'Keys': [{'id': x} for x in sl1]
            }
        }
        sleepy_time = 1
        retrieved = {key: [] for key in batch_keys}
        while True:
            response = dynamodb.batch_get_item(RequestItems=batch_keys)
            for key in response.get('Responses', []):
                retrieved[key] += response['Responses'][key]
            unprocessed = response['UnprocessedKeys']
            if len(unprocessed) > 0:
                batch_keys = unprocessed
                unprocessed_count = sum(
                    [len(batch_key['Keys']) for batch_key in batch_keys.values()])
                print(
                    "%s unprocessed keys returned. Sleep, then retry.",
                    unprocessed_count)
                print("Sleeping for %s seconds.", sleepy_time)
                time.sleep(sleepy_time)
            else:
                break
        l = retrieved['btc_output']
        for x in l:
            x = decodeItem(x)
            d[x['id']] = x
    return d


def encodeItem(item):
    v = item['value']
    item['value'] = str(v)
    item2 = jsondb.loads(jsondb.dumps(item))
    item['value'] = v
    return item2


def decodeItem(x):
    x = jsondb.loads(jsondb.dumps(x))
    x['value'] = float(x['value'])
    return x


def checkDataFrame(df, tableName):
    fields = {}
    if tableName == "blocks":
        fields = {
            'date': 'string',
            'hash': 'string',
            'size': 'bigint',
            'stripped_size': 'bigint',
            'weight': 'bigint',
            'number': 'bigint',
            'version': 'long',
            'merkle_root': 'string',
            'timestamp': 'timestamp',
            'nonce': 'bigint',
            'bits': 'string',
            'coinbase_param': 'string',
            'transaction_count': 'bigint',
            'mediantime': 'timestamp',
            'difficulty': 'double',
            'chainwork': 'string',
            'previousblockhash': 'string',
            'last_modified': 'timestamp'
        }
    elif tableName == "transactions":
        fields = {
            'date': 'string',
            'hash': 'string',
            'size': 'bigint',
            'virtual_size': 'bigint',
            'version': 'bigint',
            'lock_time': 'bigint',
            'block_hash': 'string',
            'block_number': 'bigint',
            'block_timestamp': 'timestamp',
            'index': 'bigint',
            'input_count': 'bigint',
            'output_count': 'bigint',
            'input_value': 'double',
            'output_value': 'double',
            'is_coinbase': 'boolean',
            'fee': 'double',
            'inputs': 'array',
            'outputs': 'array',
            'last_modified': 'timestamp'
        }

    c = 0
    updated = False
    cList = list(df.columns.values)
    for x in df.dtypes:
        col = cList[c]
        colName = str(col)
        if colName in fields:
            t = fields[colName]
            if t == "bigint":
                t = "int64"
            elif t == "double":
                t = "float64"
            elif t == "timestamp":
                t = "datetime64[ns]"
            if t.lower() != str(x).lower() and col != "date" and t not in ['array', 'boolean']:
                if t == "int64":
                    df[colName] = df[colName].astype('Int64')
                    updated = True
                elif t == "float64":
                    df[colName] = df[colName].astype('Float64')
                    updated = True
                elif t == "string":
                    df[colName] = df[colName].astype('str')
                    updated = True
                elif t == "decimal":
                    df[colName] = df[colName].apply(Decimal)
                    updated = True
        else:
            print("removed col:%s" % colName)
            del df[colName]
            updated = True
        c = c+1
    return updated


def stream(stream, l):
    if len(l) > 0:
        firstRow = l[0]
        block = None
        part = []
        t = None
        block_field = None
        if stream == 'blocks':
            block_field = 'number'
            block = firstRow[block_field]
            t = firstRow['timestamp']
        else:
            block_field = 'block_number'
            block = firstRow[block_field]
            t = firstRow['block_timestamp']

        pref = PREFIX+'/'+stream+'/date='+('%s' % t.year)+'-'+('%02d' % t.month)+'-'+('%02d' % t.day)
        pathStr = 's3://'+BUCKET+'/'+pref+'/'
        df = json_normalize(l)

        checkDataFrame(df, stream)

        r = wr.s3.to_parquet(
            df=df,
            path=pathStr+str(block)+'.snappy.parquet',
            dataset=False
        )


def addPartition(obj, k, t):
    obj[k] = t
    obj['date'] = str(t.year)+'-'+('%02d' % t.month)+'-'+('%02d' % t.day)
    obj['last_modified'] = datetime.now()


def processBlock(block):
    start = time.time()

    bTime = block['time']
    bTimeObj = datetime.fromtimestamp(bTime)
    nt = 0
    ntc = len(block['tx'])
    txList = []
    coinbase_param = None

    txLookupCount = 0

    # batch lookup
    idList = []
    for tx in block['tx']:
        for vin in tx['vin']:
            if 'coinbase' not in vin:
                spent_tx = vin['txid']
                spent_index = int(vin['vout'])
                idStr = (spent_tx+":"+str(spent_index))
                idList.append(idStr)
    usedIdlist = []
    idMap = {}
    if use_dynamodb:
        idMap = lookupTxBatch(idList)
    idMapOrig = idMap.copy()
    print("idList=%s:vin=%s" % (len(idMap), len(idList)))

    oList = []
    for tx in block['tx']:
        inList = []
        outList = []
        is_coinbase = False

        # inputs
        ni = 0
        nic = len(tx['vin'])

        for vin in tx['vin']:
            if 'coinbase' in vin:
                is_coinbase = True
                coinbase_param = vin['coinbase']
            else:
                vin['index'] = ni

                spent_tx = vin['txid']
                vin['spent_transaction_hash'] = spent_tx
                del vin['txid']

                if 'scriptSig' in vin:
                    scriptPubKey = vin['scriptSig']
                    vin['script_asm'] = scriptPubKey['asm']
                    vin['script_hex'] = scriptPubKey['hex']
                    del vin['scriptSig']

                spent_index = int(vin['vout'])
                vin['spent_output_index'] = spent_index
                del vin['vout']

                idStr = (spent_tx+":"+str(spent_index))
                txin = None
                if idStr in idMap:
                    txin = idMap[idStr]
                if txin is None:
                    txin1 = getrawtransaction(spent_tx)
                    if txin1 is not None:
                        txin = txin1['vout'][spent_index]
                        txin['id'] = idStr
                        txLookupCount = txLookupCount+1
                    else:
                        print("ERROR: txin not found")

                if txin is not None:
                    usedIdlist.append(txin['id'])
                    pubKey = txin['scriptPubKey']
                    if 'address' in pubKey:
                        vin['address'] = pubKey['address']
                    vin['value'] = txin['value']
                    vin['type'] = pubKey['type']

                    required_signatures = 1
                    if vin['type'] == 'multisig':
                        required_signatures = int(pubKey['asm'].split(' ')[0])
                    vin['required_signatures'] = required_signatures
                else:
                    raise Exception('tx', 'ERROR: txin not found')

                ni = ni+1
                inList.append(vin)

        # outputs
        outvalue = 0.0
        no = 0
        noc = len(tx['vout'])

        for vout in tx['vout']:
            vout['block_number'] = block['height']
            id = tx['txid']+':'+str(vout['n'])
            vout['id'] = id
            vout1 = copy.deepcopy(vout)
            oList.append(vout1)
            idMap[id] = vout1
            del vout['id']
            del vout['block_number']

            pubKey = vout['scriptPubKey']
            vout['type'] = pubKey['type']
            vout['script_asm'] = pubKey['asm']
            vout['script_hex'] = pubKey['hex']
            required_signatures = 1
            if vout['type'] == 'multisig':
                required_signatures = int(vout['script_asm'].split(' ')[0])
            vout['required_signatures'] = required_signatures

            if 'address' in pubKey:
                vout['address'] = pubKey['address']
            del vout['scriptPubKey']

            vout['index'] = vout['n']
            del vout['n']
            if 'value' in vout:
                outvalue = outvalue+vout['value']

            no = no+1
            outList.append(vout)

        # tx
        tx['block_hash'] = block['hash']
        tx['block_number'] = block['height']
        tx['index'] = nt
        tx['virtual_size'] = tx['vsize']
        tx['lock_time'] = tx['locktime']
        tx['input_count'] = ni
        tx['output_count'] = no
        tx['is_coinbase'] = is_coinbase
        if is_coinbase:
            block['coinbase_param'] = coinbase_param
        inputval = outvalue
        if 'fee' in tx:
            inputval = inputval+tx['fee']
        if ni > 0:
            tx['input_value'] = inputval
            tx['inputs'] = inList
        tx['output_value'] = outvalue
        tx['outputs'] = outList
        addPartition(tx, 'block_timestamp', bTimeObj)
        del tx['vin']
        del tx['vout']
        del tx['vsize']
        del tx['locktime']

        nt = nt+1
        txList.append(tx)

    # block
    block['number'] = block['height']
    block['transaction_count'] = block['nTx']
    block['merkle_root'] = block['merkleroot']
    block['stripped_size'] = block['strippedsize']
    del block['height']
    del block['tx']
    del block['confirmations']
    del block['time']
    del block['nTx']
    del block['versionHex']
    del block['merkleroot']
    del block['strippedsize']
    if 'nextblockhash' in block:
        del block['nextblockhash']
    addPartition(block, 'timestamp', bTimeObj)

    block['mediantime'] = datetime.fromtimestamp(block['mediantime'])

    blockList = []
    blockList.append(block)
    stream(deliveryBlocks, blockList)
    stream(deliveryTransactions, txList)

    print("txLookupCount:%s" % txLookupCount)
    if use_dynamodb:
        # insert output
        oListLen = 0
        with table.batch_writer() as writer:
            for x in oList:
                if x['id'] not in usedIdlist:
                    y = encodeItem(x)
                    writer.put_item(Item=y)
                    oListLen = oListLen+1
                else:
                    del idMap[x['id']]
        print("inserted dynamodb:%s" % oListLen)
        # remove input
        iListLen = 0
        with table.batch_writer() as writer:
            for x in idMapOrig:
                y = {'id': x}
                writer.delete_item(Key=y)
                iListLen = iListLen+1
        print("deleted dynamodb:%s" % iListLen)

    end = time.time()
    print("processed block in %.4f" % ((end - start)))
    return True


def importBlock(number):
    print("importBlock:%s" % number)
    block = getblock(getblockhash(number), 2)
    processBlock(block)


def importBlockByHash(hash):
    print("importBlockByHash:%s" % hash)
    c = 0
    block = getblock(hash, 2)
    while block is None and c < 5:
        c = c+1
        print("retry: sleep:%s" % c)
        time.sleep(c)
        block = getblock(hash, 2)
    processBlock(block)


def importBlocksByRange(fromBlock, toBlock):
    n = fromBlock
    while n <= toBlock:
        importBlock(n)
        n = n+1


class MyHttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        healthy = True
        if healthy:
            DATA = {'healthy': healthy}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(DATA).encode())
        else:
            self.send_response(501)
        return


def start_server():
    print('start http 8080')
    httpd = HTTPServer(('', 8080), MyHttpHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    daemon = threading.Thread(name='http_server', target=start_server, daemon=True)
    daemon.start()

    while True:
        messages = receive_queue_message()
        print(messages)

        if "Messages" in messages:
            for msg in messages['Messages']:
                msg_body = msg['Body']
                receipt_handle = msg['ReceiptHandle']

                print(f'The message body: {msg_body}')
                try:
                    m = json.loads(json.loads(msg_body)['Message'])
                    print("m=%s" % m)
                    if 'method' in m:
                        method = m['method']
                        print("method=%s" % method)
                        if method == "importBlockByNumber":
                            b = m['number']
                            importBlock(b)
                        elif method == "importBlockByHash":
                            b = m['hash']
                            importBlockByHash(b)
                        elif method == "importBlocksByRange":
                            importBlocksByRange(m['from'], m['to'])
                    else:
                        print("no method")
                    print("complete")

                    print('Deleting message from the queue...')
                    resp_delete = delete_queue_message(receipt_handle)
                except Exception as e:
                    traceback.print_exc()
