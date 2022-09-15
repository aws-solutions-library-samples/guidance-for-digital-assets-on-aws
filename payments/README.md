# Payments

Blog Post "Experimenting with Bitcoin Blockchain on AWS": https://aws.amazon.com/blogs/industries/experimenting-with-bitcoin-blockchain-on-aws/

## Architecture

![chart](architecture.png)

## Setup

For this blog post, follow below steps. We recommend the deployment via Copilot, the CloudFormation deployment is described [here](archive/README.md). 

### 1. Setup of VPC/Subnets
1. Run the following commands:
- Deploy [CF template](scripts/network.yaml) with stack name "payments-network" and specify environment "test"

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
- cd $DIGITAL_ASSETS_HOME/payments/copilot
- copilot app init
- Specify "digital-assets" for Application name. 
2. Setup copilot "test" environment and import existing VPC/Subnets from previous step
- copilot env init
- Specify "test" for Application name.

### 3. Setup of Bitcoin Node

1. Configure RPC authentication for "test" environment:
- cd $DIGITAL_ASSETS_HOME/payments/copilot/bitcoin-node
- ./init.sh test
2. Setup and Deploy service "bitcoin-node" 
- cd $DIGITAL_ASSETS_HOME/payments/copilot
- copilot svc init --name=bitcoin-node
- copilot svc deploy --name=bitcoin-node
3. Wait a few days until Bitcoin node has fully synced

### 4. Setup of Electrum Server

1. Configure SSL certs for "test" environment:
- cd $DIGITAL_ASSETS_HOME/payments/copilot/electrum
- ./init.sh test
2. Setup and Deploy service "electrum" 
- cd $DIGITAL_ASSETS_HOME/payments//copilot
- copilot svc init --name=electrum
- copilot svc deploy --name=electrum
3. Wait a few days until Electrum server has fully synced

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.