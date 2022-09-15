# AWS Public Blockchain Data - Tutorial
Tutorial for accessing data from Redshift 

1. Setup external schema

create external schema eth
from data catalog
database 'eth' 
iam_role 'arn:aws:iam::{account}:role/service-role/{role}
create external database if not exists;

2. Query data

select count(*) from btc.blocks;
select count(*) from btc.transactions;

select count(*) from eth.blocks;
select count(*) from eth.transactions;