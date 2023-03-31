# Producer

## Setup

### 1. Setup of VPC/Subnets
- Deploy [CF template](scripts/network.yaml) with stack name "public-blockchain-data-network" and specify environment "test"

### 2. Setup of Cloud9 environment
- Setup Cloud9 with name "copilot-test", instance type "m4.large" or similar, platform: "Ubuntu Server 18.04 LTS". In network settings, select VPC "digitalassets-test", select Subnet "test Public Subnet (AZ1)".
- Install Copilot 
```sh
sudo curl -Lo /usr/local/bin/copilot https://github.com/aws/copilot-cli/releases/download/v1.21.0/copilot-linux && sudo chmod +x /usr/local/bin/copilot
```
- Install other libs
```sh
sudo apt-get install jq
```
- Install Python 3.9
```sh
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9 python3.9-distutils
```
- Install Python libs
```sh
sudo python3.9 -m pip install boto3
```
- Clone GitHub Repo
```sh
cd ~/environment
git clone https://github.com/aws-samples/digital-assets-examples.git
cd digital-assets-examples
```
- Add environment variables in ~/.bashrc for application "digital-assets" and environment "test"
```sh
sudo vi ~/.bashrc
```
- Add below lines to the end of the file
```sh
export DIGITAL_ASSETS_HOME=/home/ubuntu/environment/digital-assets-examples
export COPILOT_APPLICATION_NAME=digital-assets
export COPILOT_ENVIRONMENT_NAME=test
```
```sh
source ~/.bashrc
```
- Create new IAM role "Cloud9Role", attach managed policy "AdministratorAccess". Assign Cloud9Role to EC2 Instance Role for Cloud9 environment. Disable "AWS managed temporary credentials" in Cloud 9/AWS Settings.
- Configure AWS SDK, only specify AWS region.
```sh
aws configure
```

### 3. Setup of test environment

- Create copilot application "digital-assets". Please note application needs to be unique per region.
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
copilot app init
```
- Specify "digital-assets" for Application name.

- Setup copilot "test" environment and import existing VPC/Subnets from previous step
```sh
copilot env init
```
- Specify "test" for Application name.
```sh
copilot env deploy --name test
```

### 4. Setup of S3 bucket

- Run the following commands:
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/scripts/
chmod +x *.sh
./create_s3_bucket.sh
./set_s3_bucket.sh internal
```

Note: Steps 5 and 6 are only required for Bitcoin

### 5. Setup of Bitcoin Node

- Configure RPC authentication:
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-node/
chmod 777 *.sh
./init.sh
```
- Setup and Deploy service "bitcoin-node" 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
copilot svc init --name=bitcoin-node
copilot svc deploy --name=bitcoin-node
```
- Set BTC endpoint to "host:port"
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/scripts/
chmod 777 *.sh
./set_endpoint.sh bitcoin {rpc-host}:8332 {listener-host}:28332
```
- Wait a few days until Bitcoin node has fully synced

### 6. Setup of Bitcoin Worker and Feed

- If you want to use DynamoDB for the transaction cache to improve import speed, run the following steps. If you don't want to use it, set parameter USE_DYNAMODB to "false in file "$DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/manifest.yml"
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/
chmod 777 *.sh
./init_storage.sh
```
- Setup and Deploy service "bitcoin-feed" 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
copilot svc init --name=bitcoin-feed
copilot svc deploy --name=bitcoin-feed
```
- Setup and Deploy service "bitcoin-worker" 
- Adjust number of workers in file "$DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/manifest.yml" (default: 1, for initial import increase it to 5). 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
copilot svc init --name=bitcoin-worker
copilot svc deploy --name=bitcoin-worker
```
- For initial historical import, run the following steps. 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/bitcoin-worker/
python3 import.py
```
- Wait until all historical data has been imported to S3

Note: Steps 7 and 8 are only required for Ethereum

### 7. Setup of Erigon Node

As the current feed requires an Ethereum node that supports batch apis, we'll use an Erigon node. Once this is supported on AMB Ethereum, we switch this to a managed node.

- Setup [Erigon Node](https://github.com/ledgerwatch/erigon) and wait until node is fully synced. Disable "wss.compression" by adding flag "--wss.compression=false".
- For the initial import it is recommended to install at least 2 nodes in front of a NLB. You can point the "rpc:host" in the next step to the NLB and designate one of nodes as the "listener-host".
- Set ETH endpoint to "host:port" for Erigon node
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/scripts/
chmod 777 *.sh
./set_endpoint.sh ethereum {rpc-host}:8545 {listener-host}:8545
```
- Set https endpoint for AMB Ethereum node (optional, partially supported)
```sh
./set_endpoint_amb.sh {https-endpoint-url}
```

### 8. Setup of Ethereum Worker and Feed

- Setup and Deploy service "ethereum-feed" 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
copilot svc init --name=ethereum-feed
copilot svc deploy --name=ethereum-feed
```
- Setup and Deploy service "ethereum-worker" 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/
```
- Adjust number of workers in file "$DIGITAL_ASSETS_HOME/analytics/producer/copilot/ethereum-worker/manifest.yml" (default: 1, for initial import increase it to 10)
```sh
copilot svc init --name=ethereum-worker
copilot svc deploy --name=ethereum-worker
```
- For initial historical import, run the following steps. 
```sh
cd $DIGITAL_ASSETS_HOME/analytics/producer/copilot/ethereum-feed/
python3 import.py
```
- Wait until all historical data has been imported to S3
