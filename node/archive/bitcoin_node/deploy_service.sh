#!/usr/bin/env bash

# This script shows how to build the Docker image and push it to ECR

image=bitcoin_ecr

# Get the account number associated with the current IAM credentials
account=$(aws sts get-caller-identity --query Account --output text)

if [ $? -ne 0 ]
then
    exit 255
fi

# Get the region defined in the current configuration (default to us-west-2 if none defined)
region=$(aws configure get region)
region=${region:-us-east-1}

fullname="${account}.dkr.ecr.${region}.amazonaws.com/${image}:latest"

echo $fullname

SSH_PUBLIC_KEY="`cat ~/.ssh/id_rsa.pub`"
SERVER_CRT="`cat server.crt`"
SERVER_KEY="`cat server.key`"

aws cloudformation deploy --template-file $1 --stack-name bitcoin-service --parameter-overrides ImageUrl=$fullname SSHPublicKey="$SSH_PUBLIC_KEY" ServerCrt="$SERVER_CRT" ServerKey="$SERVER_KEY"
