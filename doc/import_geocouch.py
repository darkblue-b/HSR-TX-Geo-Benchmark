import couchdb, httplib, urlparse, uuid, re, mmap, json, optparse, os.path

parser = optparse.OptionParser(usage="usage: %prog [options] file")
parser.add_option('-s', '--server', dest='server', help='couchdb server', metavar='SERVER', default='http://localhost:5984/')
parser.add_option('-d', '--database', dest='database', help='database name', metavar='DATABASE')
options, args = parser.parse_args()

if len(args) == 0:
    parser.error("required input file not specified")

filename = args[0]
if not options.database:
    options.database, _ = os.path.splitext(os.path.basename(filename))

couch = couchdb.Server(options.server)
try:
    db = couch.create(options.database)
except couchdb.PreconditionFailed as e:
    couch.delete(options.database)
    db = couch.create(options.database)

designdoc = {
    'spatial': {
        options.database: "function(doc) {\n    if (doc.geometry) {\n        emit(doc.geometry, doc.properties);\n    }};"
    }
}
conn = httplib.HTTPConnection(*urlparse.urlparse(options.server).netloc.split(':'))
try:
    conn.request("PUT", "/{0}/_design/main".format(options.database), json.dumps(designdoc))
    conn.getresponse().read()
    
    with open(filename, 'r') as f:
        mf = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            pattern = re.compile('^(\{.*?\})$', re.MULTILINE)
            count = 0
            for match in pattern.finditer(mf):
                doc_id = uuid.uuid4().hex
                try:
                    doc = json.loads(match.group(1))
                except UnicodeDecodeError:
                    doc = json.loads(match.group(1).decode('iso-8859-1').encode('utf-8'))
                db[doc_id] = doc
    
                count+=1
                if count % 100 == 0:
                    print count
        finally:
            mf.close()
    
    conn.request("GET", "/{0}/_design/main/_spatial/{0}?bbox=0,0,180,90".format(options.database))
    print conn.getresponse().read()
finally:
    conn.close()
