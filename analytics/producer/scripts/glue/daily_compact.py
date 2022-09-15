import datetime
import sys

import awswrangler as wr
import boto3
import pyspark.sql.functions as psf
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import Window

# @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

s3_client = boto3.client('s3')

# configs
app = os.environ['COPILOT_APPLICATION_NAME']
env = os.environ['COPILOT_ENVIRONMENT_NAME']
SCHEMA_VERSION = os.environ['SCHEMA_VERSION']

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='/copilot/applications/'+app+'/'+env +
                              '/public-blockchain-data-s3bucket', WithDecryption=True)
BUCKET = parameter['Parameter']['Value']


def compactFolder(s3_path, checkTable, schema):
    aList = []
    hasNotParts = False
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET, Prefix=s3_path)
    pCount = 0
    for page in pages:
        if 'Contents' in page:
            for object in page['Contents']:
                pref = object['Key']
                aList.append(pref)
                fName = pref.split('/')[-1:][0]
                if not fName.startswith('part-'):
                    hasNotParts = True
                else:
                    pCount = pCount+1
    if hasNotParts:
        job = Job(glueContext)
        # repartition files
        s3_bucket = 's3://'+BUCKET+'/'

        print("compressFolderGlue: %s\n" % (s3_path))
        job.init(args['JOB_NAME'], args)
        df = glueContext.create_dynamic_frame.from_options(connection_type="parquet", connection_options={
                                                           'path': s3_bucket+s3_path, 'mergeSchema': 'true'})
        partitioned_df = df.toDF().repartition(1)
        partitioned_dynamic_df = DynamicFrame.fromDF(partitioned_df, glueContext, "partitioned_df")

        datasink0 = glueContext.write_dynamic_frame.from_options(
            frame=partitioned_dynamic_df, connection_type="s3", connection_options={'path': s3_bucket+s3_path}, format="parquet")
        job.commit()

        print('delete:%s\n' % len(aList))
        for y in aList:
            print(y)
            s3_client.delete_object(Bucket=BUCKET, Key=y)


sDate = datetime.date.today()+datetime.timedelta(days=-1)
print("sDate=%s" % sDate)

sDateStr = '%s-%02d-%02d' % (sDate.year, sDate.month, sDate.day)
print('sDateStr=%s\n' % sDateStr)

type = "all"
if type == "eth" or type == "all":
    compactFolder(SCHEMA_VERSION+'/eth/blocks/date='+sDateStr+'/', 'blocks', 'eth')
    compactFolder(SCHEMA_VERSION+'/eth/transactions/date='+sDateStr+'/', 'transactions', 'eth')
    compactFolder(SCHEMA_VERSION+'/eth/logs/date='+sDateStr+'/', 'logs', 'eth')
    compactFolder(SCHEMA_VERSION+'/eth/token_transfers/date='+sDateStr+'/', 'token_transfers', 'eth')
    compactFolder(SCHEMA_VERSION+'/eth/traces/date='+sDateStr+'/', 'traces', 'eth')
    compactFolder(SCHEMA_VERSION+'/eth/contracts/date='+sDateStr+'/', 'contracts', 'eth')
elif type == "btc" or type == "all":
    compactFolder(SCHEMA_VERSION+'/btc/blocks/date='+sDateStr+'/', 'blocks', 'btc')
    compactFolder(SCHEMA_VERSION+'/btc/transactions/date='+sDateStr+'/', 'transactions', 'btc')
