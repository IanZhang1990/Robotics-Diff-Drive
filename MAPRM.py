import pygame
from pygame.locals import *
import sys, os, time
import math, copy
import random

from geometry import *
from obstacles import *
from utility import *

class LineSearch:
	def __init__( self, start, dir ):
		self.start = start;
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
		idx      = 0;
		while( lastNear == thisNear ):
			#lastDist = thisDist;	lastNear = thisNear;
			pnt = v2( self.start.x+self.dir.x*idx, self.start.y+self.dir.y*idx )
			if surf:
				pygame.draw.line( DISPLAYSURF, (100, 100, 100), (int(pnt.x), int(pnt.y)), (int(pnt.x), int(pnt.y)), 1 );
				for event in pygame.event.get():
					pass;
    			pygame.display.update();
    			#time.sleep( .1 );

			thisNear, thisDist = self.nearPoint( pnt, obstMgr, world );
			#print '-------'
			#print "{0}\t{1}\t{2}".format(pnt, lastNear, thisNear);
			
			idx += 1;
		return pnt, thisDist;


class MAPRMSampler:
	def __init__(self, world):
		self.world = world;
		self.obstMgr = self.world.obstMgr;

	def nearPoint(self, pnt):
		searcher = LineSearch(None, None);
		return searcher.nearPoint( pnt, self.obstMgr, self.world );

	def sample(self, n):
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
			progressBar( (float(len(samples))/float(n)) * 100 );
		progressBar(100);

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
testPt = v2( 10, 300 );
start = None; end = None;
if not gameWorld.obstMgr.inside( testPt ):
	print testPt
	near, dist = sampler.nearPoint(testPt);
	print "Init Near: {0}".format(near);
	start = testPt;
	dirt  = v2( testPt.x-near.x, testPt.y-near.y );
searcher  = LineSearch( start, dirt );
pntOnMA, dist = searcher.search( gameWorld.obstMgr, gameWorld, DISPLAYSURF );

'''
samples = sampler.sample( 1000 );

for sample in samples:
	pygame.draw.circle( DISPLAYSURF, (220, 220, 220), (int(sample[0].x), int(sample[0].y)), int(sample[1]) );
	
for sample in samples:
#	pygame.draw.circle( DISPLAYSURF, (30, 30, 30), (int(sample[0].x), int(sample[0].y)), int(sample[1]), 1 );
    pygame.draw.line( DISPLAYSURF, (30, 30, 30), (int(sample[0].x), int(sample[0].y)),(int(sample[0].x), int(sample[0].y)),2 );
	
gameWorld.render(DISPLAYSURF);

#pygame.draw.circle( DISPLAYSURF, (100, 100, 100), (int(pntOnMA.x), int(pntOnMA.y)), 1 );
pygame.image.save( DISPLAYSURF, 'MediaAxis_Cover.PNG' );
