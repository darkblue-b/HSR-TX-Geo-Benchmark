import benchmark, httplib, urllib, datetime, re, ujson 

class Benchmark(benchmark.Benchmark):
    def setUpClass(self):
        self.conn = httplib.HTTPConnection('localhost', 8983);
    def tearDownClass(self):
        self.conn.close();

    def loadData(self, sourcetable, targettable, bbox):    
        bbox = bbox.split(',') 
        geom = 'geom:[{p1},{p2} TO {p3},{p4}]'.format(p1=bbox[0],p2=bbox[1],p3=bbox[2], p4=bbox[3]);
        geom = urllib.quote(geom);
        rows = 10000
        globaltime = 0
        globalFound = 0
        startRow = 0
        diff = 1
        while(diff > 0) :
            print '{targettable} indexing {startRow}'.format(targettable=targettable,startRow=startRow)
            response = None;
            data = None;
            docs = None;
            query = '/solr/{sourcetable}/select?q=*&fq={geom}&wt=json&indent=true&start={startRow}&rows={rows}'.format(sourcetable=sourcetable,geom=geom,startRow=startRow,rows=rows);
            self.conn.request("GET", query);
            response = self.conn.getresponse().read();
            self.conn.close();
            data = ujson.loads(response);
            if (globalFound == 0):
                globalFound = data['response']['numFound'];
            docs = ujson.dumps(data['response']['docs']);        
            headers = {"Content-type": "application/json"}
            postQuery = "/solr/{targettable}/update/json?commit=true".format(targettable=targettable)
            self.conn.request("POST", postQuery, docs, headers);
            postResponse = self.conn.getresponse().read();
            postData = ujson.loads(response);
            startRow = startRow + rows
            diff = globalFound - startRow
            if(diff < rows):
                startRow = globalFound - diff
                query = '/solr/{sourcetable}/select?q=*&fq={geom}&wt=json&indent=true&start={startRow}&rows={rows}'.format(sourcetable=sourcetable,geom=geom,startRow=startRow,rows=rows);
                self.conn.request("GET", query);
                response = self.conn.getresponse().read();
                self.conn.close();
                data = ujson.loads(response);
                docs = ujson.dumps(data['response']['docs']); 
                headers = {"Content-type": "application/json"}
                postQuery = "/solr/{targettable}/update/json?commit=true".format(targettable=targettable)
                self.conn.request("POST", postQuery, docs, headers);
                postResponse = self.conn.getresponse().read();   
                diff = 0				
    
    def distance(self, table, point, distance):
        point = re.search(r'\((.*)\)', point).group(1)
        point = point.split(', ')
        distance = (distance/1000);
        query ='/solr/{table}/select?q=*%3A*&fq=%7B!geofilt%7D&wt=json&indent=true&spatial=true&pt={p1}%2C+{p2}&sfield=geom&d={distance}&rows=0'.format(table=table,p1=point[0],p2=point[1],distance=distance) 
        self.conn.request('GET',query)
        response = self.conn.getresponse().read();
        self.conn.close()
        data = ujson.loads(response)
        numFound = data['response']['numFound']
        qtime = data['responseHeader']['QTime']
        print 'distance ----> {table} ---> found {numFound} qtime {qtime}'.format(table=table, numFound=numFound, qtime=qtime)

    def intersectbb(self, table, bbox):
        bbox = bbox.split(',') 
        geom = 'geom:[{p1},{p2} TO {p3},{p4}]'.format(p1=bbox[0],p2=bbox[1],p3=bbox[2], p4=bbox[3]);
        geom = urllib.quote(geom);
        query = '/solr/{table}/select?q=*&fq={geom}&wt=json&indent=true&rows=0'.format(table=table,geom=geom)
        self.conn.request('GET',query)
        response = self.conn.getresponse().read()
        data = ujson.loads(response)
        numFound = data['response']['numFound']
        qtime = data['responseHeader']['QTime']
        print 'intersectbb ----> {table} ---> found:{numFound} qtime:{qtime}'.format(table=table, numFound=numFound,qtime=qtime)		
    
    def nonspatial(self, table):
        query = '/solr/{table}/select?q=ROADFLG%3AY&wt=json&indent=true&rows=0'.format(table=table);
        self.conn.request('GET',query);
        response = self.conn.getresponse().read();
        self.conn.close();
        data = ujson.loads(response);
        numFound = data['response']['numFound'];
        qtime = data['responseHeader']['QTime'];
        print 'nonspatial -> {table} ---> found: {numFound} qtime: {qtime}'.format(table=table, numFound=numFound, qtime=qtime); 		
 
    def makeBox(self, pointLL, pointUR):
        return '{yLL},{xLL},{yUR},{xUR}'.format(xLL=pointLL[0], yLL=pointLL[1],
                                               xUR=pointUR[0], yUR=pointUR[1])
    
    def makePoint(self, point):
        return "MakePoint({y}, {x})".format(x=point[0], y=point[1])
