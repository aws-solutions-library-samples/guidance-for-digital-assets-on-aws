#!/bin/sh

ENV=$1
echo "ENV=$ENV"

# create certs
openssl genrsa -out /tmp/server.key 2048
openssl req -new -key /tmp/server.key -out /tmp/server.csr
openssl x509 -req -days 1825 -in /tmp/server.csr -signkey /tmp/server.key -out /tmp/server.crt

SERVER_CRT=`cat /tmp/server.crt | jq -sR . | sed -e 's/^"//' -e 's/"$//'`
SERVER_KEY=`cat /tmp/server.key | jq -sR . | sed -e 's/^"//' -e 's/"$//'`

echo "SERVER_CRT=$SERVER_CRT"
echo "SERVER_KEY=$SERVER_KEY"

aws secretsmanager create-secret --name "bitcoin/$ENV/electrum" --secret-string "{\"server_crt\":\"$SERVER_CRT\",\"server_key\":\"$SERVER_KEY\"}" --tags "[{\"Key\":\"copilot-application\",\"Value\":\"bitcoin\"},{\"Key\":\"copilot-environment\",\"Value\":\"$ENV\"}]"