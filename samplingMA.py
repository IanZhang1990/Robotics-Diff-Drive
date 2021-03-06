import sys, os
import random
import time
from robot import *
from obstacles import *
from geometry import *
from sampling import CoordMapping
from space_partition import *

def display_update(t=0.0):
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit();
			sys.exit();

	pygame.display.update();
	time.sleep(t);

class LineSearch:
	def __init__( self, start, dir, length, obstMgr, robot, mapper ):
		'''Search a line in c-space
		@param start  : start configuration point   v3().
		@param dir    : direction of the point      v3(). 
		@param length : length of the line.
		@param obstMgr: obstacles manager to detect collision.
		@param robot  : the robot
		@param mapper : configuration mapper. '''
		self.dir   	 = dir;
		self.len   	 = length;
		self.obstMgr = obstMgr;
		self.robot 	 = robot;
		self.mapper  = mapper;
		if dir:
			self.dir = dir.normalize();
		if dir is None:
			return;


		end = start + dir*length;

		'''
		if self.dist2Obst(start) > self.dist2Obst(end):
			self.start = start;
			self.end   = end;
		else:
			self.start = end;
			self.end   = start;'''
		self.start = start;
		self.end = end;
		pass;

	def dist2Obst(self, pnt):
		'''Distance to obstacles in c-space.
		@param pnt: config point in c-space.  mapped. v3()'''
		config_ = Config( v2(pnt.x, pnt.y), pnt.z );
		config  = self.mapper.unmap(config_);
		self.robot.setConfig(config);
		timeclearance = self.obstMgr.time2obsts( self.robot );
		return timeclearance;

	def search(self, surface=None):
		'''search for the point in the medial axis'''
		print "\n=====================\nsearching..."
		t = 1;
		last_increse = False;
		last_dist = self.dist2Obst(self.start);
		while True:
			temp = self.start + self.dir*t;
			this_dist = self.dist2Obst(temp);
			this_increase = ((this_dist-last_dist)>0);
			if surface is not None:
				self.robot.render(surface);
				display_update(0.2);
			#print this_dist;
			if this_dist == 0.0:
				return None, None;
			if last_increse and not this_increase:
				config_ = Config( v2(temp.x, temp.y), temp.z );
				config  = self.mapper.unmap(config_);
				self.robot.setConfig(config);
				if not self.obstMgr.intersects(self.robot):
					if surface is not None:
						self.robot.render(surface, (255,0,0));
						display_update(0.2);
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

class Sphere:
	'''A sphere in c-space is defined as (center, radius)'''
	def __init__( self, center, radius ):
		self.center = center;
		self.radius = radius;
		self.samples = [];
		self.bndsamples = [];
		self.__closed__ = False;

	def contains( self, point ):
		'''determine if the sphre contains a point'''
		dist = (point - self.center).r();
		return dist <= self.radius;

	def isClosed(self):
		return self.__closed__;

	def dist(self, point):
		'''distance from a point to the disc, negative if inside.'''
		centerdist = (point - self.center).r();
		return centerdist - self.radius;

	def append(self, point):
		'''if the point is inside it, add it to the sample set.'''
		if not self.contains(point):
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
				continue;
			dir = dir.normalize();
			bndPoint = self.center + dir * (self.radius+0.5);
			self.bndsamples.append( bndPoint );

		self.samples = [];
		self.__closed__ = True;
		return self.bndsamples;

