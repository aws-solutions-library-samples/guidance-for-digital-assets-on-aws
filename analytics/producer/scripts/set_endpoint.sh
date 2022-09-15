#!/bin/sh

echo "TOKEN=$1"
echo "ENDPOINT=$2"
echo "LISTENER=$3"

aws ssm put-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/$1-endpoint" --type "String" --value "$2" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"$COPILOT_APPLICATION_NAME\"},{\"Key\":\"copilot-environment\",\"Value\":\"$COPILOT_ENVIRONMENT_NAME\"}]"
aws ssm put-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/$1-listener" --type "String" --value "$3" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"$COPILOT_APPLICATION_NAME\"},{\"Key\":\"copilot-environment\",\"Value\":\"$COPILOT_ENVIRONMENT_NAME\"}]"