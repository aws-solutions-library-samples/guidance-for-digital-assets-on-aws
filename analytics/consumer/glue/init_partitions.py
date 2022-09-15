import copy
import datetime
import os
import sys

import boto3

glue_client = boto3.client("glue")

args = sys.argv

app = os.environ['COPILOT_APPLICATION_NAME']
env = os.environ['COPILOT_ENVIRONMENT_NAME']
SCHEMA_VERSION = os.environ['SCHEMA_VERSION']

sym = args[1]

flag = False
if len(args) == 3:
    flag = (args[2] == "true")

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='/copilot/applications/'+app+'/'+env +
                              '/public-blockchain-data-s3bucket', WithDecryption=True)
S3_BUCKET = parameter['Parameter']['Value']

if S3_BUCKET is None:
    print("S3 bucket not found")
    sys.exit(1)

# current date
d = datetime.date.today()
dStr = '%s-%02d-%02d' % (d.year, d.month, d.day)
print('dStr=%s' % dStr)

s3_client = boto3.client('s3')


def processPrefix(PREFIX, DATABASE_NAME, TABLE_NAME, existingPartList):
    print('processPrefix:%s' % PREFIX)
    fStart = PREFIX.replace('/', '-')
    # get folders
    folders = []
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=PREFIX)
    for page in pages:
        if 'Contents' in page:
            for object in page['Contents']:
                pref = object['Key']
                x = '/'.join(pref.split('/')[:-1])+'/'
                if x not in folders:
                    folders.append(x)

    partList = []
    # process folders
    for x in folders:
        #print('FOLDER:%s' % [x])
        pList = x.split('/')
        dStr1 = (pList[3].split('=')[1]).split('-')
        yearStr = dStr1[0]
        monthStr = dStr1[1]
        dayStr = dStr1[2]
        folderDate = yearStr+'-'+monthStr+'-'+dayStr
        #print("folderDate=%s" % (folderDate))
        if folderDate != dStr and folderDate not in existingPartList:
            partList.append(folderDate)

    print("new partitions:%s" % len(partList))
    try:
        get_table_response = glue_client.get_table(
            DatabaseName=DATABASE_NAME,
            Name=TABLE_NAME
        )

        # Extract the existing storage descriptor and Create custom storage descriptor with new partition location
        storage_descriptor = get_table_response['Table']['StorageDescriptor']

        partList2 = []
        for x in partList:
            custom_storage_descriptor = copy.deepcopy(storage_descriptor)
            custom_storage_descriptor['Location'] = storage_descriptor['Location'] + "/date=" + "/".join([x]) + '/'
            # print(custom_storage_descriptor['Location'])
            partList2.append({
                'Values': [x],
                'StorageDescriptor': custom_storage_descriptor
            })
            if len(partList2) == 100:
                # Create new Glue partition in the Glue Data Catalog
                create_partition_response = glue_client.batch_create_partition(
                    DatabaseName=DATABASE_NAME,
                    TableName=TABLE_NAME,
                    PartitionInputList=partList2
                )
                print(create_partition_response)
                partList2 = []
        if len(partList2) > 0:
            # Create new Glue partition in the Glue Data Catalog
            create_partition_response = glue_client.batch_create_partition(
                DatabaseName=DATABASE_NAME,
                TableName=TABLE_NAME,
                PartitionInputList=partList2
            )
            print(create_partition_response)

    except Exception as e:
        # Handle exception as per your business requirements
        print(e)


def delete_partitions(database, table, partitions, batch=25):
    for i in range(0, len(partitions), batch):
        to_delete = [{k: v[k]} for k, v in zip(["Values"]*batch, partitions[i:i+batch])]
        glue_client.batch_delete_partition(
            DatabaseName=database,
            TableName=table,
            PartitionsToDelete=to_delete)


def get_and_delete_partitions(database, table0, deleteFirst):
    table = table0

    paginator = glue_client.get_paginator('get_partitions')
    itr = paginator.paginate(DatabaseName=database, TableName=table)

    partList = []

    for page in itr:
        if deleteFirst:
            delete_partitions(database, table, page["Partitions"])
        else:
            for x in page["Partitions"]:
                partList.append(x['Values'][0])

    partList.sort()
    processPrefix(SCHEMA_VERSION+'/'+database+'/'+table0+'/', database, table, partList)


if sym == 'btc' or sym == 'all':
    get_and_delete_partitions('btc', 'blocks', flag)
    get_and_delete_partitions('btc', 'transactions', flag)
if sym == 'eth' or sym == 'all':
    get_and_delete_partitions('eth', 'blocks', flag)
    get_and_delete_partitions('eth', 'transactions', flag)
    get_and_delete_partitions('eth', 'token_transfers', flag)
    get_and_delete_partitions('eth', 'traces', flag)
    get_and_delete_partitions('eth', 'contracts', flag)
    get_and_delete_partitions('eth', 'logs', flag)
if sym == 'eth2' or sym == 'all':
    get_and_delete_partitions('eth', 'traces', flag)
    get_and_delete_partitions('eth', 'transactions', flag)
