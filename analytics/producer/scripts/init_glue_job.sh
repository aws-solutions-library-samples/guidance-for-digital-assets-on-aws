#!/bin/sh

S3_BUCKET=`aws ssm get-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/public-blockchain-data-s3bucket" | jq -r '.Parameter | .Value'`
echo "S3_BUCKET:$S3_BUCKET"

aws cloudformation deploy --template-file=glue_job.yaml --parameter-overrides "s3_bucket=$S3_BUCKET" --stack-name=public-blockchain-data-glue --capabilities=CAPABILITY_IAM

export S3_BUCKET_GLUE=`aws cloudformation list-exports --query "Exports[?Name=='public-blockchain-data-glue-s3bucket'].Value" --output text`
echo $S3_BUCKET_GLUE
aws s3 cp glue/daily_glue_job.py s3://$S3_BUCKET_GLUE/