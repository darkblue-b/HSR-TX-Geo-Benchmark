import benchmark

class Benchmark(benchmark.Benchmark):
    def setUpClass(self):
        print >>self.out, "DROP TABLE IF EXISTS benchmark_results;";
        
        print >>self.out, """CREATE TEMPORARY TABLE benchmark_results(
          key VARCHAR(255) PRIMARY KEY,
          duration INTERVAL(6)
        );"""
        
        print >>self.out, """CREATE TEMPORARY TABLE benchmark_temptimestamps(
          key TEXT PRIMARY KEY,
          value TIMESTAMP
        );"""
    
        ##-- no longer needed for PostGIS 2.0+
        if False:
            print >>self.out, """DROP FUNCTION IF EXISTS benchmark_addgeoconstraints(VARCHAR(255));
        CREATE OR REPLACE FUNCTION benchmark_addgeoconstraints(in_table VARCHAR(255)) RETURNS VOID AS $$
        DECLARE
          geotype TEXT;
        BEGIN
          EXECUTE 'SELECT GeometryType(geom) FROM ' || quote_ident(in_table) || ' LIMIT 1;' INTO geotype;
          EXECUTE 'ALTER TABLE ' || quote_ident(in_table) || ' ADD CONSTRAINT enforce_dims_the_geom CHECK(ST_NDims(geom) = 2);';     
          EXECUTE 'ALTER TABLE ' || quote_ident(in_table) || ' ADD CONSTRAINT enforce_geotype_the_geom CHECK(GeometryType(geom) = ' || quote_literal(geotype) || '::text OR geom IS NULL);';
          EXECUTE 'ALTER TABLE ' || quote_ident(in_table) || ' ADD CONSTRAINT enforce_srid_the_geom CHECK(ST_SRID(geom) = 4326);';
          SELECT Probe_Geometry_Columns();
          RETURN;
        END
        $$ LANGUAGE 'plpgsql';"""

    def printResults(self):
        print >>self.out, "SELECT * FROM benchmark_results";

    def loadData(self, sourcetable, targettable, bbox):
        print >>self.out, " DROP TABLE IF EXISTS {targettable} cascade;".format(targettable=targettable);
        print >>self.out, """CREATE TABLE {targettable} AS
            SELECT * FROM {sourcetable}
            WHERE ST_Intersects(ST_SetSRID({bbox}, 4326), geom);""".format(targettable=targettable, sourcetable=sourcetable, bbox=bbox)

        print >>self.out, "ALTER TABLE {table} ADD PRIMARY KEY (gid);".format(table=targettable)

        # checking the constraints for every single row is *really* slow
        #print >>self.out, "SELECT benchmark_addgeoconstraints({table});".format(table=targettable);

        print >>self.out, "CREATE INDEX idx_{table}_the_geom ON {table} USING gist (geom);".format(table=targettable);
        print >>self.out, "CREATE INDEX idx_{table}_32614_geom ON {table} USING gist( st_transform(geom,32614));".format(table=targettable);

    def createIndex(self, table, column):
        print >>self.out, "CREATE INDEX idx_{table}_{column} ON {table}({column});".format(table=table, column=column)

    def startTimer(self, description):
        print >>self.out, "DELETE FROM benchmark_temptimestamps WHERE key='start';"
        print >>self.out, "DELETE FROM benchmark_results WHERE key='{key}';".format(key=description)
        print >>self.out, "INSERT INTO benchmark_temptimestamps (key, value) VALUES ('start', clock_timestamp());"
    
    def stopTimer(self, description):
        print >>self.out, "INSERT INTO benchmark_results (key, duration) VALUES ('{key}', clock_timestamp()-(SELECT value FROM benchmark_temptimestamps WHERE key='start'));".format(key=description)

    def nonspatial(self, table):
        print >>self.out, "SELECT count(*) FROM {table} WHERE roadflg='Y';".format(table=table)

    def intersectbb(self, table, bbox):
        print >>self.out, """SELECT count(*) FROM {table}
            WHERE ST_Intersects(ST_SetSRID({bbox}, 4326), geom);""".format(table=table, bbox=bbox)

    def distance_geom0(self, table, point, distance):
        print >>self.out, """SELECT count(*) FROM {table}
            WHERE geom && ST_Transform(ST_Expand(ST_Transform(ST_SetSRID({point}, 4326), 32614), {distance}), 4326)
            AND ST_Distance(ST_Transform(ST_SetSRID({point}, 4326), 32614), ST_Transform(geom, 32614)) <= {distance};""".format(table=table, point=point, distance=distance)

    def distance_geog(self, table, point, distance):
        print >>self.out, """SELECT count(*) FROM {table}
            WHERE ST_Dwithin( geog, {point}, {distance} )
        """.format(table=table, point=point, distance=distance)

    def distance(self, table, point, distance):
        print >>self.out, """
          SELECT 
            count(*) FROM {table}
          WHERE 
            ST_Dwithin( 
              st_transform(geom, 32614), 
              st_transform(ST_SetSRID( {point}, 4326),32614), 
              {distance} );
        """.format(table=table, point=point, distance=distance)


    def intersectlines(self, table):
        print >>self.out, """SELECT count(*) FROM {table} e, areawater a
            WHERE ST_Intersects(e.geom, a.geom) AND e.railflg = 'Y';""".format(table=table)

    def makeBox(self, pointLL, pointUR):
        return "ST_MakeBox2D(ST_MakePoint({xLL}, {yLL}), ST_MakePoint({xUR}, {yUR}))".format(xLL=pointLL[0], yLL=pointLL[1], xUR=pointUR[0], yUR=pointUR[1])
    
    def makePoint(self, point):
        return "ST_MakePoint({x}, {y})".format(x=point[0], y=point[1])
