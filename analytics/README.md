# Analytics

This open-source solution pulls data from the public Bitcoin and Ethereum blockchains and normalizes data into tabular data structures for blocks, transactions, and additional tables for data inside a block. The data is provided as parquet files partioned by date to provide an easy query interface through tools like Amazon Athena, Amazon Redshift, and Amazon SageMaker.

## Architecture

![chart](architecture.png)

Go the the relevant section:
- How to consume this data from AWS [here](consumer/README.md)  
- How to setup this solution in your own AWS account [here](producer/README.md)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.