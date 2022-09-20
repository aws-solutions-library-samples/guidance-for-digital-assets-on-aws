## Digital Assets Examples

Blog Post "Experimenting with Bitcoin Blockchain on AWS": https://aws.amazon.com/blogs/industries/experimenting-with-bitcoin-blockchain-on-aws/

## CloudFormation deployment (archived)

### Setup of Bitcoin Node and Electrum Server

- Setup Cloud9 IDE with instance type "t3.medium"
- Run the following commands in Cloud9 Terminal window:
```sh
cd ~/environments
git clone https://github.com/aws-samples/digital-assets-examples.git
cd digital-assets-examples/archive/bitcoin_node/
```
- Setup SSL certificate
```sh
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 1825 -in server.csr -signkey server.key -out server.crt
```
- Deploy template and specify ***bitcoin-app*** as stack name
```sh
sam build --template-file template.yaml
sam deploy --guided --template-file template.yaml
./deploy_image.sh
```
- Setup SSK key
```sh
ssh-keygen -t rsa
```
- Deploy node
```sh
./deploy_service.sh node-service.yaml
```
- Wait for sync of bitcoin core and electrum