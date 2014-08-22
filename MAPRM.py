import pygame
from pygame.locals import *
import sys, os, time
import math, copy
import random
import Queue

from geometry import *
from obstacles import *
from utility import *

class Helper:
	def __init__(self):
		self.idx = 0.0;

class LineSearch:
	def __init__( self, start, dir ):
		self.start = start;
		self.idx = 0;
		if dir:
			self.dir   = dir.normalize();
		pass;

	def point2WallDist(self, point, width, height):
		dist = 1000000000;
		near = None;
		if width - point.x > point.x:
			dist = point.x;
			near = v2( 0, point.y );
		else:
			dist = width - point.x;
			near = v2( width, point.y );
		if height - point.y > point.y:
			if dist > point.y:
				dist = point.y;
				near = v2( point.x, 0 );
		else:
			if dist > height - point.y:
				dist = height - point.y;
				near = v2( point.x, height );
		return near, dist;

	def nearPoint( self, pnt, obstMgr, world ):
		if obstMgr.inside(pnt):
			return None, 0.0;

		if pnt.x < 0 or pnt.y < 0 or pnt.x > world.WIDTH or pnt.y > world.HEIGHT:
			return None, 0.0; 

		near, dist = obstMgr.closest_point( pnt );
		near2Wall, dist2Wall = self.point2WallDist( pnt, world.WIDTH, world.HEIGHT );
		if dist < dist2Wall:
			retNear = near; 		retDist = dist;
		else:
			retNear = near2Wall;	retDist = dist2Wall;
		return retNear, retDist;

	def search(self, obstMgr, world, surf=None):
		lastNear, lastDist  = self.nearPoint( self.start, obstMgr, world );
		thisNear = copy.copy(lastNear); thisDist = lastDist;
		helper = Helper();
		pnt = copy.copy(self.start);
		while( lastNear == thisNear ):
			pnt = v2( self.start.x+self.dir.x*helper.idx, self.start.y+self.dir.y*helper.idx );
			thisNear, thisDist = self.nearPoint( pnt, obstMgr, world );
			helper.idx += 1;
		return pnt, thisDist;

	def searchISO(self, obstMgr, world, cost, surf=None):
		lastNear, lastDist  = self.nearPoint( self.start, obstMgr, world );
		helper = Helper();
		helper.idx = 0.0;
		pnt = copy.copy(self.start);
		acc = 1.0;

		while( math.fabs(cost-lastDist) >= 1 ):
			if( helper.idx > (cost/acc) ):
				acc = acc / 2.0;
				helper.idx = 0.0;
				if acc <= 0.25:
					break;

			#lastDist = thisDist;	lastNear = thisNear;
			pnt = v2( self.start.x+self.dir.x*helper.idx*acc, self.start.y+self.dir.y*helper.idx*acc )
			if surf:
				pygame.draw.line( DISPLAYSURF, (100, 100, 100), (int(pnt.x), int(pnt.y)), (int(pnt.x), int(pnt.y)), 1 );
				for event in pygame.event.get():
					pass;
    			pygame.display.update();
    			#time.sleep( .1 );

			lastNear, lastDist = self.nearPoint( pnt, obstMgr, world );
			#print '-------'
			#print "{0}\t{1}\t{2}".format(pnt, lastNear, lastDist);
			
			helper.idx += 1;
		return pnt, lastDist;


