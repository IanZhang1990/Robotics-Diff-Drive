import pygame
from pygame.locals import *
import sys, os, time
import math, copy
import random
import Queue
from datetime import datetime

from geometry  import *
from obstacles import *
from utility   import *
from priority_queue import *
from pixel_reader   import *

class Disc:
	def __init__(self, center, radius):
		self.center  = center;
		self.radius  = radius;
		self.samples = [];
		self.bndsamples = [];
		self.__closed__ = False;

	def inside(self, point):
		dist = (point - self.center).r();
		if dist < self.radius:
			return True;
		else:
			return False;

	def isClosed(self):
		return self.__closed__;

	def dist(self, point):
		'''distance from a point to the disc, negative if inside.'''
		centerdist = (point - self.center).r();
		return centerdist - self.radius;

	def add(self, point):
		'''if the point is inside it, add it to the sample set.'''
		if not self.inside(point):
			return False;

		if self.__closed__:
			return True;

		self.samples.append( point );
		return True;

	def getbndpoints(self):
		'''Push all points to the boundary of the disc'''
		if self.__closed__:
			return [];
		self.bndsamples = [];
		for point in self.samples:
			dir = (point - self.center);
			if dir.r() == 0:
				dir = v2(1,3);
			dir = dir.normalize();
			bndPoint = self.center + dir * (self.radius+0.5);
			self.bndsamples.append( bndPoint );

		self.samples = [];
		self.__closed__ = True;
		return self.bndsamples;

	def render(self, surf, mode=1, color = (0, 200, 0)):
		'''render the disc.
		mode = 1: render the disc only.
		mode = 2: render the disc with inside points.
		mode = 3: render the disc with boundaryy points. '''
		if surf is None:
			return;

		pygame.draw.circle( surf, color, (int(self.center.x), int(self.center.y)), int(self.radius) )
		
		if mode == 2:
			for point in self.samples:
				pygame.draw.circle( surf, (50,50,50), (int(point.x), int(point.y)), 2 );
		elif mode == 3:
			for point in self.bndsamples:
				pygame.draw.circle( surf, (0,0,150), (int(point.x), int(point.y)), 2 );

		return;

class LineSearch:
	def __init__( self, start, dir, length, obstMgr, world ):
		 
		self.dir   	 = dir;
		self.len   	 = length;
		self.obstMgr = obstMgr;
		self.world 	 = world;
		if dir:
			self.dir = dir.normalize();
		if dir is None:
			return;

		end = start + dir*length;
		if self.dist2Obst(start) < self.dist2Obst(end):
			self.start = start;
			self.end   = end;
		else:
			self.start = end;
			self.end   = start;
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

	def nearPoint( self, pnt ):
		inside = 1;
		if self.obstMgr.inside(pnt):
			inside = -1;

		if pnt.x < 0 or pnt.y < 0 or pnt.x > self.world.WIDTH or pnt.y > self.world.HEIGHT:
			return None, min( pnt.x, self.world.WIDTH-pnt.x, pnt.y, self.world.HEIGHT-pnt.y )*(-1.0); 

		near, dist = self.obstMgr.closest_point( pnt );
		near2Wall, dist2Wall = self.point2WallDist( pnt, self.world.WIDTH, self.world.HEIGHT );
		if dist < dist2Wall:
			retNear = near; 		retDist = dist;
		else:
			retNear = near2Wall;	retDist = dist2Wall;
		return retNear, retDist*inside;


	def dist2Obst(self, pnt):
		#if pnt.x < 0 or pnt.y < 0 or pnt.x > self.world.WIDTH or pnt.y > self.world.HEIGHT:
		#	return min( pnt.x, self.world.WIDTH-pnt.x, pnt.y, self.world.HEIGHT-pnt.y )*(-1.0);

		#near, dist = self.obstMgr.closest_point(pnt);
		near, dist = self.nearPoint( pnt );
		return dist;

	def search(self):
		'''search for point in the medial axis'''
		t = 1;
		last_increse = False;
		last_dist = self.dist2Obst(self.start);
		while True:
			temp = self.start + self.dir*t;
			this_dist = self.dist2Obst(temp);
			this_increase = ((this_dist-last_dist)>0);
			if last_increse and not this_increase:
				if not self.obstMgr.inside(temp):
					return temp, this_dist;
				else:
					return None, None;
			else:
				t += 1;
				last_increse = this_increase;
				last_dist = this_dist;

			if t-1 >= self.len:
				break;

		return None, None;



