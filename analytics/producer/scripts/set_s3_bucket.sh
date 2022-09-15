#!/bin/sh

if [ "$1" = "internal" ]; then
  echo "set to internal s3 bucket"
  S3_BUCKET=`aws cloudformation list-exports --query "Exports[?Name=='public-blockchain-data-s3bucket'].Value" --output text`
else
  echo "set to public s3 bucket"
  S3_BUCKET='aws-public-blockchain'
fi

echo "set:/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/public-blockchain-data-s3bucket=$S3_BUCKET"
aws ssm put-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/public-blockchain-data-s3bucket" --type "String" --value "$S3_BUCKET" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"$COPILOT_APPLICATION_NAME\"},{\"Key\":\"copilot-environment\",\"Value\":\"$COPILOT_ENVIRONMENT_NAME\"}]"