
import os
import time
import traceback
from datetime import datetime
from decimal import *
from http.server import BaseHTTPRequestHandler, HTTPServer

import awswrangler as wr
import boto3
from botocore.exceptions import ClientError
from pandas import json_normalize

from initblocks import *
from rpc import *


deliveryBlocks = 'blocks'
deliveryTransactions = 'transactions'
deliveryLogs = 'logs'
deliveryTokenTransfers = 'token_transfers'
deliveryTraces = 'traces'
deliveryContracts = 'contracts'

SCHEMA_VERSION = os.environ['SCHEMA_VERSION']
PREFIX = SCHEMA_VERSION+'/eth'

BUCKET = os.environ['S3_BUCKET']

COPILOT_QUEUE_URI = os.getenv("COPILOT_QUEUE_URI")

region = os.environ['AWS_REGION']
sqs_client = boto3.client("sqs", region_name=region)
s3_client = boto3.client('s3')


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


def checkDataFrame(df, tableName):
    fields = {}
    if tableName == "blocks":
        fields = {
            'date': 'string',
            'timestamp': 'timestamp',
            'number': 'bigint',
            'hash': 'string',
            'parent_hash': 'string',
            'nonce': 'string',
            'sha3_uncles': 'string',
            'logs_bloom': 'string',
            'transactions_root': 'string',
            'state_root': 'string',
            'receipts_root': 'string',
            'miner': 'string',
            'difficulty': 'double',
            'total_difficulty': 'double',
            'size': 'bigint',
            'extra_data': 'string',
            'gas_limit': 'bigint',
            'gas_used': 'bigint',
            'transaction_count': 'bigint',
            'base_fee_per_gas': 'bigint',
            'last_modified': 'timestamp'
        }
    elif tableName == "logs":
        fields = {
            'date': 'string',
            'log_index': 'bigint',
            'transaction_hash': 'string',
            'transaction_index': 'bigint',
            'address': 'string',
            'data': 'string',
            'topics': 'array',
            'block_timestamp': 'timestamp',
            'block_number': 'bigint',
            'block_hash': 'string',
            'last_modified': 'timestamp'
        }
    elif tableName == "token_transfers":
        fields = {
            'date': 'string',
            'token_address': 'string',
            'from_address': 'string',
            'to_address': 'string',
            'value': 'double',
            'transaction_hash': 'string',
            'log_index': 'bigint',
            'block_timestamp': 'timestamp',
            'block_number': 'bigint',
            'block_hash': 'string',
            'last_modified': 'timestamp'
        }
    elif tableName == "contracts":
        fields = {
            'date': 'string',
            'address': 'string',
            'bytecode': 'string',
            'block_timestamp': 'timestamp',
            'block_number': 'bigint',
            'block_hash': 'string',
            'last_modified': 'timestamp'
        }
    elif tableName == "traces":
        fields = {
            'date': 'string',
            'transaction_hash': 'string',
            'transaction_index': 'bigint',
            'from_address': 'string',
            'to_address': 'string',
            'value': 'double',
            'input': 'string',
            'output': 'string',
            'trace_type': 'string',
            'call_type': 'string',
            'reward_type': 'string',
            'gas': 'double',
            'gas_used': 'double',
            'subtraces': 'bigint',
            'trace_address': 'string',
            'error': 'string',
            'status': 'bigint',
            'block_timestamp': 'timestamp',
            'block_number': 'bigint',
            'block_hash': 'string',
            'trace_id': 'string',
            'last_modified': 'timestamp'
        }
    elif tableName == "transactions":
        fields = {
            'date': 'string',
            'hash': 'string',
            'nonce': 'bigint',
            'transaction_index': 'bigint',
            'from_address': 'string',
            'to_address': 'string',
            'value': 'double',
            'gas': 'bigint',
            'gas_price': 'bigint',
            'input': 'string',
            'receipt_cumulative_gas_used': 'bigint',
            'receipt_gas_used': 'bigint',
            'receipt_contract_address': 'string',
            'receipt_status': 'bigint',
            'block_timestamp': 'timestamp',
            'block_number': 'bigint',
            'block_hash': 'string',
            'max_fee_per_gas': 'bigint',
            'max_priority_fee_per_gas': 'bigint',
            'transaction_type': 'bigint',
            'receipt_effective_gas_price': 'bigint',
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
            del df[colName]
            updated = True

        c = c+1
    return updated


def getBlockRangeForDate(d, amb=False):
    n = blockNumber(amb)
    print("latest=%s % n")
    maxN = n
    dNext = d+datetime.timedelta(days=1)
    dStr = '%s-%02d-%02d' % (d.year, d.month, d.day)
    print("getBlockRangeForDate:%s" % dStr)
    print("current=%s" % n)

    end = None
    start = None

    c = 0
    while (end is None or start is None) and c < 1000:
        c = c+1
        print("get block:%s" % n)
        block = getBlockByNumber(n, amb)
        if end is None:
            bTime = int(block['timestamp'], 16)
            bTimeObj = datetime.datetime.fromtimestamp(bTime)
            print(bTimeObj)
            blockStr = '%s-%02d-%02d' % (bTimeObj.year, bTimeObj.month, bTimeObj.day)
            if blockStr == dStr:
                block2 = getBlockByNumber(n+1, amb)
                bTime2 = int(block2['timestamp'], 16)
                bTimeObj2 = datetime.datetime.fromtimestamp(bTime2)
                print(bTimeObj2)
                blockStr2 = '%s-%02d-%02d' % (bTimeObj2.year, bTimeObj2.month, bTimeObj2.day)
                if blockStr2 > blockStr:
                    end = n
                    print("end=%s %s" % (end, blockStr))
            if end is None:
                dt = datetime.datetime.combine(dNext, datetime.datetime.min.time())
                diff = (bTimeObj-dt).total_seconds()
                print(diff)
                if diff > 60*3 or diff < 0:
                    nDiff = int(diff/14.5)
                    if diff < 0:
                        nDiff = int(diff/8)
                        if nDiff > -2:
                            nDiff = -2
                    # print(nDiff)
                    n = n-nDiff
                    print("adjusted to %s" % n)

        if end is not None and start is None:
            bTime = int(block['timestamp'], 16)
            bTimeObj = datetime.datetime.fromtimestamp(bTime)
            print(bTimeObj)
            blockStr = '%s-%02d-%02d' % (bTimeObj.year, bTimeObj.month, bTimeObj.day)
            if blockStr < dStr:
                block2 = getBlockByNumber(n+1, amb)
                bTime2 = int(block2['timestamp'], 16)
                bTimeObj2 = datetime.datetime.fromtimestamp(bTime2)
                print(bTimeObj2)
                blockStr2 = '%s-%02d-%02d' % (bTimeObj2.year, bTimeObj2.month, bTimeObj2.day)
                if blockStr2 == dStr:
                    start = n+1
                    print("start=%s %s" % (start, dStr))
            if start is None:
                dt = datetime.datetime.combine(d, datetime.datetime.min.time())
                diff = (bTimeObj-dt).total_seconds()
                print(diff)
                if diff > 60*3 or diff < 0:
                    nDiff = int(diff/14.5)
                    if diff < 0:
                        nDiff = int(diff/8)
                        if nDiff > -2:
                            nDiff = -2
                    # print(nDiff)
                    n = n-nDiff
                    print("adjusted to %s" % n)
        n = n-1
    return (start, end)


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
    obj['last_modified'] = datetime.datetime.now()


def processTracesContracts(block, amb=False):
    bTime = int(block['timestamp'], 16)
    bTimeObj = datetime.datetime.fromtimestamp(bTime)

    blockNumber = block['number']
    blockHash = block['hash']

    # traces
    rewardCount = 0
    traces = getTraceBlock(blockNumber, amb, block)
    if traces is None:
        print("WARN:trace empty for block:%s" % (blockNumber))
        traces = []
    sorted_traces = sorted(traces, key=lambda trace: len(trace['traceAddress'] or []))
    indexed_traces = {getTraceAddressStr(trace): trace for trace in sorted_traces}
    tracesList = []
    contractsList = []
    for trace in sorted_traces:
        updatedTrace = {}
        updatedTrace['block_number'] = trace['blockNumber']
        if 'transactionHash' in trace:
            updatedTrace['transaction_hash'] = trace['transactionHash']
        else:
            updatedTrace['transaction_hash'] = None

        if 'transactionPosition' in trace:
            updatedTrace['transaction_index'] = trace['transactionPosition']
        else:
            updatedTrace['transaction_index'] = None

        if 'error' in trace:
            updatedTrace['error'] = trace['error']
            updatedTrace['status'] = 0
        else:
            updatedTrace['error'] = None
            updatedTrace['status'] = 1

        traceId = None
        traceAddressStr = getTraceAddressStr(trace)

        if traceAddressStr is not None:
            parent_trace = indexed_traces.get(traceAddressStr)
            if parent_trace is None:
                logging.info('A parent trace for trace with trace_address {} in transaction {} is not found'
                             .format(traceAddressStr, trace['transactionHash']))
            elif 'error' in parent_trace:
                updatedTrace['status'] = 0

        traceId = None
        if updatedTrace['transaction_hash'] is not None:
            traceId = trace['type']+'_'+updatedTrace['transaction_hash']
            if traceAddressStr is not None:
                traceId = traceId+'_'+traceAddressStr.replace(',', "_")

        if trace['type'] == 'reward':
            traceId = trace['type']+'_'+str(trace['blockNumber'])+'_'+str(rewardCount)
            rewardCount = rewardCount+1

        updatedTrace['trace_id'] = traceId

        updatedTrace['subtraces'] = trace['subtraces']
        updatedTrace['trace_address'] = traceAddressStr
        updatedTrace['block_hash'] = blockHash

        action = {}
        if 'action' in trace:
            action = trace['action']
        result = {}
        if 'result' in trace and trace['result'] is not None:
            result = trace['result']

        traceType = trace['type']
        updatedTrace['trace_type'] = traceType

        # common fields in call/create
        updatedTrace['gas'] = None
        updatedTrace['gas_used'] = None
        if traceType == 'call' or traceType == 'create':
            updatedTrace['from_address'] = action['from']
            updatedTrace['value'] = float(int(action['value'], 16))
            updatedTrace['gas'] = int(action['gas'], 16)
            if 'gasUsed' in result:
                updatedTrace['gas_used'] = int(result['gasUsed'], 16)
            else:
                updatedTrace['gas_used'] = None

        updatedTrace['reward_type'] = None
        updatedTrace['input'] = None
        updatedTrace['output'] = None
        updatedTrace['call_type'] = None

        # process diff traceTypes
        if traceType == 'call':
            updatedTrace['call_type'] = action['callType']
            updatedTrace['to_address'] = action['to']
            updatedTrace['input'] = action['input']
            if 'output' in result:
                updatedTrace['output'] = result['output']
            else:
                updatedTrace['output'] = ''
        elif traceType == 'create':
            if 'address' in result:
                updatedTrace['to_address'] = result['address']
            else:
                updatedTrace['to_address'] = ''
            updatedTrace['input'] = action['init']
            if 'code' in result:
                updatedTrace['output'] = result['code']
            else:
                updatedTrace['output'] = ''
        elif traceType == 'suicide':
            updatedTrace['from_address'] = action['address']
            updatedTrace['to_address'] = action['refundAddress']
            if 'balance' in action:
                updatedTrace['value'] = float(int(action['balance'], 16))
        elif traceType == 'reward':
            updatedTrace['to_address'] = action['author']
            updatedTrace['value'] = float(int(action['value'], 16))
            updatedTrace['reward_type'] = action['rewardType']

        # update status
        addPartition(updatedTrace, 'block_timestamp', bTimeObj)
        tracesList += [updatedTrace]

        contract = {}
        if updatedTrace.get('trace_type') == 'create' and updatedTrace.get('to_address') is not None and len(updatedTrace.get('to_address')) > 0 and updatedTrace.get('status') == 1:
            result = trace['result']
            contract['address'] = updatedTrace['to_address']
            contract['bytecode'] = updatedTrace['output']
            contract['block_number'] = blockNumber
            contract['block_hash'] = blockHash
            addPartition(contract, 'block_timestamp', bTimeObj)
            contractsList += [contract]

    return (tracesList, contractsList)


def processTransactionsReceipts(block, amb=False):
    bTime = int(block['timestamp'], 16)
    bTimeObj = datetime.datetime.fromtimestamp(bTime)

    blockNumber = block['number']

    rt = 0
    rList = getBlockReceipts(blockNumber, amb, block)
    rtc = len(rList)-1
    rDict = {}
    for x in rList:
        k = x['transactionHash']
        rDict[k] = x

    blockTransactions = block['transactions']
    txList = []
    nt = 0
    ntc = len(blockTransactions)-1
    for tx in blockTransactions:
        tx['block_number'] = int(tx['blockNumber'], 16)
        del tx['blockNumber']
        tx['block_hash'] = tx['blockHash']
        del tx['blockHash']
        tx['transaction_index'] = int(tx['transactionIndex'], 16)
        del tx['transactionIndex']
        tx['from_address'] = tx['from']
        del tx['from']
        tx['to_address'] = tx['to']
        del tx['to']
        tx['nonce'] = int(tx['nonce'], 16)
        tx['value'] = float(int(tx['value'], 16))
        tx['gas'] = int(tx['gas'], 16)
        tx['gas_price'] = int(tx['gasPrice'], 16)
        del tx['gasPrice']

        r1 = rDict[tx['hash']]

        tx['receipt_cumulative_gas_used'] = int(r1['cumulativeGasUsed'], 16)
        tx['receipt_gas_used'] = int(r1['gasUsed'], 16)
        tx['receipt_contract_address'] = ""
        if 'contractAddress' in r1 and r1['contractAddress'] is not None:
            tx['receipt_contract_address'] = str(r1['contractAddress'])

        # Not Needed Pre Byzentium
        #tx['receipt_root']=None #
        tx['receipt_status'] = int(r1['status'], 16)
        tx['receipt_effective_gas_price'] = int(r1['effectiveGasPrice'], 16)
        del tx['v']  # Not Needed
        del tx['r']  # Not Needed
        del tx['s']  # Not Needed
        if 'chainId' in tx:
            del tx['chainId']
        if 'accessList' in tx:
            del tx['accessList']
        tx['transaction_type'] = int(tx['type'], 16)
        del tx['type']
        if 'maxFeePerGas' in tx:
            tx['max_fee_per_gas'] = int(tx['maxFeePerGas'], 16)
            del tx['maxFeePerGas']
        else:
            tx['max_fee_per_gas'] = 0
        if 'maxPriorityFeePerGas' in tx:
            tx['max_priority_fee_per_gas'] = int(tx['maxPriorityFeePerGas'], 16)
            del tx['maxPriorityFeePerGas']
        else:
            tx['max_priority_fee_per_gas'] = 0

        addPartition(tx, 'block_timestamp', bTimeObj)
        nt += 1
        txList += [tx]

    return (txList, rList)


def processLogsTokenTransfers(block, rList):
    bTime = int(block['timestamp'], 16)
    bTimeObj = datetime.datetime.fromtimestamp(bTime)

    blockHash = block['hash']

    # logs
    logsList = []
    # token_transfers
    token_transfersList = []

    TRANSFER_EVENT_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

    # receipts
    for rItem in rList:
        # logs
        if 'logs' in rItem:
            logs = rItem['logs']
            ln = 0
            lc = len(logs)-1
            for logObj in logs:
                if 'topics' in logObj:
                    topics = logObj['topics']
                    if topics is not None and len(topics) > 0 and topics[0] == TRANSFER_EVENT_TOPIC:
                        topics_with_data = topics + split_to_words(logObj['data'])
                        if len(topics_with_data) >= 4:
                            tokenTransferObj = {}
                            tokenTransferObj['token_address'] = logObj['address']
                            tokenTransferObj['from_address'] = topics_with_data[1]
                            tokenTransferObj['to_address'] = topics_with_data[2]
                            tokenTransferObj['value'] = float(int(topics_with_data[3], 16))
                            if logObj['data'] != '0x':
                                tokenTransferObj['value'] = float(int(logObj['data'], 16))
                            tokenTransferObj['transaction_hash'] = logObj['transactionHash']
                            tokenTransferObj['log_index'] = int(logObj['logIndex'], 16)
                            tokenTransferObj['block_number'] = int(logObj['blockNumber'], 16)
                            tokenTransferObj['block_hash'] = blockHash
                            addPartition(tokenTransferObj, 'block_timestamp', bTimeObj)

                            token_transfersList += [tokenTransferObj]

                logObj['transaction_index'] = int(logObj['transactionIndex'], 16)
                del logObj['transactionIndex']
                logObj['log_index'] = int(logObj['logIndex'], 16)
                del logObj['logIndex']
                logObj['transaction_hash'] = logObj['transactionHash']
                del logObj['transactionHash']
                logObj['block_number'] = int(logObj['blockNumber'], 16)
                del logObj['blockNumber']
                logObj['block_hash'] = blockHash
                del logObj['blockHash']
                del logObj['removed']  # TBD

                addPartition(logObj, 'block_timestamp', bTimeObj)
                ln += 1
                logsList += [logObj]

    return (logsList, token_transfersList)


def processBlockData(block):
    bTime = int(block['timestamp'], 16)
    bTimeObj = datetime.datetime.fromtimestamp(bTime)

    block['difficulty'] = float(int(block['difficulty'], 16))
    block['total_difficulty'] = float(int(block['totalDifficulty'], 16))
    del block['totalDifficulty']
    if 'baseFeePerGas' in block:
        block['base_fee_per_gas'] = int(block['baseFeePerGas'], 16)
        del block['baseFeePerGas']
    else:
        block['base_fee_per_gas'] = None

    block['size'] = int(block['size'], 16)
    block['gas_limit'] = int(block['gasLimit'], 16)
    del block['gasLimit']
    block['gas_used'] = int(block['gasUsed'], 16)
    del block['gasUsed']
    block['extra_data'] = block['extraData']
    del block['extraData']
    block['logs_bloom'] = block['logsBloom']
    del block['logsBloom']
    block['parent_hash'] = block['parentHash']
    del block['parentHash']
    block['state_root'] = block['stateRoot']
    del block['stateRoot']
    block['receipts_root'] = block['receiptsRoot']
    del block['receiptsRoot']
    block['transactions_root'] = block['transactionsRoot']
    del block['transactionsRoot']
    block['sha3_uncles'] = block['sha3Uncles']
    del block['sha3Uncles']
    del block['mixHash']
    del block['uncles']
    blockTransactions = block['transactions']
    block['transaction_count'] = len(blockTransactions)
    del block['transactions']

    addPartition(block, 'timestamp', bTimeObj)

    blockList = [block]
    return blockList


def processBlock(block):
    start = time.time()

    # transactions
    (txList, rList) = processTransactionsReceipts(block)
    # logs, token_transfers
    (logsList, token_transfersList) = processLogsTokenTransfers(block, rList)
    # traces, contracts
    (tracesList, contractsList) = processTracesContracts(block)
    # block
    blockList = processBlockData(block)

    stream(deliveryBlocks, blockList)
    stream(deliveryTransactions, txList)
    stream(deliveryLogs, logsList)
    stream(deliveryTokenTransfers, token_transfersList)
    stream(deliveryTraces, tracesList)
    stream(deliveryContracts, contractsList)

    end = time.time()
    print("processed block in %.4f" % ((end - start)))
    return True

# MIT License
#
# Copyright (c) 2018 Evgeny Medvedev, evge.medvedev@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def split_to_words(data):
    if data and len(data) > 2:
        data_without_0x = data[2:]
        words = list(chunk_string(data_without_0x, 64))
        words_with_0x = list(map(lambda word: '0x' + word, words))
        return words_with_0x
    return []


def chunk_string(string, length):
    return (string[0 + i:length + i] for i in range(0, len(string), length))

# ***


def getTraceAddressStr(trace):
    traceAdressStr = None
    if 'traceAddress' in trace:
        for x in trace['traceAddress']:
            if traceAdressStr is None:
                traceAdressStr = str(x)
            else:
                traceAdressStr = traceAdressStr+','+str(x)
    return traceAdressStr


def importBlock(number):
    try:
        print("importBlock:%s" % number)
        b = getBlockByNumber(number)
        processBlock(b)
    except Exception as ex:
        raise ex


def getFiles(pref):
    files = []
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET, Prefix=pref)
    for page in pages:
        if 'Contents' in page:
            for object in page['Contents']:
                s = object['Key']
                files += [s]
    return files


