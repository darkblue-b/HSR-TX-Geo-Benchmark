HSR-Texas-Geo-Database-Benchmark
================================

This is a proposal for a spatial database benchmark from the University of Applied Sciences Rapperswil (HSR). A study of existing database benchmarks revealed that there exists no information publicly available which compares spatial database systems regarding their performance. Spatial 'database management systems' (DMBS) typically form the persistence layer of a geographic information system (GIS).
Thus the Institute for Software at the University of Applied Sciences Rapperswil (HSR) decided to propose such a benchmark. This benchmark is being called 'The HSR Texas Spatial Database Benchmark' because it was defined from a HSR institute and because data comes from Texas USA.
The benchmark is based on a predefined set of queries. These queries consist of simple spatial queries, defined in the OpenGIS(tm) 'Simple Features Interface Standard (SFS)'. The queries are performed on different-sized data sets for monitoring the behavior on various loads as well as on different hardware systems.
In the following sections the methodology, the queries are explained and the used datasets are defined. This proposal concludes with a Call for Comments about the benchmark as well as a Call for Participation to apply and test this benchmark on existing DBMS software.

Read more at http://giswiki.hsr.ch/HSR_Texas_Geo_Database_Benchmark

Download the texas test data at https://www.dropbox.com/sh/9stif43l95t21do/ZoU2Gtdw0n


### Update May 2014 -dbb

#### Benchmark updated
+ PostgreSQL 9.2+ / PostGIS 2.1+ / GEOS 3.4.2
+ Solr 4.8.0 / Java OpenJDK 1.7 / spatial4j 0.4.1
+ Spatialite 4.1.0 / GEOS 3.4.2


