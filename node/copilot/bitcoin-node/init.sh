#!/bin/sh

wget -O /tmp/rpcauth.py https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py

# bitcoind rpcauth
export RPCUSERNAME='bitcoinrpc'
python3 /tmp/rpcauth.py $RPCUSERNAME > /tmp/rpc.txt
export RPCPASSWORD=`cat /tmp/rpc.txt | tail -n 1`
export RPCAUTH=`cat /tmp/rpc.txt | grep rpcauth | cut -d '=' -f2`

echo "RPCUSERNAME=$RPCUSERNAME"
echo "RPCPASSWORD=$RPCPASSWORD"
echo "RPCAUTH=$RPCAUTH"

aws secretsmanager create-secret --name "$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/bitcoin-node" --secret-string "{\"rpc_user\":\"$RPCUSERNAME\",\"rpc_password\":\"$RPCPASSWORD\",\"rpc_auth\":\"$RPCAUTH\"}" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"$COPILOT_APPLICATION_NAME\"},{\"Key\":\"copilot-environment\",\"Value\":\"$COPILOT_ENVIRONMENT_NAME\"}]"
aws ssm put-parameter --name "/copilot/applications/$COPILOT_APPLICATION_NAME/$COPILOT_ENVIRONMENT_NAME/bitcoin-node/reindex" --type "String" --value "None" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"$COPILOT_APPLICATION_NAME\"},{\"Key\":\"copilot-environment\",\"Value\":\"$COPILOT_ENVIRONMENT_NAME\"}]"