## Digital Assets Examples

This repo contains AWS examples for digital assets use cases.  


### Setup of Bitcoin Full Node and Electrum Server

1. Setup Cloud9 IDE with instance type  "t3.medium"
2. Run the following commands in Cloud9 Terminal window:
* cd ~/environments
* git clone https://github.com/aws-samples/digital-assets-examples.git
* cd digital-assets-examples/bitcoin_node
* openssl genrsa -out server.key 2048
* openssl req -new -key server.key -out server.csr
* openssl x509 -req -days 1825 -in server.csr -signkey server.key -out server.crt
* sam build --template-file template.yaml
* sam deploy --guided --template-file template.yaml # specify bitcoin-app as Stack name
* ./deploy_image.sh
* ssh-keygen -t rsa
* ./deploy_service.sh node-service.yaml

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

