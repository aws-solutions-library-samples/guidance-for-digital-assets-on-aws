# Analytics

This open-source solution pulls data from the public Bitcoin and Ethereum blockchains and normalizes data into tabular data structures for blocks, transactions, and additional tables for data inside a block. The data is provided as parquet files partioned by date to provide an easy query interface through tools like Amazon Athena, Amazon Redshift, and Amazon SageMaker.

## Architecture

![chart](architecture.png)

### How to consume this data from AWS

To consume this data, run the following AWS CloudFormation template in your AWS Account:

[Deploy Stack](https://console.aws.amazon.com/cloudformation/home?region=us-east-2#/stacks/new?stackName=aws-public-blockchain&templateURL=https://aws-blogs-artifacts-public.s3.amazonaws.com/artifacts/DBBLOG-2500/aws-public-blockchain.yaml)
 

### How to setup this solution in your own AWS account 

Follow the instructions from [here](producer/README.md)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.