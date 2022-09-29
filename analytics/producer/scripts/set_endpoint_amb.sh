#!/bin/sh

echo "AMB_ENDPOINT=$1"
aws configure set cli_follow_urlparam false
aws ssm put-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/amb-endpoint" --type "String" --value "$1" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"$COPILOT_APPLICATION_NAME\"},{\"Key\":\"copilot-environment\",\"Value\":\"$COPILOT_ENVIRONMENT_NAME\"}]"