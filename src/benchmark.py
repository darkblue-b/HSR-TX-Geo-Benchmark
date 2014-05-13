import sys, time, optparse

class DatabaseNotFoundError(Exception):
    def __init__(self, dbname):
        self.dbname = dbname
    def __str__(self):
        return self.dbname

class Benchmark(object):
    def __init__(self, out):
        self.out = out
        self.timers = {}
        self.results = {}
    
    def setUpClass(self):
        pass

    def tearDownClass(self):
        pass
    
    def startTimer(self, description):
        self.timers[description] = time.time()
    
    def stopTimer(self, description):
        self.results[description] = time.time() - self.timers[description]
    
    def printResults(self):
        for key in sorted(self.results.iterkeys()):
            print >>self.out, '{key}: {result}'.format(key=key, result=round(self.results[key], 3))
    
    def loadData(self, sourcetable, targettable, bbox):
        raise NotImplementedError()
    
    def createIndex(self, table, column):
        pass
    
    def makeBox(self, pointLL, pointUR):
        raise NotImplementedError()
        
    def makePoint(self, point):
        raise NotImplementedError()
    
    def nonspatial(self, table):
        raise NotImplementedError()
    
    def intersectbb(self, table, bbox):
        raise NotImplementedError()
    
    def distance(self, table, point, distance):
        raise NotImplementedError()
    
    def intersectlines(self, table):
        raise NotImplementedError()