class MAPRMSampler:
	def __init__(self, world):
		self.world = world;
		self.obstMgr = self.world.obstMgr;

	def nearPoint(self, pnt):
		searcher = LineSearch(None, None);
		return searcher.nearPoint( pnt, self.obstMgr, self.world );

	def dist2Obst(self, pnt):
		near = self.obstMgr.closest_point(pnt);
		return math.sqrt( (near.x-pnt.x)**2 + (near.y-pnt.y)**2 );

	def sampleMA(self, n, ifShowProgressbar = True):
		'''Continuously sample on medial axis'''
		samples = [];
		while( len(samples) < n ):
			rand_x = random.randint( 0, self.world.WIDTH );
			rand_y = random.randint( 0, self.world.HEIGHT);
			pnt = v2(rand_x, rand_y);
			start = None; end = None;
			while( self.obstMgr.inside( pnt ) ):
				rand_x = random.randint( 0, self.world.WIDTH );
				rand_y = random.randint( 0, self.world.HEIGHT);
				pnt = v2(rand_x, rand_y);
			# Now, pnt is in free space
			near, dist = self.nearPoint(pnt);
			#print "Last Near: {0}".format(near);
			start = pnt;
			dirt  = v2( pnt.x-near.x, pnt.y-near.y );
			if dirt.r() == 0:
				continue;

			searcher       = LineSearch( start, dirt );
			pntOnMA, dist  = searcher.search( self.obstMgr, self.world );
			samples.append( (pntOnMA, dist) );
			if ifShowProgressbar:
				progressBar( (float(len(samples))/float(n)) * 100 );
		if ifShowProgressbar:
			progressBar(100);

		return samples;

	def sampleMAn( self, surf):
		'''Sampling on medial axis such that no new sample is centered within existing ones'''
		def inside(point, center, radius):
			distSqr = (point.x-center.x)**2 + (point.y-center.y)**2;
			if distSqr < radius**2:
				return True;
			else:
				return False;

		def ifNearMA( point ):
			near, dist = self.nearPoint(point);
			#print "Last Near: {0}".format(near);
			if near is None or self.obstMgr.inside(point):
				return False, 0;
			start = point;
			dirt  = v2( point.x-near.x, point.y-near.y );
			if dirt.r() == 0:
				return False, 0;
			searcher       = LineSearch( start, dirt );
			pntOnMA, dist  = searcher.search( self.obstMgr, self.world );
			#print "\t\t\t{0}".format( (pntOnMA.x-point.x)**2+(pntOnMA.y-point.y)**2 );
			if( (pntOnMA.x-point.x)**2+(pntOnMA.y-point.y)**2 <= 5):
				return True, dist;
			else:
				return False, 0;

		def getNewSample( point, dist ):
			'''Get points on the boundary of the disc that is also on the MA'''
			retSamps = [];
			for idx in range(0, 360*3):
				if idx % 36 == 0:
					progressBar( (idx/(360.0*3.0) ) * 100 );
				pnt = v2( point.x+float(dist)*math.cos(idx*(1.0/3.0)), point.y+float(dist)*math.sin(idx*(1.0/3.0)) );
				isNear = ifNearMA(pnt);
				if isNear[0] == True:
					retSamps.append( (pnt, isNear[1]) );

			return retSamps;

		samples = [];
		que = Queue.Queue();
		first = self.sampleMA(1, False);
		pygame.draw.circle( DISPLAYSURF, (220, 220, 220), (int(first[0][0].x), int(first[0][0].y)), int(first[0][1]) );
		for event in pygame.event.get():
			pass;
		pygame.display.update();
		samples.append( first[0] );
		que.put( first[0] );

		while not que.empty():
			lastSamp = que.get();
			newSamps = getNewSample( lastSamp[0], lastSamp[1] );
			for newsamp in newSamps:
				isInside = False;
				for samp in samples:
					if inside( newsamp[0], samp[0], samp[1] ):
						isInside = True;
						break;
				if not isInside and newsamp[1] > 10:
					pygame.draw.circle( DISPLAYSURF, (220, 220, 220), (int(newsamp[0].x), int(newsamp[0].y)), int(newsamp[1]), 0 );
					pygame.draw.line( DISPLAYSURF, (0, 0, 0), (int(newsamp[0].x), int(newsamp[0].y)), (int(newsamp[0].x), int(newsamp[0].y)), 2 );
					for event in pygame.event.get():
						pass;
    					pygame.display.update();
					samples.append( newsamp );
					que.put( newsamp );
					clear = lambda: os.system('clear');
    					clear();
					print len(samples);

		return samples;




	def sampleISO(self, n, cost, showProgressbar = True):
		'''Sample configs with the same cost.'''
		samples = [];
		while( len(samples) < n ):
			rand_x = random.randint( 0, self.world.WIDTH );
			rand_y = random.randint( 0, self.world.HEIGHT);
			pnt = v2(rand_x, rand_y);
			start = None; end = None;
			while( self.obstMgr.inside( pnt ) ):
				rand_x = random.randint( 0, self.world.WIDTH );
				rand_y = random.randint( 0, self.world.HEIGHT);
				pnt = v2(rand_x, rand_y);
			# Now, pnt is in free space
			near, dist = self.nearPoint(pnt);
			if dist > cost:
				if dist/2.0 > cost:
					start = near;
					dirt = v2( pnt.x-near.x, pnt.y-near.y );
				else:
					start = pnt;
					dirt = v2( near.x-pnt.x, near.y-pnt.y );
			else:
				start = pnt;
				dirt  = v2( pnt.x-near.x, pnt.y-near.y ); 
			#print "Last Near: {0}".format(near);
			if dirt.r() == 0:
				continue;

			searcher       = LineSearch( start, dirt );
			pntOnMA, dist  = searcher.searchISO( self.obstMgr, self.world, cost );
			if math.fabs(dist-cost) <= 1: 
				samples.append( (pntOnMA, dist) );
			if showProgressbar:
				progressBar( (float(len(samples))/float(n)) * 100 );
		if showProgressbar:
			progressBar(100);

		return samples;		

	def sampleIsoAround(self, pnt, cost):
		'''Sample points with some cost arond a point'''
		for idx in range(0, 360):
			point = v2( pnt.x+float(cost+5)*math.cos(idx), pnt.y+float(cost+5)*math.sin(idx) );
			near, currDist = self.nearPoint(point);
			if near is not None and math.fabs( cost-currDist ) <= 0.4:
				return point;

	def checkWithinMaSamples(self, point, r, maSamples):
		'''Check if the current iso sample is inside any medial axis samples.
		@param point: 		current iso sample position.
		@param r: 			current iso sample radius.
		@param maSamples: 	medial axis samples.
		'''
		for masam in maSamples:
			d = math.sqrt( (masam[0].x-point.x)**2 + (masam[0].y-point.y)**2 );
			if d + r - masam[1] < r * (1.0/3.0):
				return True;
		return False;

	def sampleISOn( self, cost, maSamples, surf=None ):
		vertices = [];
		inits = [];
		inits.append( v2( cost, cost ) )
		for obst in self.obstMgr.obsts:
			vertices.append(obst.vertices[0]);
			print obst.vertices[0];
		for vert in vertices:
			init = self.sampleIsoAround( vert, cost );
			print init;
			inits.append( init );

		samples = [];
 
		for init in inits:
			self.__sampleISOn__( init, cost, samples, maSamples, surf );

		return samples;


	def __sampleISOn__( self, initPnt, cost, samples, maSamples, surf ):
		'''Sample on the iso-cost contour such that no sample is centered in existing ones'''
		def inside(point, center, radius):
			distSqr = (point.x-center.x)**2 + (point.y-center.y)**2;
			if distSqr < radius**2/4.0:
				return True;
			else:
				return False;

		def getNewSample( point, dist ):
			'''Get points on the boundary of the disc that has the same cost as the center'''
			retSamps = [];
			for idx in range(0, 360):
				pnt = v2( point.x+float(dist/2.0)*math.cos(idx), point.y+float(dist/2.0)*math.sin(idx) );
				near, currDist = self.nearPoint(pnt);
				if math.fabs( dist-currDist ) <= 0.4:
					retSamps.append( pnt );

			return retSamps;


		#samples = [];
		que = Queue.Queue();

		samples.append( initPnt );
		que.put(initPnt);		

		while not que.empty():
			sample = que.get();
			newSamps = getNewSample( sample, cost+0.4 )
			print 'new samples:{0}'.format(len(newSamps));
			if len(samples) >= 2:
				for newsamp in newSamps:
					ifwithin = False;
					for j in range(1, len(samples)):
						if inside(newsamp, samples[j], cost):
							ifwithin = True;
							break;

					if not ifwithin:
						samples.append( newsamp );
						que.put( newsamp );
						clear = lambda: os.system('clear');
    						clear();
    						print len(samples);
    						if surf:
							pygame.draw.line( DISPLAYSURF, (255, 0, 00), (int(newsamp.x), int(newsamp.y)), (int(newsamp.x), int(newsamp.y)), 5 );
							for event in pygame.event.get():
								pass;
    							pygame.display.update();
    							#time.sleep( .1 );
	    		else:
	    			for newsamp in newSamps:
    					samples.append(newsamp);
    					que.put(newsamp);
    					if surf:
						pygame.draw.line( DISPLAYSURF, (255, 0, 0), (int(newsamp.x), int(newsamp.y)), (int(newsamp.x), int(newsamp.y)), 5 );
						for event in pygame.event.get():
							pass;
    						pygame.display.update();
    						#time.sleep( .1 );
    				continue;

		#return samples;
	def save_data( self, masamples, filename ):
		'''Save sampled spheres. Write data to a file'''
		file2write = open( filename, 'w' );
		formattedData = "";
		for samp in masamples:
			formattedData += str( samp[0].x ) + "\t";
			formattedData += str( samp[0].y ) + "\t";
			#formattedData += str( sphere.center[2] ) + "\t";
			formattedData += str( samp[1]);
			formattedData += "\n";

		file2write.write( formattedData );
		file2write.close();

	def load_data(self, filename):
		'''load spheres information from file'''
		samples = [];
		file2read = open( filename, 'r' );
		lineNum = 0;
		for line in file2read:
			if( lineNum % 100 == 0 ):
				print "Reading line: {0}".format( lineNum );
			lineNum += 1;
			strSphere = line;
			info = strSphere.split( '\t' );
			pos = [0] * 2;
			pos[0] = float( info[0] );
			pos[1] = float( info[1] );
			radius = float( info[2] );
			#sphere = Sphere( v2( pos[0], pos[1] ), radius );
			if( radius >= 2.0 ):
				samples.append( (v2(pos[0], pos[1]), radius) );

		return samples;


