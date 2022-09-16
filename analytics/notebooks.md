# AWS Public Blockchain Data - SageMaker Examples

Examples for accessing data from SageMaker Studio / Jupyter Notebooks.

## Instrutions

1. Setup Amazon SageMaker Studio
- Follow the instruction from [here](https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-quick-start.html)
2. Update SageMaker Execution role
- Lookup the default SageMaker Execution role in your SageMaker Studio Domain, it has the following format: **arn:aws:iam::NNN:role/service-role/AmazonSageMaker-ExecutionRole-DDD**
- Add the policy **AWSCloudFormationReadOnlyAccess** and **AWSGlueServiceNotebookRole** to the SageMaker Execution role

With the above setup, you can query AWS Public Blockchain Data from SageMaker Studio.

## Market Data

For the examples that require crypto market data, please run through the following steps first.
1. Deploy CloudFormation Stack for market data S3 bucket and schema: [Deploy Stack](https://console.aws.amazon.com/cloudformation/home?region=us-east-2#/stacks/new?stackName=crypto-marketdata&templateURL=https://aws-blogs-artifacts-public.s3.amazonaws.com/artifacts/DBBLOG-2500/crypto-marketdata.yaml)
2. Run through all the cells of this notebook [Load Market Data](consumer/sagemaker/load-marketdata.ipynb) in SageMaker Studio to pull external market data and store it in your S3 bucket.

## Jupyter Notebooks:

- [Bitcoin Analytics](consumer/sagemaker/btc-analytics.ipynb)
- [Ethereum Analytics](consumer/sagemaker/eth-analytics.ipynb)
- [Cross-Chain Analytics](consumer/sagemaker/cross-chain-analytics.ipynb)