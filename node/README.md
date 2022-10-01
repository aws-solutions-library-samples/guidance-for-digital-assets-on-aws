# node

Blog Post "Experimenting with Bitcoin Blockchain on AWS": https://aws.amazon.com/blogs/industries/experimenting-with-bitcoin-blockchain-on-aws/

## Architecture

![chart](architecture.png)

## Setup

For this blog post, follow below steps. We recommend the deployment via Copilot, the CloudFormation deployment is described [here](archive/README.md). 

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
cd $DIGITAL_ASSETS_HOME/node/copilot/
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

### 4. Setup of Bitcoin Node

- Configure RPC authentication:
```sh
cd $DIGITAL_ASSETS_HOME/node/copilot/bitcoin-node/
chmod 777 *.sh
./init.sh
```
- Setup and Deploy service "bitcoin-node" 
```sh
cd $DIGITAL_ASSETS_HOME/node/copilot/
copilot svc init --name=bitcoin-node
copilot svc deploy --name=bitcoin-node
```
- Wait a few days until Bitcoin node has fully synced

### 5. Setup of Electrum Server (optional, only needed for electrum clients)

- Configure SSL certs for "test" environment:
```sh
cd $DIGITAL_ASSETS_HOME/node/copilot/electrum/
chmod 777 *.sh
./init.sh test
```
- Setup and Deploy service "electrum" 
```sh
cd $DIGITAL_ASSETS_HOME/node/copilot/
copilot svc init --name=electrum
copilot svc deploy --name=electrum
```
- Wait a few days until Electrum server has fully synced

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.