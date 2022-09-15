#!/bin/sh

echo "set:/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/bitcoin-node/reindex=$2"
aws ssm put-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/bitcoin-node/reindex" --type "String" --value "$2" --overwrite