class World:
    '''World class'''
    def __init__( self, width, height, obstacles ):
        self.WIDTH = width;
        self.HEIGHT = height;
        self.obstMgr = ObstManager( obstacles );

    def render(self, surface):
        self.obstMgr.render(surface);


WIDTH = 800;
HEIGHT = 800;

DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT));
DISPLAYSURF.fill((255,255,255));

###========== Robots and Obstacles
###======================================================

pts1 = [ v2(200, 100), v2(500, 100), v2(500, 200), v2(200, 200) ];
pts2 = [ v2(200, 330), v2(500, 330), v2(500, 430), v2(200, 430) ];
pts3 = [ v2(200, 500), v2(500, 500), v2(500, 550), v2(200, 550) ];
pts4 = [ v2(200, 600), v2(500, 600), v2(500, 700), v2(200, 700) ];
obst1 = Polygon(pts1);
obst2 = Polygon(pts2);
obst3 = Polygon(pts3);
obst4 = Polygon(pts4);

obsts = [obst1, obst2,  obst4];

config = Config( v2( 150, 150 ), math.pi/3 )
#diffDrive = DiffDriveRobot(80, config)

gameWorld = World( WIDTH, HEIGHT, obsts );

sampler = MAPRMSampler(gameWorld);

##################################################
#####           Render the world
##################################################
DISPLAYSURF.fill((255,255,255))
for event in pygame.event.get():
    if event.type == QUIT:
        pygame.quit()
        sys.exit()