def writeFile(objList, s3pref, fileCount, table):
    tStr = str(time.time())
    nFile = s3pref+'/'+table+'-'+str(fileCount)+'-'+tStr+'.snappy.parquet'

    df = json_normalize(objList)
    checkDataFrame(df, table)
    print("write:%s" % nFile)

    r = wr.s3.to_parquet(
        df=df,
        path=nFile,
        dataset=False)
    print(r)


def importByDate(date, amb=False):
    print("importByDate:%s" % date)
    start = time.time()

    #latest = blockNumber(amb)
    #print("lastest=%s" % latest)

    blockMap = getBlockMap()
    minBlock = -1
    maxBlock = -1
    if date in blockMap:
        v = blockMap[date]
        minBlock = v['start']
        maxBlock = v['end']
    else:
        dateObj = datetime.datetime.strptime(date, '%Y-%m-%d')
        (minBlock, maxBlock) = getBlockRangeForDate(dateObj, amb)

    print("minBlock=%s,maxBlock=%s,count=%s" % (minBlock, maxBlock, (maxBlock-minBlock+1)))

    # if latest < maxBlock:
    #    print("blocks not synced:latest=%s last=%s diff=%s" % (latest, maxBlock, (latest-maxBlock)))

    s3pref = 's3://'+BUCKET+'/'
    blockS3 = s3pref+SCHEMA_VERSION+'/eth/blocks/date='+date
    txS3 = s3pref+SCHEMA_VERSION+'/eth/transactions/date='+date
    logS3 = s3pref+SCHEMA_VERSION+'/eth/logs/date='+date
    contractS3 = s3pref+SCHEMA_VERSION+'/eth/contracts/date='+date
    traceS3 = s3pref+SCHEMA_VERSION+'/eth/traces/date='+date
    transferS3 = s3pref+SCHEMA_VERSION+'/eth/token_transfers/date='+date

    blockFilesList = getFiles(blockS3[len(s3pref):])
    txFilesList = getFiles(txS3[len(s3pref):])
    logFilesList = getFiles(logS3[len(s3pref):])
    contractFilesList = getFiles(contractS3[len(s3pref):])
    traceFilesList = getFiles(traceS3[len(s3pref):])
    transferFilesList = getFiles(transferS3[len(s3pref):])

    deleteFilesList = blockFilesList+txFilesList+logFilesList+transferFilesList+traceFilesList+contractFilesList
    print('Current files (%s):%s' % (len(deleteFilesList), deleteFilesList))

    blockList = []
    txList = []
    logList = []
    contractList = []
    traceList = []
    transferList = []

    blockCount = 0
    txCount = 0
    logCount = 0
    contractCount = 0
    traceCount = 0
    transferCount = 0

    blockFileCount = 0
    txFileCount = 0
    logFileCount = 0
    contractFileCount = 0
    traceFileCount = 0
    transferFileCount = 0

    processed = 0
    blockNumber = minBlock
    blocksToImport = (maxBlock-minBlock+1)
    while blockNumber <= maxBlock:
        blockObj = getBlockByNumber(blockNumber, amb)
        if True:  # blockObj is not None:
            blockObj['number'] = int(blockObj['number'], 16)

            (txAdd, rList) = processTransactionsReceipts(blockObj, amb)
            txList += txAdd

            (logAdd, transferAdd) = processLogsTokenTransfers(blockObj, rList)
            logList += logAdd
            transferList += transferAdd

            (traceAdd, contractAdd) = processTracesContracts(blockObj, amb)
            traceList += traceAdd
            contractList += contractAdd

            blockAdd = processBlockData(blockObj)
            blockList += blockAdd

            if len(blockList) > 100000:
                blockCount += len(blockList)
                blockFileCount += 1
                writeFile(blockList, blockS3, blockFileCount, "blocks")
                blockList = []
            if len(txList) > 100000:
                txCount += len(txList)
                txFileCount += 1
                writeFile(txList, txS3, txFileCount, "transactions")
                txList = []
            if len(logList) > 100000:
                logCount += len(logList)
                logFileCount += 1
                writeFile(logList, logS3, logFileCount, "logs")
                logList = []
            if len(transferList) > 100000:
                transferCount += len(transferList)
                transferFileCount += 1
                writeFile(transferList, transferS3, transferFileCount, "token_transfers")
                transferList = []
            if len(traceList) > 100000:
                traceCount += len(traceList)
                traceFileCount += 1
                writeFile(traceList, traceS3, traceFileCount, "traces")
                traceList = []
            if len(contractList) > 100000:
                contractCount += len(contractList)
                contractFileCount += 1
                writeFile(contractList, contractS3, contractFileCount, "contracts")
                contractList = []

            processed = processed+1
            if processed > 1 and processed % 50 == 0:
                print("processed:%s of %s (%.2f)" % (processed, blocksToImport, processed/blocksToImport*100.0))
        else:
            print("WARN: block not found:%s" % blockNumber)

        blockNumber += 1

    # end of loop
    if len(blockList) > 0:
        blockCount += len(blockList)
        blockFileCount += 1
        writeFile(blockList, blockS3, blockFileCount, "blocks")
        blockList = []
    if len(txList) > 0:
        txCount += len(txList)
        txFileCount += 1
        writeFile(txList, txS3, txFileCount, "transactions")
        txList = []
    if len(logList) > 0:
        logCount += len(logList)
        logFileCount += 1
        writeFile(logList, logS3, logFileCount, "logs")
        logList = []
    if len(transferList) > 0:
        transferCount += len(transferList)
        transferFileCount += 1
        writeFile(transferList, transferS3, transferFileCount, "token_transfers")
        transferList = []
    if len(traceList) > 0:
        traceCount += len(traceList)
        traceFileCount += 1
        writeFile(traceList, traceS3, traceFileCount, "traces")
        traceList = []
    if len(contractList) > 0:
        contractCount += len(contractList)
        contractFileCount += 1
        writeFile(contractList, contractS3, contractFileCount, "contracts")
        contractList = []

    print("total blocks=%s" % blockCount)
    print("total transactions=%s" % txCount)
    print("total logs=%s" % logCount)
    print("total token_transfers=%s" % transferCount)
    print("total traces=%s" % traceCount)
    print("total contracts=%s" % contractCount)

    print('delete:%s' % len(deleteFilesList))
    for y in deleteFilesList:
        print(y)
        s3_client.delete_object(Bucket=BUCKET, Key=y)

    end = time.time()
    print("processed date in %.4f" % ((end - start)))


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
    while True:
        messages = receive_queue_message()
        if "Messages" in messages:
            for msg in messages['Messages']:
                msg_body = msg['Body']
                receipt_handle = msg['ReceiptHandle']
                try:
                    m = json.loads(json.loads(msg_body)['Message'])
                    if 'method' in m:
                        method = m['method']
                        print("method=%s" % method)
                        if method == "importBlockByNumber":
                            b = m['number']
                            importBlock(b)
                        elif method == "importByDate":
                            b = m['date']
                            importByDate(b)
                    else:
                        print("no method")
                    print("complete")

                    resp_delete = delete_queue_message(receipt_handle)
                except Exception as e:
                    traceback.print_exc()
