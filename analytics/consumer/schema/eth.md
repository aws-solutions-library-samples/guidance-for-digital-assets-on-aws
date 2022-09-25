# Database eth

This schema follows the table/field structure of the open-source project ethereum-etl (https://github.com/blockchain-etl/ethereum-etl).

All data is sourced from Erigon node (v2022.09.03) with Lighthouse (v3.1.0) CL. 

Currently new data is delivered in each table folder every night ~01:45 am UTC as one Parquet file per day "part-NNNNN-*.snappy.parquet". Depending on feedback, intraday files can be provided.

## Table blocks

This table captures all blocks.

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
timestamp | timestamp | The unix timestamp for when the block was collated
number | bigint | The block number
hash | string | Hash of the block
parent_hash | string | Hash of the parent block
nonce | string | Hash of the generated proof-of-work
sha3_uncles | string | SHA3 of the uncles data in the block
logs_bloom | string | The bloom filter for the logs of the block
transactions_root | string | The root of the transaction trie of the block
state_root | string | The root of the final state trie of the block
receipts_root | string | The root of the receipts trie of the block
miner | string | The address of the beneficiary to whom the mining rewards were given
difficulty | double | Difficulty for this block
total_difficulty | double | Total difficulty of the chain until this block
size | bigint | The size of this block in bytes
extra_data | string | The “extra data” field of this block
gas_limit | bigint | The maximum gas allowed in this block
gas_used | bigint | The total used gas by all transactions in this block
transaction_count | bigint | Number of transactions in this block
base_fee_per_gas | bigint | Minimum to be charged to send a transaction on the network

## Table transactions

This table captures all transactions for a block.

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
hash | string | Hash of the transaction
nonce | bigint | The number of transactions made by the sender prior to this one
transaction_index | bigint | Integer of the transactions index position in the block
from_address | string | Address of the sender
to_address | string | Address of the receiver
value | double | Value transferred in wei      
gas | bigint | Gas price provided by the sender in wei       
gas_price | bigint | Gas provided by the sender
input | string | The data sent along with the transaction
receipt_cumulative_gas_used | bigint | The total amount of gas used when this transaction was executed in the block
receipt_gas_used | bigint | The amount of gas used by this specific transaction alone
receipt_contract_address | string | The contract address created, if the transaction was a contract creation
receipt_status | bigint | if the transaction was successful
block_timestamp | timestamp | The unix timestamp for when the block was collated
block_number | bigint | Block number where this transaction was in
block_hash | string | Hash of the block
max_fee_per_gas | bigint | Total fee that covers both base and priority fees
max_priority_fee_per_gas | bigint | Fee given to miners to incentivize them to include the transaction
transaction_type | bigint | Transaction type
receipt_effective_gas_price | bigint | The actual value per gas deducted from the senders account.

## Table token_transfers

This table captures ERC-20 token transfers.

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
token_address | string | Uniqye token address
from_address | string | Sender address
to_address | string | Recipient address
value | double | Amount of token
transaction_hash | string | Transaction hash of the block
log_index | bigint | Logs index position in the transaction
block_timestamp | timestamp | The unix timestamp for when the block was collated
block_number | bigint | Block number where this transaction was in
block_hash | string | Hash of the block

## Table logs

This table captures all logs for a transaction.

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
log_index | bigint | Logs index position in the transaction
transaction_hash | string | Transaction hash of the block
transaction_index | bigint | Transactions index position in the block
address | string | Address from which this log originated
data | string | Contains one or more 32 Bytes non-indexed arguments of the log
topics | array | Indexed log arguments 
block_timestamp | timestamp | The unix timestamp for when the block was collated
block_number | bigint | Block number where this transaction was in
block_hash | string | Hash of the block

## Table traces

This table captures all traces for a transaction.

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
transaction_hash | string | Transaction hash of the block
transaction_index | bigint | Transactions index position in the block
from_address | string | Address of the sender
to_address | string | Address of the receiver
value | double | Value transferred
input | string | The data sent along with the message call
output | string | The output of the message call, bytecode of contract when trace_type is create
trace_type | string | Trace type
call_type | string | Call type
reward_type | string | Reward type
gas | bigint | Gas provided with the message call
gas_used | bigint | Gas used by the message call
subtraces | bigint | Number of subtraces
trace_address | string | list of trace address in call tree
error | string | Error if message call failed
status | bigint | Either 1 (success) or 0 (failure)
block_timestamp | timestamp | The unix timestamp for when the block was collated
block_number | bigint | Block number where this transaction was in
block_hash | string | Hash of the block
trace_id | string | Unique syncthetic trace_id

## Table contracts

This table captures all contracts in a block.

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
address | string | Address of the contract
bytecode | string | Bytecode of the contract
block_timestamp | timestamp | The unix timestamp for when the block was collated
block_number | bigint | Block number where this transaction was in
block_hash | string | Hash of the block