gameWorld.render( DISPLAYSURF );
#pygame.image.save( DISPLAYSURF, 'world.PNG' );

'''
testPt = v2( 772.000,795.000 );
start = None; end = None;
if not gameWorld.obstMgr.inside( testPt ):
	print testPt
	near, dist = sampler.nearPoint(testPt);
	print "Init Near: {0}".format(near);
	start = testPt;
	dirt  = v2( testPt.x-near.x, testPt.y-near.y );
searcher  = LineSearch( start, dirt );
pntOnMA, dist = searcher.searchISO( gameWorld.obstMgr, gameWorld, 30, DISPLAYSURF );
'''
#samples = sampler.sampleISO( 1000, 30 );
#samples = sampler.sample( 1000 );
#samples = sampler.sampleISOn(30, DISPLAYSURF);
#samples  = sampler.sampleMAn(DISPLAYSURF);
#sampler.save_data( samples, "masamples.txt" );
#samples  = sampler.load_data( "masamples.txt" );
samples2 = sampler.sampleMA( 3000 );
#samples3 = sampler.sampleISOn( 34, samples );

print "Finished!"
'''
for sample in samples:
	pygame.draw.circle( DISPLAYSURF, (220, 220, 220), (int(sample[0].x), int(sample[0].y)), int(sample[1]) );
'''
#for sample in samples:
#	pygame.draw.circle( DISPLAYSURF, (20, 20, 20), (int(sample[0].x), int(sample[0].y)), int(sample[1]), 1 );

for sample in samples2:
	pygame.draw.line( DISPLAYSURF, (30, 30, 30), (int(sample[0].x), int(sample[0].y)),(int(sample[0].x), int(sample[0].y)), 2 );	

gameWorld.render(DISPLAYSURF);
pygame.image.save( DISPLAYSURF, './imgs/medialaxis.PNG' );

sys.exit()
#for sample in samples:
#	pygame.draw.circle( DISPLAYSURF, (30, 30, 30), (int(sample[0].x), int(sample[0].y)), int(sample[1]), 1 );
#   pygame.draw.line( DISPLAYSURF, (30, 30, 30), (int(sample[0].x), int(sample[0].y)),(int(sample[0].x), int(sample[0].y)), 2 );
sample4 = [];
for sample in samples3:
	if not sampler.checkWithinMaSamples( sample, 34, samples ):
		sample4.append( sample );
		#pygame.draw.circle( DISPLAYSURF, (150, 150, 150), (int(sample.x), int(sample.y)), 34, 1 );

for sample in sample4:
	for other in sample4:
		if math.sqrt( (sample.x-other.x)**2+(sample.y-other.y)**2 ) < 20:
			sample4.remove(sample);
			break;

for sample in sample4:
	pygame.draw.circle( DISPLAYSURF, (180, 180, 180), (int(sample.x), int(sample.y)), 34, 1 );
'''
for sample in samples:
	if sample:
	    	pygame.draw.line( DISPLAYSURF, (30, 30, 30), (int(sample.x), int(sample.y)),(int(sample.x), int(sample.y)), 3 );
'''

gameWorld.render(DISPLAYSURF);

#pygame.draw.circle( DISPLAYSURF, (100, 100, 100), (int(pntOnMA.x), int(pntOnMA.y)), 1 );
pygame.image.save( DISPLAYSURF, 'MediaAxis_bnd_iso2.PNG' );


