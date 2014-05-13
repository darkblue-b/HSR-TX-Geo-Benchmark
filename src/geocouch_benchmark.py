import benchmark, httplib, json

# From http://stackoverflow.com/questions/823196/yaml-merge-in-python/823240#823240
# (2010-07-07)
# Values from b will overwrite existing values from a
def extend(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        for k,v in b.iteritems():
            if k not in a:
                a[k] = v
            else:
                a[k] = extend(a[k],v)
    elif b is not None:
        return b
    return a

def update_doc(conn, path, data):
    conn.request('GET', path)
    resp = conn.getresponse()
    if resp.status == 404:
        # full response must be read first
        resp.read()
    else:
        doc = json.loads(resp.read())
        extend(doc, json.loads(data))
        data = json.dumps(doc)

    conn.request('PUT', path, data)
    conn.getresponse().read()

class Benchmark(benchmark.Benchmark):
    def setUpClass(self):
        self.conn = httplib.HTTPConnection('localhost', 5984)
        
    def tearDownClass(self):
        self.conn.close()

    def loadData(self, sourcetable, targettable, bbox):    
        bbox = bbox.split(',')
        
        self.conn.request("DELETE", "/{targettable}".format(targettable=targettable))
        self.conn.getresponse().read()
    
        # Add replication filter 
        update_doc(self.conn,
                   "/{sourcetable}/_design/bench".format(sourcetable=sourcetable),
                   '{"language": "erlang", "filters": {"' + targettable + '": "fun({Doc}, {Req}) -> case proplists:get_value(<<\\"geometry\\">>, Doc, null) of null -> false; Geom -> GeomBbox = couch_spatial_updater:geojson_get_bbox(Geom), FilterBbox = {' + bbox[0] + ',' + bbox[1] + ',' + bbox[2] + ',' + bbox[3] + '}, not vtree:disjoint(GeomBbox, FilterBbox) end end."}}')
        #           '{"language": "erlang", "filters": {"' + target + '": "fun({Doc}, {Req}) -> case proplists:get_value(<<\\"geometry\\">>, Doc, null) of null -> false; Geom -> case couch_spatial_updater:geojson_get_bbox(Geom) of {E, S, W, N} when E > ' + bbox[0] + ', S > ' + bbox[1] + ', W < ' + bbox[2] + ', N < ' + bbox[3] + ' -> true; _ -> false end end end."}}')
        #           '{"language": "erlang", "filters": {"' + target + '": "fun({Doc}, {Req}) -> case proplists:get_value(<<\\"geometry\\">>, Doc, null) of null -> false; {Geom} -> case proplists:get_value(<<\\"coordinates\\">>, Geom, null) of [X, Y] when X > ' + bbox[0] + ', X < ' + bbox[2] + ', Y > ' + bbox[1] + ', Y < ' + bbox[3] + ' -> true; _ -> false end end end."}}')
        # old JavaScript replication filter
        #           '{"filters": {"' + target + '": "function(doc, req) {\u000a    if (!doc.geometry) return false;\u000a    var coord = doc.geometry.coordinates;\u000a    if (coord[0] > ' + bbox[0] + ' && coord[0] < ' + bbox[2] + ' && coord[1] > ' + bbox[1] + ' && coord[1] < ' + bbox[3] + ') {\u000a        return true;\u000a    }\u000a    return false;\u000a};"}}')
    
        # Start replication (create smaller subset)
        self.conn.request("POST", "/_replicate", '{"source":"' + sourcetable + '", "target":"http://localhost:5984/' + targettable + '", "create_target":true, "filter":"bench/' + targettable + '"}', {"Content-type": "application/json"})
        self.conn.getresponse().read()
    
        # Build spatial index
        #   First add the spatial index function
        self.conn.request("PUT", "/{targettable}/_design/main".format(targettable=targettable),
                     '{"spatial":{"points":"function(doc) {\n    if (doc.geometry) {\n        emit(doc.geometry, doc.properties);\n    }};"}}')
        self.conn.getresponse().read()
    
        #   then trigger the indexing with some bounding box query
        #print "GET", "/{targettable}/_design/main/_spatial/points?bbox=0,0,1,1".format(targettable=targettable)
        self.conn.request("GET",
                     "/{targettable}/_design/main/_spatial/points?bbox=0,0,1,1".format(targettable=targettable))
        self.conn.getresponse().read()

    def intersectbb(self, table, bbox):
        self.conn.request('GET',
                     '/{table}/_design/main/_spatial/points?bbox={bbox}&count=true'.format(table=table, bbox=bbox))
        print >>self.out, self.conn.getresponse().read()
        
    def makeBox(self, pointLL, pointUR):
        return '{xLL},{yLL},{xUR},{yUR}'.format(xLL=pointLL[0], yLL=pointLL[1],
                                               xUR=pointUR[0], yUR=pointUR[1])
    
    def makePoint(self, point):
        return "MakePoint({x}, {y})".format(x=point[0], y=point[1])
