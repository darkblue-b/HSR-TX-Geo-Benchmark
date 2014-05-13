import benchmark

class Benchmark(benchmark.Benchmark):

    def setUpClass(self):
        print >>self.out, "DROP TABLE IF EXISTS benchmark_results;";
        print >>self.out, """CREATE TEMPORARY TABLE benchmark_results(
          key TEXT PRIMARY KEY,
          duration REAL
        );"""
        
        print >>self.out, "DROP TABLE IF EXISTS benchmark_tempstrings;";
        print >>self.out, """CREATE TEMPORARY TABLE benchmark_tempstrings(
          key TEXT PRIMARY KEY,
          value TEXT
        );"""
        
        print >>self.out, "DROP TABLE IF EXISTS benchmark_tempreals;";
        print >>self.out, """CREATE TEMPORARY TABLE benchmark_tempreals(
          key TEXT PRIMARY KEY,
          value REAL
        );"""

    def printResults(self):
        print >>self.out, "SELECT key, duration*24*60*60 AS seconds FROM benchmark_results;";

    def loadData(self, sourcetable, targettable, bbox):        
        print >>self.out, "DROP TABLE IF EXISTS {targettable};".format(targettable=targettable);
        print >>self.out, """CREATE TABLE {targettable} AS
            SELECT * FROM {sourcetable}
            WHERE Intersects(SetSRID({bbox}, 4326), Geometry)
            AND ROWID IN (SELECT pkid FROM idx_{sourcetable}_Geometry WHERE
                xmin < MbrMaxX(SetSRID({bbox}, 4326)) AND
                xmax > MbrMinX(SetSRID({bbox}, 4326)) AND
                ymin < MbrMaxY(SetSRID({bbox}, 4326)) AND
                ymax > MbrMinY(SetSRID({bbox}, 4326))
            );""".format(targettable=targettable, sourcetable=sourcetable, bbox=bbox)
    
        # adding constraints to an existing table is not supported in sqlite
        print >>self.out, "CREATE UNIQUE INDEX idx_{table}_gid ON {table}(PK_UID);".format(table=targettable)
        
        print >>self.out, "INSERT OR REPLACE INTO benchmark_tempstrings (key, value) VALUES ('geotype', (SELECT GeometryType(Geometry) FROM {table} LIMIT 1));".format(table=targettable) 
        print >>self.out, "SELECT RecoverGeometryColumn('{table}', 'Geometry', 4326, (SELECT value FROM benchmark_tempstrings WHERE key='geotype'), 2);".format(table=targettable)
      
        print >>self.out, "SELECT CreateSpatialIndex('{table}', 'Geometry');".format(table=targettable);

    def createIndex(self, table, column):
        print >>self.out, "CREATE INDEX idx_{table}_{column} ON {table}({column});".format(table=table, column=column)    
    
    def startTimer(self, description):
        print >>self.out, "INSERT OR REPLACE INTO benchmark_tempreals (key, value) VALUES ('start', julianday('now'));"
    
    def stopTimer(self, description):
        print >>self.out, "INSERT OR REPLACE INTO benchmark_results (key, duration) VALUES ('{key}', julianday('now')-(SELECT value FROM benchmark_tempreals WHERE key='start'));".format(key=description)        

    def nonspatial(self, table):
        print >>self.out, "SELECT count(*) FROM {table} WHERE roadflg='Y';".format(table=table)

    def intersectbb(self, table, bbox):
        print >>self.out, """SELECT count(*) FROM {table}
            WHERE Intersects(SetSRID({bbox}, 4326), Geometry)
            AND ROWID IN (SELECT pkid FROM idx_{table}_Geometry WHERE
                xmin < MbrMaxX(SetSRID({bbox}, 4326)) AND
                xmax > MbrMinX(SetSRID({bbox}, 4326)) AND
                ymin < MbrMaxY(SetSRID({bbox}, 4326)) AND
                ymax > MbrMinY(SetSRID({bbox}, 4326))
            );""".format(table=table, bbox=bbox)

    def distance(self, table, point, distance):
        print >>self.out, """SELECT count(*) FROM {table}
            WHERE Distance(Transform(SetSRID({point}, 4326), 32614), Transform(Geometry, 32614)) <= {distance}
            AND ROWID IN (SELECT pkid FROM idx_{table}_Geometry WHERE
                xmin > MbrMinX(Transform(BuildCircleMbr(X(Transform(SetSRID({point}, 4326), 32614)), Y(Transform(SetSRID({point}, 4326), 32614)), {distance}, 32614), 4326)) AND
                xmax < MbrMaxX(Transform(BuildCircleMbr(X(Transform(SetSRID({point}, 4326), 32614)), Y(Transform(SetSRID({point}, 4326), 32614)), {distance}, 32614), 4326)) AND
                ymin > MbrMinY(Transform(BuildCircleMbr(X(Transform(SetSRID({point}, 4326), 32614)), Y(Transform(SetSRID({point}, 4326), 32614)), {distance}, 32614), 4326)) AND
                ymax < MbrMaxY(Transform(BuildCircleMbr(X(Transform(SetSRID({point}, 4326), 32614)), Y(Transform(SetSRID({point}, 4326), 32614)), {distance}, 32614), 4326)));""".format(table=table, point=point, distance=distance)

    def intersectlines(self, table):
        print >>self.out, """SELECT count(*) FROM {table} e, areawater a
            WHERE e.railflg = 'Y' AND Intersects(e.Geometry, a.Geometry)
            AND a.ROWID IN (SELECT pkid FROM idx_areawater_Geometry WHERE
                xmin < MbrMaxX(e.Geometry) AND
                xmax > MbrMinX(e.Geometry) AND
                ymin < MbrMaxY(e.Geometry) AND
                ymax > MbrMinY(e.Geometry));""".format(table=table)
        
    def makeBox(self, pointLL, pointUR):
        return "BuildMbr({xLL}, {yLL}, {xUR}, {yUR})".format(xLL=pointLL[0], yLL=pointLL[1], xUR=pointUR[0], yUR=pointUR[1])
    
    def makePoint(self, point):
        return "MakePoint({x}, {y})".format(x=point[0], y=point[1])
