# Producer

## Setup

### 1. Setup of VPC/Subnets
1. Run the following commands:
- Deploy [CF template](scripts/network.yaml) with stack name "public-blockchain-data-network" and specify environment "test"

### 2. Setup of Cloud9 environment
1. Setup Cloud9 with name "copilot-test", instance type "m5.large", platform: "Ubuntu Server 18.04 LTS". In network settings, select VPC "digitalassets-test", select Subnet "test Public Subnet (AZ1)".
2. Install Copilot 
- sudo curl -Lo /usr/local/bin/copilot https://github.com/aws/copilot-cli/releases/download/v1.21.0/copilot-linux && sudo chmod +x /usr/local/bin/copilot
3. Install Python 3.9
- sudo add-apt-repository ppa:deadsnakes/ppa
- sudo apt install python3.9 python3.9-distutils
4. Install Python libs
- sudo python3.9 -m pip install boto3
5. Clone GitHub Repo
- cd ~/environment
- git clone https://github.com/aws-samples/digital-assets-examples.git
- cd digital-assets-examples
6. Add environment variables in ~/.bashrc for application "digital-assets" and environment "test"
- sudo vi ~/.bashrc
- Add below lines to the end of the file
export DIGITAL_ASSETS_HOME=/home/ubuntu/environment/digital-assets-examples
export COPILOT_APPLICATION_NAME=digital-assets
export COPILOT_ENVIRONMENT_NAME=test
- . ~/.bashrc
7. Create new IAM role "Cloud9Role", attach managed policy "AdministratorAccess". Assign Cloud9Role to EC2 Instance Role for Cloud9 environment. Disable "AWS managed temporary credentials" in Cloud 9/AWS Settings.
8. Configure AWS SDK, only specify AWS region.
- aws configure

### 3. Setup of test environment

1. Create copilot application "digital-assets". Please note application needs to be unique per region.
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot
- copilot app init
- Specify "digital-assets" for Application name. 
2. Setup copilot "test" environment and import existing VPC/Subnets from previous step
- copilot env init
- Specify "test" for Application name.

### 4. Setup of S3 bucket

1. Run the following commands:
- cd $DIGITAL_ASSETS_HOME/analytics/producer/scripts/
- ./create_s3_bucket.sh
- ./set_s3_bucket.sh internal

Note: Steps 5 and 6 are only required for Bitcoin

### 5. Setup of Bitcoin Node

1. Configure RPC authentication:
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-node/
- ./init.sh
2. Setup and Deploy service "bitcoin-node" 
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
- copilot svc init --name=bitcoin-node
- copilot svc deploy --name=bitcoin-node
3. Set BTC endpoint to "host:port"
- cd $DIGITAL_ASSETS_HOME/base
- ./set_endpoint.sh bitcoin {rpc-host}:8332 {listener-host}:28332
4. Wait a few days until Bitcoin node has fully synced

### 6. Setup of Bitcoin Worker and Feed

1. If you want to use DynamoDB for the transaction cache to improve import speed, run the following steps. If you don't want to use it, set parameter USE_DYNAMODB to "false in file "$DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/manifest.yml"
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/
- ./init_storage.sh
2. Setup and Deploy service "bitcoin-feed" 
- cd $DIGITAL_ASSETS_HOME/copilot
- copilot svc init --name=bitcoin-feed
- copilot svc deploy --name=bitcoin-feed
3. Setup and Deploy service "bitcoin-worker" 
- Adjust number of workers in file "$DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/manifest.yml" (default: 1, for initial import increase it to 5). 
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot
- copilot svc init --name=bitcoin-worker
- copilot svc deploy --name=bitcoin-worker
4. For initial historical import, run the following steps. 
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/
- nohup python3 import.py &
5. Wait until all historical data has been imported to S3

Note: Steps 7 and 8 are only required for Ethereum

### 7. Setup of Erigon Node

As the current feed requires an Ethereum node that supports batch apis, we'll use an Erigon node. Once this is supported on AMB Ethereum, we switch this to a managed node.

1. Setup [Erigon Node](https://github.com/ledgerwatch/erigon) and wait until node is fully synced. Disable "wss.compression" by adding flag "--wss.compression=false".
2. For the initial import it is recommended to install at least 2 nodes in front of a NLB. You can point the "rpc:host" in the next step to the NLB and designate one of nodes as the "listener-host".
3. Set ETH endpoint to "host:port"
- cd $DIGITAL_ASSETS_HOME/analytics/producer/scripts
- ./set_endpoint.sh ethereum {rpc-host}:8545 {listener-host}:8545

### 8. Setup of Ethereum Worker and Feed

1. Setup and Deploy service "ethereum-feed" 
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot
- copilot svc init --name=ethereum-feed
- copilot svc deploy --name=ethereum-feed
2. Setup and Deploy service "ethereum-worker" 
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot
- Adjust number of workers in file "$DIGITAL_ASSETS_HOME/analytics/producer/copilot/ethereum-worker/manifest.yml" (default: 1, for initial import increase it to 10)
- copilot svc init --name=ethereum-worker
- copilot svc deploy --name=ethereum-worker
3. For initial historical import, run the following steps. 
- cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/ethereum-feed/
- nohup python3 import.py &
4. Wait until all historical data has been imported to S3
