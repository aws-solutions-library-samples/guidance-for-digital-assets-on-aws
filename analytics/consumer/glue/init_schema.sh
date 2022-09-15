#!/bin/sh

S3_BUCKET=`aws ssm get-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/public-blockchain-data-s3bucket" | jq -r '.Parameter | .Value'`
echo "s3bucket=${S3_BUCKET}" 

aws cloudformation deploy --template-file=schema.yaml --parameter-overrides "s3bucket=${S3_BUCKET}" --stack-name=public-blockchain-data-schema --capabilities=CAPABILITY_IAM