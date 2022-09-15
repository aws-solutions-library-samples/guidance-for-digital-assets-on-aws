## Digital Assets Examples

Blog Post "Experimenting with Bitcoin Blockchain on AWS": https://aws.amazon.com/blogs/industries/experimenting-with-bitcoin-blockchain-on-aws/

## CloudFormation deployment (archived)

### 1. Setup of Bitcoin Node and Electrum Server

1. Setup Cloud9 IDE with instance type "t3.medium"
2. Run the following commands in Cloud9 Terminal window:
- cd ~/environments
- git clone https://github.com/aws-samples/digital-assets-examples.git
- cd digital-assets-examples/archive/bitcoin_node
- Setup SSL certificate
    - openssl genrsa -out server.key 2048
    - openssl req -new -key server.key -out server.csr
    - openssl x509 -req -days 1825 -in server.csr -signkey server.key -out server.crt
- sam build --template-file template.yaml
- sam deploy --guided --template-file template.yaml # specify bitcoin-app as Stack name
- ./deploy_image.sh
- Setup SSK key
    - ssh-keygen -t rsa
- ./deploy_service.sh node-service.yaml
3. Wait for sync of bitcoin core and electrum