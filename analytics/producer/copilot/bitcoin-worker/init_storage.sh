#!/bin/sh
aws cloudformation deploy --template-file=storage.yaml --stack-name=bitcoin-worker-storage --capabilities=CAPABILITY_IAM