class UMAPRMSampler:
	def __init__(self, world):
		self.world = world;
		self.obstMgr = self.world.obstMgr;
		self.MASamples = [];

	def nearPoint(self, pnt):
		searcher = LineSearch(None, None, 0, self.obstMgr, self.world);
		return searcher.nearPoint( pnt );

	def dist2Obst(self, pnt):
		#near, dist = self.obstMgr.closest_point(pnt);
		#dist = min( pnt.x, self.world.WIDTH-pnt.x, pnt.y, self.world.HEIGHT-pnt.y, dist );
		#return math.sqrt( (near.x-pnt.x)**2 + (near.y-pnt.y)**2 );
		near, dist = self.nearPoint( pnt );
		return dist;

	def k_nearest( self, totalpnts, pointset, point, radius ):
		'''Get k-nearest points in the point set to a givin point. k is determined by radius'''
	        rho = float(totalpnts) / (self.world.WIDTH*self.world.HEIGHT);
	        pq = PriorityQueue();
        	for pnt in pointset:
        		dist = (pnt-point).r();
        		pq.push( pnt, dist );

      		k = math.pi*((radius*1.3 )**2) * rho;
      		if k > len(pointset):
      			return pointset;
        	k_near = [];
        	for i in range(0,int(math.floor(k))):
        		k_near.append( pq.pop() );

        	return k_near;

	def sampleMAr(self, n, surf = None):
		'''randomly generate points in c-space and sample on medial axis'''
		pntset = [];
		while i in range(0,n):
			#progressBar( float(len(pntset)) / n * 100);
			rand_x = random.randint( 0, self.world.WIDTH );
			rand_y = random.randint( 0, self.world.HEIGHT);
			pnt = v2(rand_x, rand_y);
			if not self.obstMgr.inside( pnt ):
				pntset.append( pnt );
				
		#for point in pntset:
		#	if surf is not None:
		#		pygame.draw.line( surf, (0,0,0), (point.x, point.y), (point.x, point.y), 2 );
				
		#self.refreshPygame(0);


		l = 40;
		maSamples = [];
		for point in pntset:

			#Check if within any discs.
			good = True;
			for disc in maSamples:
				if (point.x-disc[0].x)**2+(point.y-disc[0].y)**2 < disc[1]**2:
					good = False;
					pntset.remove(point);
					break;

			if not good:
				continue;

			dir_x = random.randint( -100, 100 );
			dir_y = random.randint( -100, 100);
			rand_dir = v2(dir_x, dir_y);
			line_searcher = LineSearch( point, rand_dir, l, self.obstMgr, self.world );
			maSample = line_searcher.search();
			if maSample[0] is not None and maSample[1] >= 5:
				if surf is not None:
					pygame.draw.circle( surf, (0,200,0), (int(maSample[0].x), int(maSample[0].y)), int(maSample[1]), 1);
					pygame.draw.circle( surf, (0,200,0), (int(maSample[0].x), int(maSample[0].y)), int(maSample[1]));
					self.refreshPygame();

				maSamples.append( maSample );
				pntset.remove( point );

				#remove k-nearest
				'''
				K_near = self.k_nearest(pntset, point, maSample[1]);
				for near in K_near:
					pntset.remove( near );
					if surf is not None:
						pygame.draw.line( surf, (255,255,255), (near.x, near.y), (near.x, near.y), 3 );
						self.refreshPygame();
				'''

		for lftpnt in pntset:
			good = True;
			for disc in maSamples:
				if (lftpnt.x-disc[0].x)**2+(lftpnt.y-disc[0].y)**2 < disc[1]**2:
					good = False;
					break;

			if not good:
				continue;

			dist2obst = self.dist2Obst(lftpnt);
			maSamples.append( (lftpnt, dist2obst) );
			if surf is not None and dist2obst >= 10:
					pygame.draw.circle( surf, (0,0,200), (lftpnt.x, lftpnt.y), int(dist2obst), 1);
					self.refreshPygame(0);		

		return maSamples;

	def sampleMAb(self, n, surf = None):
		'''randomly sample disc on MA, and sample on the boundary of existing discs'''
		pntset = [];
		while len(pntset) < n:
			#progressBar( float(len(pntset)) / n * 100);
			rand_x = random.randint( 0, self.world.WIDTH );
			rand_y = random.randint( 0, self.world.HEIGHT);
			pnt = v2(rand_x, rand_y);
			if not self.obstMgr.inside( pnt ):
				pntset.append( pnt );
				
		#for point in pntset:
		#	if surf is not None:
		#		pygame.draw.line( surf, (0,0,0), (point.x, point.y), (point.x, point.y), 2 );
				
		self.refreshPygame(0);


		l = 40;
		maSamples = [];
		for point in pntset:
			#Check if within any discs.
			good = True;
			for disc in maSamples:
				if disc.add( point ):
					good = False;
					#pntset.remove( point );
					break;

			if not good:
				continue;

			dir_x = random.randint( -100, 100 );
			dir_y = random.randint( -100, 100);
			if dir_x == dir_y == 0:
				dir_x = dir_y = 50;
			rand_dir = v2(dir_x, dir_y);
			line_searcher = LineSearch( point, rand_dir, l, self.obstMgr, self.world );
			maSample = line_searcher.search();
			if maSample[0] is not None and maSample[1] >= 5:
				newDisc = Disc( maSample[0], maSample[1] );
				maSamples.append( newDisc );
				#pntset.remove( point );

		########
		## Deal with points left outside any existing discs.
		#----- Don't do anything for now.


		roundIdx = 0;
		while True:
			roundIdx += 1;
			newAdded = 0;

			for pnt in pntset:
				for disc in maSamples:
					if disc.add( pnt ):
						#pntset.remove( pnt );
						break;
				

			bndpntset = [];
			#bndpntset += pntset;
			#pntset = [];
			for disc in maSamples:
				bndpntset += disc.getbndpoints();
				if roundIdx == 1:
					disc.render( surf);
					self.refreshPygame(0.1);

			print len(bndpntset);
			for lftpnt in bndpntset:
				good = True;
				for disc in maSamples:
					if disc.inside( lftpnt ):
						good = False;
						#break;

				if not good:
					continue;

				dist2obst = self.dist2Obst(lftpnt);
				if dist2obst >= 10:
					newDisc = Disc(lftpnt, dist2obst);
					maSamples.append( newDisc );
					newAdded += 1;
					pygame.draw.circle( surf, (0,0,200), (int(lftpnt.x), int(lftpnt.y)), int(dist2obst), 1);
					self.refreshPygame();

			if newAdded == 0:
				break;

		return maSamples;

	def sampleMAbk(self, n, surf = None):
		'''randomly sample disc on MA, and sample on the boundary of existing discs'''
		pntset = [];
		for i in range(0, n):
			#progressBar( float(len(pntset)) / n * 100);
			rand_x = random.randint( 0, self.world.WIDTH );
			rand_y = random.randint( 0, self.world.HEIGHT);
			pnt = v2(rand_x, rand_y);
			if not self.obstMgr.inside( pnt ):
				pntset.append( pnt );
				
		#for point in pntset:
		#	if surf is not None:
		#		pygame.draw.line( surf, (0,0,0), (point.x, point.y), (point.x, point.y), 2 );
				
		self.refreshPygame(0);


		l = 40;
		maSamples = [];
		for point in pntset:
			#Check if within any discs.
			good = True;
			for disc in maSamples:
				if disc.add( point ):
					good = False;
					#pntset.remove( point );
					break;

			if not good:
				continue;

			dir_x = random.randint( -100, 100 );
			dir_y = random.randint( -100, 100);
			if dir_x == dir_y == 0:
				dir_x = dir_y = 50;
			rand_dir = v2(dir_x, dir_y);
			line_searcher = LineSearch( point, rand_dir, l, self.obstMgr, self.world );
			maSample = line_searcher.search();
			if maSample[0] is not None and maSample[1] >= 5:
				newDisc = Disc( maSample[0], maSample[1] );
				maSamples.append( newDisc );
				#pntset.remove( point );

		self.MASamples = copy.copy(maSamples);
		########
		## Deal with points left outside any existing discs.
		#----- Don't do anything for now.


		roundIdx = 0;
		newSmallSamples = maSamples;
		while True:
			roundIdx += 1;
			newAdded = 0;

			bndpntset = [];
			#bndpntset += pntset;
			#pntset = [];
			for disc in maSamples:
				if not disc.isClosed():
					knear = self.k_nearest(n, pntset, disc.center, disc.radius);
					disc.samples += knear;
					bndpntset += disc.getbndpoints();
					if roundIdx == 1:
						disc.render( surf);
						self.refreshPygame(0);

			for bndpnt in bndpntset:
				good = True;
				for disc in maSamples:
					if disc.inside( bndpnt ):
						good = False;
						#break;

				if not good:
					continue;

				dist2obst = self.dist2Obst(bndpnt);
				if dist2obst >= 10:
					newDisc = Disc(bndpnt, dist2obst);
					maSamples.append( newDisc );
					newAdded += 1; 
					pygame.draw.circle( surf, (0,0,200), (int(bndpnt.x), int(bndpnt.y)), int(dist2obst)); ######################## Boundary Discs
					self.refreshPygame();

			if newAdded == 0:
				break;

		return maSamples;

	def refreshPygame(self, t=0.0):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit();
				sys.exit();
			pass;
    		pygame.display.update();
    		time.sleep( t );


