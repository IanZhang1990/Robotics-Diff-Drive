
import sys, os
import random
from robot import *
from obstacles import *
from geometry import *
from space_partition import *

class CoordMapping:
	'''Coordinate Mapping class. Scale x,y and theta coordinates to relatively similar max values'''
	def __init__( self, width, height ):
		self.width = width;
		self.height = height;

	def map(self, config):
		'''Map a config from origin space to a scaled space'''
		x_     = ((float(config.x) / float(self.width)) * 100.0) / (math.pi/2+1.0);
		y_     = ((float(config.y) / float(self.height))* 100.0) / (math.pi/2+1.0);
		theta_ = (float(config.orient)/ (2 * math.pi)) * 100.0;
		return Config( v2(x_, y_), theta_ );

	def mapDist(self, dist):
		return ((float(dist) / ((self.width+self.height)/2.0)) * 100.0) / (math.pi/2+1.0);

	def mapOrient( self, orient ):
		return float(orient)/ (2 * math.pi) * 100.0;

	def unmap(self, config):
		x 	  = float( config.x ) * (math.pi/2+1.0) * float(self.width) / 100.0;
		y 	  = float( config.y ) * (math.pi/2+1.0) * float(self.width) / 100.0;
		theta = float( config.orient) * (2 * math.pi) / 100.0;
		return Config( v2(x,y), theta ); 

	def scaledSpaceSize(self):
		return (100, 100, 100);


class Sphere:
	'''A sphere in c-space is defined as (center, radius)'''
	def __init__( self, center, radius ):
		self.center = center;
		self.radius = radius;

	def contains( self, point ):
		'''determine if the sphre contains a point'''
		distSqr = (point[0]-self.center[0])**2 + (point[1]-self.center[1])**2 + (point[2]-self.center[2])**2

		if distSqr <= self.radius**2:
			return True;
		else:
			return False; 

class Sampler:
	'''Sampling class is responsible for sampling spheres in the c-space'''
	def __init__( self, world ):
		self.robot 	   = world.robot;
		self.obstMgr   = world.obstMgr;
		self.world 	   = world;
		self.samples   = [];
		self.partition = SpacePartition([100, 100, 100], [10,10,10]);
		self.mapper    = CoordMapping( self.world.WIDTH, self.world.HEIGHT );
		pass;

	def getSphere( self, config, clearance ):
		'''Assume there is T clearance, T == @clearance, at configuration @config, 
		get the sphere at that config'''
		radius = clearance / ( math.sqrt(2) );
		config_ = self.mapper.map(config);
		center = [ config_.x, config_.y, config_.orient ];
		return Sphere( center, radius );

	def sample( self, num ):
		'''@param num: max failure times. Sampling stops when failed @num times.'''
		failures = 0;

		while failures < num:
			rand_x 	   = random.randint( 0, self.world.WIDTH );
			rand_y 	   = random.randint( 0, self.world.HEIGHT);
			rand_theta = random.uniform( 0, 2*math.pi );

			config  = Config(v2(rand_x, rand_y), rand_theta);
			config_ = self.mapper.map( config );

			if not self.partition.checkValid( (config_.x, config_.y, config_.orient) ):
				failures += 1;
				continue;
			
			# valid point	
			self.robot.setConfig( config );
			clearance = self.obstMgr.time2obsts( self.robot, self.mapper );
			if clearance <= 0.1:
				continue;				# disgard too small spheres
			sphere = self.getSphere( config, clearance );
			self.partition.addSphere( sphere );
			self.samples.append( sphere );

	def sampleSlice( self, theta, check=False ):
		'''complete sample when the orientation of robot is set to @theta
		@param theta: the fixed orientation
		@param check: True or False for check(or not) a point is inside any existing spheres'''
		for i in range( 0, int(self.world.WIDTH/4) ):
			for j in range( 0, int(self.world.HEIGHT/4) ):
				if( j % 30 == 0 ):
					percentage = (i*self.world.WIDTH/4.0 + j)/(self.world.WIDTH*self.world.HEIGHT/16)*100.0;
					self.progressBar(percentage);
				x = 4.0*i; y = 4.0 * j;
				config  = Config( v2(x, y), theta );
				config_ = self.mapper.map( config );

				if check and not self.partition.checkValid( (config_.x, config_.y, config_.orient) ):
					continue;
			
				# valid point	
				self.robot.setConfig( config );
				clearance = self.obstMgr.time2obsts( self.robot, self.mapper );
				if clearance <= 0.1:
					continue;				# disgard too small spheres
				sphere = self.getSphere( config, clearance );
				self.partition.addSphere( sphere );
				self.samples.append( sphere );
		self.progressBar(100);

	def clearConsole(self):
		clear = lambda: os.system('clear');
		clear();

	def progressBar(self, percentage):
		percStr = ""
		for i in range( 0, int(percentage) ):
			percStr += '|';
		for i in range(int(percentage), 100):
			percStr += '-'
		self.clearConsole();
		print percStr;
		print "{0:.2f} %".format( percentage );

	def save_data( self, filename ):
		'''Save sampled spheres. Write data to a file'''
		file2write = open( filename, 'w' );
		formattedData = "";
		for sphere in self.samples:
			formattedData += str( sphere.center[0] ) + "\t";
			formattedData += str( sphere.center[1] ) + "\t";
			#formattedData += str( sphere.center[2] ) + "\t";
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
				sself.partition.addSphere( sphere );