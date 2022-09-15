import datetime
import os
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


# current date
d = datetime.date.today()
dStr = '%s-%02d-%02d' % (d.year, d.month, d.day)
print('\ndStr=%s\n' % dStr)


def checkFolderFix(s3_path, tableName, schema):
    print("\ncheckFolderFix: %s %s\n" % (s3_path, tableName))
    update = False
    try:
        hasNotParts = False
        hasNewFiles = True
        fileList = []
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET, Prefix=s3_path)
        for page in pages:
            if 'Contents' in page:
                for object in page['Contents']:
                    s = object['Key']
                    file_name = os.path.basename(s)
                    if not file_name.startswith("part-"):
                        hasNotParts = True
                    if not file_name.startswith(tableName+"-"):
                        hasNewFiles = False
                    fileList.append(s)
        print(fileList)
        print("hasNotParts=%s,hasNewFiles=%s" % (hasNotParts, hasNewFiles))

        if (hasNotParts or len(fileList) > 1) and hasNewFiles:
            s3_bucket = 's3://'+BUCKET+'/'
            job = Job(glueContext)

            print("\ncompressFolderGlue: %s\n" % (s3_path))
            job.init(args['JOB_NAME'], args)
            df = glueContext.create_dynamic_frame.from_options(connection_type="parquet", connection_options={
                                                               'path': s3_bucket+s3_path, 'mergeSchema': 'true'})
            df.printSchema()
            df0 = df.toDF()
            partitioned_df = df0.repartition(1)
            partitioned_dynamic_df = DynamicFrame.fromDF(partitioned_df, glueContext, "partitioned_df")
            datasink0 = glueContext.write_dynamic_frame.from_options(
                frame=partitioned_dynamic_df, connection_type="s3", connection_options={'path': s3_bucket+s3_path}, format="parquet")

            job.commit()

            print('delete:%s\n' % len(fileList))
            for y in fileList:
                print(y)
                s3_client.delete_object(Bucket=BUCKET, Key=y)
        else:
            print("folder ok")

    except Exception as e:
        print(e)
    return update


# current date
sDate = datetime.date(2015, 7, 30)
type = "all"

eDate = datetime.date.today()+datetime.timedelta(days=-1)

while sDate <= eDate:
    sDateStr = '%s-%02d-%02d' % (sDate.year, sDate.month, sDate.day)
    print('sDateStr=%s\n' % sDateStr)
    sDate = sDate+datetime.timedelta(days=1)

    if type == "eth" or type == "all":
        checkFolderFix(SCHEMA_VERSION+'/eth/blocks/date='+sDateStr+'/', 'blocks', 'eth')
        checkFolderFix(SCHEMA_VERSION+'/eth/transactions/date='+sDateStr+'/', 'transactions', 'eth')
        checkFolderFix(SCHEMA_VERSION+'/eth/logs/date='+sDateStr+'/', 'logs', 'eth')
        checkFolderFix(SCHEMA_VERSION+'/eth/token_transfers/date='+sDateStr+'/', 'token_transfers', 'eth')
        checkFolderFix(SCHEMA_VERSION+'/eth/traces/date='+sDateStr+'/', 'traces', 'eth')
        checkFolderFix(SCHEMA_VERSION+'/eth/contracts/date='+sDateStr+'/', 'contracts', 'eth')
    elif type == "btc" or type == "all":
        checkFolderFix(SCHEMA_VERSION+'/btc/blocks/date='+sDateStr+'/', 'blocks', 'btc')
        checkFolderFix(SCHEMA_VERSION+'/btc/transactions/date='+sDateStr+'/', 'transactions', 'btc')