class SamplerV2:
	'''Sampling class is responsible for sampling spheres in the c-space.
	V2 version will sample points on medial axis first then the boundary.'''
	def __init__( self, world ):
		self.robot 	   = world.robot;
		self.obstMgr   = world.obstMgr;
		self.world 	   = world;
		self.samples   = [];
		self.maSamples = [];
		self.partition = SpacePartition([100, 100, 100], [10,10,10]);
		self.mapper    = CoordMapping( self.world.WIDTH, self.world.HEIGHT );
		pass;

	def dist2obsts(self, config):
		self.robot.setConfig(config);
		return self.obstMgr.dist2obsts( self.robot );

	def getSphere( self, config, clearance ):
		'''Assume there is T clearance, T == @clearance, at configuration @config, 
		get the sphere at that config'''
		radius = clearance / ( math.sqrt(2) );
		config_ = self.mapper.map(config);
		center = v3(config_.x, config_.y, config_.orient);
		return Sphere( center, radius );

	def save_data( self, filename ):
		'''Save sampled spheres. Write data to a file'''
		file2write = open( filename, 'w' );
		formattedData = "";
		for sphere in self.samples:
			formattedData += str( sphere.center[0] ) + "\t";
			formattedData += str( sphere.center[1] ) + "\t";
			formattedData += str( sphere.center[2] ) + "\t";
			formattedData += str( sphere.radius);
			formattedData += "\n";

		file2write.write( formattedData );
		file2write.close();

	def load_data(self, filename):
		'''load spheres information from file'''
		self.partition.empty();
		self.samples = [];
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
			sphere = Sphere( v2( pos[0], pos[1] ), radius );
			if( sphere.radius >= 2.0 ):
				self.samples.append( sphere );
				self.partition.addSphere( sphere );


	def __sampleMA__(self, pntset, surface=None, rho=None ):
		'''Sample spheres centered on Medial Axis in c-space.
		@param pntset: A set of random points in free space. Coordinates are mapped.
		@param rho   : number of points per unit volume.    '''
		l = 15;
		self.maSamples = [];
		for point in pntset:
			#Check if within any balls.
			'''
			good = True;
			currentGridBalls = self.partition.getCurrentGridSpheres( point );
			for ball in currentGridBalls:
				if ball.append( point ):
					good = False;
					break;

			if not good:
				continue;
			'''
			dir_x = random.randint( -100, 100 );
			dir_y = random.randint( -100, 100 );
			dir_z = 0;#random.randint( -100, 100 );
			if dir_x == dir_y == dir_z == 0:
				dir_x = dir_y = dir_z = 50;
			rand_dir = v3(dir_x, dir_y, dir_z);
			line_searcher = LineSearch( point, rand_dir, l, self.obstMgr, self.robot, self.mapper );
			maSample = line_searcher.search(surface);
			if maSample[0] is not None and maSample[1] >= 0.01:
				config_ = Config( v2(maSample[0].x, maSample[0].y), maSample[0].z );
				config  = self.mapper.unmap(config_);
				newBall = self.getSphere(config, maSample[1]);
				self.maSamples.append( newBall );
				self.partition.addSphere( newBall );

		return self.maSamples;

	def sample(self, n, surface=None):
		'''Sample spheres in c-space
		@param n: (int) number of random points in free space'''
		pntset = [];
		for i in range(0, n):
			#progressBar( float(len(pntset)) / n * 100);
			rand_x 	   = random.randint( 0, self.world.WIDTH );
			rand_y 	   = random.randint( 0, self.world.HEIGHT);
			rand_theta = math.pi/4.0;#random.uniform( 0, 2*math.pi );

			config  = Config(v2(rand_x, rand_y), rand_theta);
			self.robot.setConfig( config );
			if not self.obstMgr.intersects( self.robot ):
				config_ = self.mapper.map( config );
				pntset.append( v3( config_.x, config_.y, config_.orient ) );

		spaceSize = self.mapper.scaledSpaceSize();
		rho = float(n)/float( spaceSize[0]*spaceSize[1]*spaceSize[2] );
		self.__sampleMA__(pntset, surface);

		self.samples += self.maSamples;

		return self.maSamples;

    	def randsample(self, n):
		'''Sample spheres in c-space
		@param n: (int) number of random points in free space'''
		pntset = [];
		for i in range(0, n):
			#progressBar( float(len(pntset)) / n * 100);
			rand_x 	   = random.randint( 0, self.world.WIDTH );
			rand_y 	   = random.randint( 0, self.world.HEIGHT);
			rand_theta = 0; #random.uniform( 0, 2*math.pi );

			config  = Config(v2(rand_x, rand_y), rand_theta);
			config_ = self.mapper.map( config );
			self.robot.setConfig( config );
			if self.obstMgr.intersects( self.robot ):
				continue;

			if not self.partition.checkValid( v3(config_.x, config_.y, config_.orient) ):
				continue;

			# valid point	
			
			clearance = self.obstMgr.time2obsts( self.robot );
			if clearance <= 0.1:
				continue;				# disgard too small spheres
			sphere = self.getSphere( config, clearance );
			self.partition.addSphere( sphere );
			self.samples.append( sphere );