class World:
    '''World class'''
    def __init__( self, width, height, obstacles ):
        self.WIDTH = width;
        self.HEIGHT = height;
        self.obstMgr = ObstManager( obstacles );

    def render(self, surface):
        self.obstMgr.render(surface);


#=========================================================================================
#
#
#=========================================================================================

WIDTH = 800;
HEIGHT = 800;

pygame.init();

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

print "Initializing sampler..."
sampler = UMAPRMSampler(gameWorld);

##################################################
#####           Render the world
##################################################
filename = 'imgs/MAk_coverage/data_3.txt';
datafile2write = open( filename, 'w' );

for i in range( 1, 36 ):
	for j in range(1, 6):		
		infostr = '';
		DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT));
		DISPLAYSURF.fill((255,255,255));
		for event in pygame.event.get():
    			if event.type == QUIT:
        			pygame.quit();
        			sys.exit();
        	pygame.display.update();
		gameWorld.render( DISPLAYSURF );

		num = 200*i;
		print '=================================='
		print num;
		timestr = time.strftime('%a-%d-%b-%Y-%H:%M:%S')
		namestr = "imgs/MAk_coverage/" + timestr + '||' + str(num) + '||';
		starttime = datetime.now()
		samples = sampler.sampleMAbk( num, DISPLAYSURF );
		endtime = datetime.now()
		print "time cost: {0} microseconds".format(((endtime - starttime).microseconds)/float(1000));
		namestr += str(len(samples)) + '.PNG'
		#pygame.image.save( DISPLAYSURF, namestr );


		# Collect pixel info for analysis
		#infostr += "{0}\t{1}\t{2}\t".format( timestr, num, str(len(samples)) );
		pixelreader = PixelReader( DISPLAYSURF, gameWorld );
		coverage = float(pixelreader.count( (255, 255, 255), samples ));
		print "White Pixels: {0}".format(coverage);
		#infostr += str(coverage) +'\t{0}\n'.format( ((endtime - starttime).microseconds)/float(1000));
		#DISPLAYSURF = None;

		for record in pixelreader.records:
			infostr += "{0}\t{1}\t{2}\t{3}\t{4}\n".format( num, str(len(samples)), record[0].x, record[0].y, record[1] );

		datafile2write.write( infostr );
		
datafile2write.close();

#=========================================================================================
