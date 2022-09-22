import json
import boto3
import os
import datetime

s3_client = boto3.client('s3')

# configs
app = os.environ['COPILOT_APPLICATION_NAME']
env = os.environ['COPILOT_ENVIRONMENT_NAME']
SCHEMA_VERSION = os.environ['SCHEMA_VERSION']

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='/copilot/applications/'+app+'/'+env +
                              '/public-blockchain-data-s3bucket', WithDecryption=True)
BUCKET = parameter['Parameter']['Value']

# override to copy to other S3 bucket
DEST_BUCKET = ''


def getFiles(bucket, pref):
    files = []
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=pref)
    for page in pages:
        if 'Contents' in page:
            for object in page['Contents']:
                s = object['Key']
                files += [s]
    return files


def processFolder(folderPath):
    destList = getFiles(DEST_BUCKET, folderPath)
    srcList = getFiles(SRC_BUCKET, folderPath)

    aggFilesCopied = False
    for key in srcList:
        filename = os.path.basename(key)
        if filename.endswith(".snappy.parquet") and filename.startswith("part-"):
            print("copy %s from %s to %s" % (key, SRC_BUCKET, DEST_BUCKET))
            copy_object = {'Bucket': SRC_BUCKET, 'Key': key}
            s3_client.copy_object(CopySource=copy_object, Bucket=DEST_BUCKET, Key=key, ACL='bucket-owner-full-control')
            aggFilesCopied = True

    print("aggFilesCopied=%s" % aggFilesCopied)
    if aggFilesCopied:
        for key in destList:
            filename = os.path.basename(key)
            if key not in srcList and filename.endswith(".snappy.parquet"):
                print("delete %s in %s" % (key, DEST_BUCKET))
                s3_client.delete_object(Bucket=DEST_BUCKET, Key=key)


def lambda_handler(event, context):
    d = datetime.date.today()
    d = d+datetime.timedelta(days=-1)
    dStr = '%s-%02d-%02d' % (d.year, d.month, d.day)

    processFolder(SCHEMA_VERSION+'/btc/blocks/date='+dStr)
    processFolder(SCHEMA_VERSION+'/btc/transactions/date='+dStr)

    return {
        'statusCode': 200,
        'body': json.dumps('ok')
    }
