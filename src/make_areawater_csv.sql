copy
( SELECT 
    gid as "FID",
    statefp as "STATEFP", 
    countyfp as "COUNTYFP", 
    ansicode as "ANSICODE", 
    hydroid as "HYDROID", 
    fullname as "FULLNAME", 
    mtfcc as "MTFCC", 
    st_astext(geom) as "geom", 
    '-' as "text"
FROM areawater) to '/home/shared/hsr_tx_areawater.csv'
 with CSV header delimiter E';';

-- curl 'http://localhost:8983/solr/hsr_areawater/update/?commit=true&separator=;&escape=\&stream.file=/home/shared/geodata_misc/HSR_Texas_Geo_benchmark_data/hsr_tx_areawater_part0.csv&stream.contentType=text/csv;charset=utf-8&trim=false'
--
