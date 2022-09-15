import json
import boto3
import urllib.parse
import os
import datetime

s3_client = boto3.client('s3')

# configs
SCHEMA_VERSION = os.environ['SCHEMA_VERSION']

# override to copy to other S3 bucket
DEST_BUCKET = ''


def lambda_handler(event, context):
    for record in event['Records']:
        # print(record)
        try:
            source_bucket = record['s3']['bucket']['name']
            source_key = urllib.parse.unquote_plus(
                record['s3']['object']['key'], encoding='utf-8')
            source_file_name = os.path.basename(source_key)
            print("source=%s : %s" % (source_bucket, source_key))

            d = datetime.date.today()
            dStr = '%s-%02d-%02d' % (d.year, d.month, d.day)
            d = d+datetime.timedelta(days=-1)
            dPrevStr = '%s-%02d-%02d' % (d.year, d.month, d.day)
            #print('dStr=%s,dPrevStr=%s' % (dStr,dPrevStr))

            if not source_file_name.startswith('part-') and source_file_name.endswith('.snappy.parquet') and source_key.startswith(SCHEMA_VERSION+'/btc/') and (('/date='+dStr+'/') in source_key or ('/date='+dPrevStr+'/') in source_key):
                print("copy to %s" % DEST_BUCKET)
                copy_object = {'Bucket': source_bucket, 'Key': source_key}
                # write copy statement
                s3_client.copy_object(CopySource=copy_object, Bucket=DEST_BUCKET, Key=source_key)

        except Exception as e:
            print(e)

    return {
        'statusCode': 200,
        'body': json.dumps('ok')
    }
