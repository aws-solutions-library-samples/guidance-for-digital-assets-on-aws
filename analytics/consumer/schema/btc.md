# Database btc

This schema follows the table/field structure of the open-source project bitcoin-etl (https://github.com/blockchain-etl/bitcoin-etl).
All data is sourced from Bitcoin Core node (22.0). 

## Table blocks

Stores each block from Bitcoin Blockchain

Field | Type | Description 
--- | --- | ---
date | string | Partition column (YYYY-MM-DD)
hash | string | Hash of this block
size | bigint | The size of block data in bytes
stripped_size | bigint | The size of block data in bytes excluding witness data
weight | bigint | Three times the base size plus the total size
number | bigint | The number of the block     
version | int | Protocol version specified in block header
merkle_root | string | The root node of a Merkle tree, where leaves are transaction hashes
timestamp | timestamp | Block creation timestamp specified in block header
nonce | bigint | Difficulty solution specified in block header
bits | string |  Difficulty threshold specified in block header
coinbase_param | string | Data specified in the coinbase transaction of this block
transaction_count | bigint | Number of transactions included in this block
mediantime | timestamp |
difficulty | double |
chainwork | string |
previousblockhash | string

## Table transactions

Stores each transaction per block, including all inputs and outputs as nested arrays. For easier consumption, input transaction provides more  details about the spending transaction. 

Field | Nested Field | Type | Description 
--- | --- | --- | ---
date | | string | Partition column (YYYY-MM-DD)
hash | | string | The hash of this transaction
size | | bigint | The size of this transaction in bytes
virtual_size | | bigint | The virtual transaction size (differs from size for witness transactions)
version | | bigint | Protocol version specified in block which contained this transaction
lock_time | | bigint | Earliest time that miners can include the transaction in their hashing of the Merkle root to attach it in the latest block of the blockchain
block_hash | | string | Hash of the block which contains this transaction
block_number | | bigint | Number of the block which contains this transaction
block_timestamp | | timestamp | Timestamp of the block which contains this transaction
index | | bigint | The index of the transaction in the block
input_count | | bigint | The number of inputs in the transaction
output_count | | bigint | The number of outputs in the transaction
input_value | | double | Total value of inputs in the transaction (in BTC)
output_value | | double | Total value of outputs in the transaction (in BTC)
is_coinbase | | boolean | True if this transaction is a coinbase transaction
fee | | double | The fee paid by this transaction
inputs | | array | Transaction inputs
inputs | index | bigint | 0 indexed number of an input within a transaction
inputs | spent_transaction_hash | string | The hash of the transaction which contains the output that this input spends
inputs | spend_output_index | bigint | The index of the output this input spends
inputs | script_asm | string | Symbolic representation of the bitcoins script language op-codes
inputs | script_hex | string | Hexadecimal representation of the bitcoins script language op-codes
inputs | sequence | bigint | A number intended to allow unconfirmed time-locked transactions to be updated before being finalized; not currently used except to disable locktime in a transaction
inputs | required_signatures | bigint | The number of signatures required to authorize the spent output
inputs | type | string | The address type of the spent output
inputs | address | string | Address which owns the spent output
inputs | value | double | The value in BTC attached to the spent output
outputs | | array | Transaction outputs
outputs | index | bigint | 0 indexed number of an output within a transaction used by a later transaction to refer to that specific output
outputs | script_asm | string | Symbolic representation of the bitcoins script language op-codes
outputs | script_hex | string | Hexadecimal representation of the bitcoins script language op-codes
outputs | required_signatures | bigint | The number of signatures required to authorize spending of this output
outputs | type | string | The address type of the output
outputs | address | string | Address which owns this output
outputs | value | double | The value in BTC attached to this output

## View inputs

View for all inputs can be created from table transactions with the following statement.

```sql
CREATE OR REPLACE VIEW btc.inputs AS (
  SELECT t.date,t.block_hash,t.block_number,t.block_timestamp,t.hash AS transaction_hash,input.index,input.spent_transaction_hash,input.spend_output_index,input.script_asm,input.script_hex,input.sequence,input.required_signatures,input.type,input.address,input.value FROM btc.transactions t,UNNEST(t.inputs) AS t(input)
)
```

## View outputs

View for all outputs can be created from table transactions with the following statement.

```sql
CREATE OR REPLACE VIEW btc.outputs as (
  SELECT t.date,t.block_hash,t.block_number,t.block_timestamp,t.hash AS transaction_hash,output.index,output.script_asm,output.script_hex,output.required_signatures,output.type,output.address,output.value from btc.transactions t,UNNEST(t.outputs) AS t(output)
)
```