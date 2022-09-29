-- duplicate blocks
select distinct date,count(number) from eth.blocks group by number,date having count(number)>1 order by date

-- missing blocks
select max(number),min(number),(max(number)-min(number)+1)-count(number) as diff from eth.blocks 

-- check tx count
select distinct a.date from (
select b.date,b.number,b.transaction_count as c1,count(t.hash) as c2 from eth.blocks b left join eth.transactions t on b.number=t.block_number
group by b.date,b.number,b.transaction_count
) a where a.c1<>a.c2 order by a.date