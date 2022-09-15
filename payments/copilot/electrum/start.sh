#!/bin/sh

export COIN=Bitcoin
export DB_DIRECTORY=/root/electrum_data/electrumx
export DAEMON_URL=http://$RPC_USER:$RPC_PASSWORD@bitcoin-core.$COPILOT_ENVIRONMENT_NAME.bitcoin.local:8332/
echo "DAEMON_URL=$DAEMON_URL"
export ALLOW_ROOT=true
export SERVICES=ssl://:50002,rpc://
export SSL_CERTFILE=/root/server.crt
export SSL_KEYFILE=/root/server.key
export PEER_DISCOVERY=off

echo "$SERVER_CRT" > /root/server.crt
echo "$SERVER_KEY" > /root/server.key

mkdir /log
## Redirecting Filehanders
ln -sf /proc/$$/fd/1 /log/stdout.log
ln -sf /proc/$$/fd/2 /log/stderr.log

mkdir /root/electrum_data/electrumx

## Pre execution handler
pre_execution_handler() {
  ## Pre Execution
  echo "pre_execution"
}

## Post execution handler
post_execution_handler() {
  ## Post Execution
  echo "post_execution"
  echo "wait 5s"
  sleep 5
  echo "finished"
}

## Sigterm Handler
sigterm_handler() { 
  if [ $pids -ne 0 ]; then
    # the above if statement is important because it ensures 
    # that the application has already started. without it you
    # could attempt cleanup steps if the application failed to
    # start, causing errors.
    kill -15 "$pids"
    wait "$pids"
    post_execution_handler
  fi
  exit 143; # 128 + 15 -- SIGTERM
}

## Setup signal trap
# on callback execute the specified handler
trap 'sigterm_handler' TERM

## Initialization
pre_execution_handler

## Start Process
# run process in background and record PID
pids=""
RESULT=0

echo "start electrumx"
/root/electrumx/electrumx_server &
pids="$pids $!"

## Wait until one app dies
for pid in $pids; do
    wait $pid || let "RESULT=1"
done
if [ "$RESULT" == "1" ];
    then
       exit 1
fi
return_code="$?"

## Cleanup
post_execution_handler
# echo the return code of the application
exit $return_code