class BenchmarkRunner(object):
    def __init__(self, dbname, out):
        self.heatupruns = 2
        
        try:
            __import__(dbname+'_benchmark')
            self.db = sys.modules[dbname+'_benchmark'].Benchmark(out)
        except (ImportError, KeyError):
            raise DatabaseNotFoundError(dbname)

        def wrapWithBenchmark(func):
            def benchmark(*args, **kwargs):
                description = func.__name__ + ' ' + args[0]
                add_desc = kwargs.get('description', '')
                if add_desc:
                    description += ' ' + add_desc

                try:
                    for _ in xrange(self.heatupruns):
                        func(*args, **kwargs)

                    self.db.startTimer(description)
                    func(*args, **kwargs)
                    self.db.stopTimer(description)
                except NotImplementedError:
                    pass
            return benchmark

        for fname in ['nonspatial', 'intersectbb', 'distance', 'intersectlines']:
            func = getattr(self.db, fname, None)
            setattr(self.db, fname, wrapWithBenchmark(func))
    
    def setUp(self):
        self.db.setUpClass()

    def tearDown(self):
        self.db.tearDownClass()

    def createDatasets(self):
        self.db.loadData('names', 'names_40k', self.db.makeBox((-103.208, 28.435), (-96.891, 33.460)))
        self.db.loadData('names', 'names_60k', self.db.makeBox((-104.006, 27.787), (-96.093, 34.193)))
        self.db.loadData('names', 'names_80k', self.db.makeBox((-104.904, 27.058), (-95.195, 34.830)))
        self.db.loadData('names', 'names_100k', self.db.makeBox((-106.168, 26.032), (-93.932, 35.693)))
        
        self.db.loadData('edges', 'edges_500k', self.db.makeBox((-102.169, 29.279), (-97.930, 30.515)))
        self.db.loadData('edges', 'edges_1000k', self.db.makeBox((-103.109, 28.516), (-96.991, 30.580)))
        self.db.loadData('edges', 'edges_1500k', self.db.makeBox((-103.518, 28.183), (-96.581, 31.255)))
        self.db.loadData('edges', 'edges_2000k', self.db.makeBox((-104.605, 27.301), (-95.494, 30.945)))
        self.db.loadData('edges', 'edges_2500k', self.db.makeBox((-106.041, 26.134), (-94.058, 30.754)))
        
        # create index for query 1
        self.db.createIndex('edges_500k', 'roadflg')
        self.db.createIndex('edges_1000k', 'roadflg')
        self.db.createIndex('edges_1500k', 'roadflg')
        self.db.createIndex('edges_2000k', 'roadflg')
        self.db.createIndex('edges_2500k', 'roadflg')
        
        # create index for query 5
        self.db.createIndex('edges_500k', 'railflg')
        self.db.createIndex('edges_1000k', 'railflg')
        self.db.createIndex('edges_1500k', 'railflg')
        self.db.createIndex('edges_2000k', 'railflg')
        self.db.createIndex('edges_2500k', 'railflg')
        
        self.db.loadData('areawater', 'areawater_100k', self.db.makeBox((-102.789, 28.775), (-97.3102, 33.174)))
        self.db.loadData('areawater', 'areawater_150k', self.db.makeBox((-103.261, 28.391), (-96.8380, 33.556)))
        self.db.loadData('areawater', 'areawater_200k', self.db.makeBox((-103.674, 28.057), (-96.4257, 33.814)))
        self.db.loadData('areawater', 'areawater_250k', self.db.makeBox((-104.272, 27.571), (-95.8272, 34.041)))
        self.db.loadData('areawater', 'areawater_300k', self.db.makeBox((-104.691, 27.230), (-95.4083, 34.451)))
        self.db.loadData('areawater', 'areawater_350k', self.db.makeBox((-105.536, 26.545), (-94.5637, 35.042)))

    def run(self):        
        self.db.nonspatial('edges_500k');
        self.db.nonspatial('edges_1000k');
        self.db.nonspatial('edges_1500k');
        self.db.nonspatial('edges_2000k');
        self.db.nonspatial('edges_2500k');
        
        self.db.intersectbb('names_40k', self.db.makeBox((-102.311, 29.164), (-97.789, 32.836)))
        self.db.intersectbb('names_60k', self.db.makeBox((-102.7765, 28.786), (-97.3235, 33.214)))
        self.db.intersectbb('names_80k', self.db.makeBox((-103.1755, 28.462), (-96.9245, 33.538)))
        self.db.intersectbb('names_100k', self.db.makeBox((-103.508, 28.192), (-96.592, 33.808)))
        
        self.db.intersectbb('areawater_100k', self.db.makeBox((-102.227875, 29.2315), (-97.872125, 32.7685)))
        self.db.intersectbb('areawater_150k', self.db.makeBox((-102.54375, 28.975), (-97.55625, 33.025)))
        self.db.intersectbb('areawater_200k', self.db.makeBox((-102.79645, 28.7698), (-97.30355, 33.2302)))
        self.db.intersectbb('areawater_250k', self.db.makeBox((-103.00925, 28.597), (-97.09075, 33.403)))
        self.db.intersectbb('areawater_300k', self.db.makeBox((-103.2686, 28.3864), (-96.8314, 33.6136)))
        self.db.intersectbb('areawater_350k', self.db.makeBox((-103.47475, 28.219), (-96.62525, 33.781)))
        
        self.db.intersectbb('edges_500k', self.db.makeBox((-101.743755, 29.62462), (-98.356245, 32.37538)))
        self.db.intersectbb('edges_1000k', self.db.makeBox((-102.0982, 29.3368), (-98.0018, 32.6632)))
        self.db.intersectbb('edges_1500k', self.db.makeBox((-102.54375, 28.975), (-97.55625, 33.025)))
        self.db.intersectbb('edges_2000k', self.db.makeBox((-102.9893, 28.6132), (-97.1107, 33.3868)))
        self.db.intersectbb('edges_2500k', self.db.makeBox((-103.242, 28.408), (-96.858, 33.592)))
        
        self.db.distance('names_40k', self.db.makePoint((-102.311, 32.836)), 20000)
        self.db.distance('names_60k', self.db.makePoint((-102.7765, 33.214)), 20000)
        self.db.distance('names_80k', self.db.makePoint((-103.1755, 33.538)), 20000)
        self.db.distance('names_100k', self.db.makePoint((-103.508, 33.808)), 20000)
        
        self.db.distance('areawater_100k', self.db.makePoint((-101.227, 30.7685)), 20000)
        self.db.distance('areawater_150k', self.db.makePoint((-102.54375, 32.025)), 20000)
        self.db.distance('areawater_200k', self.db.makePoint((-102.79645, 32.2302)), 20000)
        self.db.distance('areawater_250k', self.db.makePoint((-102.009, 32.951)), 20000)
        self.db.distance('areawater_300k', self.db.makePoint((-102.2686, 32.1136)), 20000)
        self.db.distance('areawater_350k', self.db.makePoint((-102.47475, 33.781)), 20000)
        
        self.db.distance('edges_500k', self.db.makePoint((-101.743755, 30.37538)), 20000)
        self.db.distance('edges_1000k', self.db.makePoint((-102.0982, 30.4632)), 20000)
        self.db.distance('edges_1500k', self.db.makePoint((-102.54375, 31.025)), 20000)
        self.db.distance('edges_2000k', self.db.makePoint((-102.9893, 29.3868)), 20000)
        self.db.distance('edges_2500k', self.db.makePoint((-103.242, 30.592)), 20000)
        
        self.db.intersectlines('edges_500k')
        self.db.intersectlines('edges_1000k')
        self.db.intersectlines('edges_1500k')
        self.db.intersectlines('edges_2000k')
        self.db.intersectlines('edges_2500k')
        
        self.db.printResults()
        
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-d", "--db", dest="database", action="store", default=None, help="specifies the database")
    parser.add_option("-l", "--load", dest="action", action="append_const", const="load", help="load the datasets")
    parser.add_option("-b", "--benchmark", dest="action", action="append_const", const="benchmark", help="run the benchmark (default)")
    parser.add_option("-o", "--output", dest="output", action="store", default="stdout", help="define the output file (default: stdout)", metavar="FILE")
    parser.add_option("-r", "--heatupruns", dest="heatupruns", action="store", default=2, type="int", help="specify the number of runs to heat up the cache (default: 2)", metavar="NUMBER")
    
    options, args = parser.parse_args()
    if not options.action:
        options.action = ['benchmark']
    if not options.database:
        parser.error("option -d is required")
    
    try:
        out = sys.stdout
        if options.output != 'stdout':
            out = open(options.output, 'w')
        
        benchmark = BenchmarkRunner(options.database, out)
        benchmark.heatupruns = options.heatupruns

        benchmark.setUp()
        if 'load' in options.action:
            benchmark.createDatasets()
        if 'benchmark' in options.action:
            benchmark.run()
        benchmark.tearDown()

        if callable(getattr(out, 'getvalue', None)):
            print out.getvalue()
    
    except DatabaseNotFoundError:
        parser.error("database '{database}' not available".format(database=options.database))
    
    finally:
        out.close()
