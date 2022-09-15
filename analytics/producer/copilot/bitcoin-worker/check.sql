-- duplicate blocks
select number,date,count(number) from btc.blocks group by number,date having count(number)>1

-- missing blocks
select max(number),min(number),(max(number)-min(number)+1)-count(number) as diff from btc.blocks 

-- check inputs/outputs
select date,block_number from (select distinct date,block_number from btc.transactions where (cardinality(inputs)<>input_count or cardinality(outputs)<>output_count)
) order by date,block_number 

-- check tx count
select a.* from (
select b.date,b.number,b.transaction_count as c1,count(t.hash) as c2 from btc.blocks b left join btc.transactions t on b.number=t.block_number 
group by b.date,b.number,b.transaction_count
order by b.date,b.number
) a where a.c1<>a.c2