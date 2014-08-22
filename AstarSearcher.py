
import sys, os, datetime
import math
from collections import defaultdict
from time import sleep
import pygame

from AstarPriorityQueue import *;
from geometry import *;
from obstacles import *
from robot import *

class Sphere:
	'''A sphere in c-space is defined as (center, radius)'''
	def __init__( self, center, radius ):
		self.center = center;
		self.radius = radius;

	def contains( self, point ):
		'''determine if the sphre contains a point'''
		distSqr = (self.center - point).r()

		if distSqr <= self.radius:
			return True;
		else:
			return False;

	def getBoundaryConfigs(self, num):
		""" Get configs in the boundary of the sphere. For 2D only!!!!
		@param num: the number of boundary configs you need. 
		When num = 0, automatically get boundary configs.
		"""
		retSet = []
		if( num == 0 ):
			num = self.radius / 5 + 5;

		dlt_ang = (2*math.pi) / float(num); # increment of angle;
		for i in range(1, int(num)+1):
			ang = dlt_ang * i;
			newX = self.center.x+(self.radius+1.3)*math.cos( ang );
			newY = self.center.y+(self.radius+1.3)*math.sin( ang );
			retSet += [ v2(newX, newY) ]
		return retSet;



class SphereRelationDetector:
	def __init__( self, spheres ):
		"""Given a list of spheres detect the overlapping realationship between each sphere"""
		self.mSpheres = spheres;
		self.mOverlapDict = default( list );

class AstarNode:
	def __init__(self, pos, parent, sphere = None):
		"""
		@param pos:v2
		@param parent: AstarNode
		@param sphere: Sphere. The sphere the sample is in
		"""
		self.mPosition = pos;
		self.mParentNode = parent;
		self.mSphere = sphere;		# The sphere the sample is in
		self.mG = 0;
		self.mH = 0;
		self.mF = 0; 				# F = cost + heuristic

class AstarPlus(object):
	"""description of class"""
	def __init__( self, spheres ):
		"""Constructor of AstarSearcher. The constructor will iterate each given spheres,
		and record their overlapping relationship. 
		@param spheres: distance samples got by SampleManager. Those samples should have 
		covered the whole free space.
		"""
		self.mSpheres = spheres;
		self.mOverlapDict = defaultdict( list );
		
		for sphere in self.mSpheres:
			for other in self.mSpheres:
				if( sphere == other ):
					continue;

				dist = (sphere.center-other.center).r();
				if( dist < (sphere.radius+other.radius) ):
					# Overlap! Record it in the dictionary
					self.mOverlapDict[sphere] += [ other ];

	def findOwnerSphere( self, config ):
		"""Given sample with (x,y) coordinate, find the sphere the sample is in."""
		maxRadius = 0;
		chosenSphere = None;
		for sphere in self.mSpheres:
			if sphere.contains(config):
				if maxRadius <= sphere.radius:
					maxRadius = sphere.radius;
					chosenSphere = sphere;
		return chosenSphere;


	def getSphereBoundaries( self, sphere, goal ):
		"""Given a sphere, return the points in the boundary of the sphere.
		 These boundary points should lie in shared areas btw the sphere and its overlaping spheres.
		 Data structure of each element in returned list: (point, sphere)
		 @param sphere: Sphere.
		 @param goal: v2.
		 """
		if sphere.contains( goal ):
			return [(goal, sphere)];

		delta = 2.0;
		alpha = 2.0 * math.asin( delta / float(sphere.radius) );
		num = 2.0 * 3.14159265354 / alpha;
		points = [];
		for i in range( 0, int(num)+1 ):
			angle = alpha * i;
			radius = sphere.radius + 1;
			x_coord = radius * math.cos(angle) + sphere.center.x;
			y_coord = radius * math.sin(angle) + sphere.center.y;
			points += [ v2( x_coord, y_coord ) ];

		neighborSpheres = self.mOverlapDict[sphere];

		legalPoints = [];
		for point in points:
			for neighborSphere in neighborSpheres:
				if neighborSphere is not sphere and neighborSphere.contains( point ):
					legalPoints += [(point, neighborSphere)]
					break;

		return legalPoints;


	def listContains( self, alist, astartNode ):
		pos = astartNode.mPosition;
		for element in alist:
			if math.fabs(element.mPosition.x - pos.x) < 1 and math.fabs(element.mPosition.y-pos.y) < 1:
				return element;

		return None;

	def astarSearch( self, start, goal, imgsurface=None ):
		"""Astart search with priority queue. 
		@param start: v2.
		@param goal: v2. """
		def backtrace( node, pardict ):
			path = []
			path.append( node )
			while( pardict.has_key(str(node))):
				path.append( pardict[str(node)] );
				node = pardict[str(node)];
			path.reverse();
			return path;

		openList = AstarPriorityQueue();
		closedList = AstarPriorityQueue();

		parentDict = defaultdict();
		sphereDict = defaultdict();
		GDict = defaultdict();

		ownerShpere = self.findOwnerSphere( start );
		startNode = AstarNode( start, None, ownerShpere );
		start_mF =  (start-goal).r();
		openList.push( startNode.mPosition,  start_mF );
		sphereDict[str(startNode.mPosition)] = ownerShpere;
		GDict[str(startNode.mPosition)] = 0;

		while( not openList.isEmpty() ):
			current, curr_mF = openList.pop();
			if current == goal:
				return backtrace( current, parentDict );
			#if( imgsurface is not None ):
			#	for event in pygame.event.get():
			#		pass;
			#	pygame.draw.circle( imgsurface, (0,255,0), (int(current.x), int(current.y)), 2 );
			#	pygame.display.update();

			#openList.remove_task( current );
			currOwnerSphere = sphereDict[str(current)];
			successors = self.getSphereBoundaries(currOwnerSphere, goal);
			closedList.push( current, curr_mF );

			for suc in successors:
				sucSamp = suc[0];
				if( closedList.find( sucSamp ) ):
					continue;
				sucOwnerSphere = suc[1];
				sucNode = AstarNode( sucSamp, current, sucOwnerSphere )
				sphereDict[str(sucNode.mPosition)] = sucOwnerSphere;

				#if sucSamp == goal:
				#	parentDict[str(sucNode.mPosition)] = current;
				#	return backtrace( sucSamp, parentDict );
				sucNode.mG = GDict[str(current)] + (sucSamp-current).r();

				sameOpen = openList.find( sucNode.mPosition );
				if( sameOpen is None or GDict[str(sucNode.mPosition)] > sucNode.mG):
					parentDict[str(sucNode.mPosition)] = sucNode.mParentNode;
					GDict[str(sucNode.mPosition)] = sucNode.mG;
					sucNode_mH = (sucSamp-goal).r()
					sucNode_mF = sucNode.mG + sucNode_mH;
					openList.push( sucNode.mPosition, sucNode_mF );
				pass
			pass
		return None;

	def savePath( self, path, filename ):
		"""Given a path in the scaled CSpace, save it to disk"""
		pathfile = open( filename, 'w' );
		if path is not None:
			for i in range( 0, len(path) ):
				config = path[i];
				pathfile.write( "{0}\t{1}\n".format(config.x, config.x) );


	def loadPath( self, pathfile ):
		"""Given a path file in the disk,  read the path to memory"""
		pathfile = open( pathfile );
		path = []
		for line in pathfile:
			info = line.split('\t');
			path.append( (float(info[0]), float(info[1])) );
			pass;
		return path;



class World:
	'''World class'''
	def __init__( self, width, height, obstacles, robot ):
		self.WIDTH = width;
		self.HEIGHT = height;
		self.obstMgr = ObstManager( obstacles );
		self.robot = robot;

	def render(self, surface):
		self.obstMgr.render(surface);


def load_sphere_data(filename):
	'''load spheres information from file'''
	file2read = open( filename, 'r' );
	lineNum = 0;
	spheres = [];
	for line in file2read:
		lineNum += 1;
		strSphere = line;
		info = strSphere.split( '\t' );
		pos = v2(float( info[0] ), float( info[1] ));
		radius = float( info[2] );
		spheres.append( Sphere(pos, radius) );
	return spheres;


if __name__ == "__main__":
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

	gameWorld = World( WIDTH, HEIGHT, obsts, None );


	##################################################
	#####		   Render the world
	##################################################
	DISPLAYSURF.fill((240,235,240))
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
	gameWorld.render( DISPLAYSURF );
	pygame.display.update();


	spheres = load_sphere_data( './topology/balls.txt' );
	i = 0;
	for sphere in spheres:
		if i < 43:
			pygame.draw.circle( DISPLAYSURF, (200, 200, 200), (int(sphere.center.x),int(sphere.center.y)), int(sphere.radius), 1 );
		else:
			pygame.draw.circle( DISPLAYSURF, (0, 150, 0), (int(sphere.center.x),int(sphere.center.y)), int(sphere.radius), 1 );
		i += 1;
    

	start = v2(400,20);
	goal = v2(400, 770);

	searcher = AstarPlus(spheres);
	path = searcher.astarSearch( start, goal, DISPLAYSURF );
	if path is not None:
		for i in range( 1, len(path) ):
			pygame.draw.line( DISPLAYSURF, (255,0,0), (int(path[i-1].x),int(path[i-1].y)), (int(path[i].x),int(path[i].y)), 2);
			pygame.display.update();
	

	pygame.draw.circle( DISPLAYSURF, (200, 0, 0), (int(start.x),int(start.y)), 3 );
	pygame.draw.circle( DISPLAYSURF, (200, 0, 0), (int(goal.x),int(goal.y)), 3 );

	pygame.draw.line( DISPLAYSURF, (0,0,0), (0,0), (0,799), 2);
	pygame.draw.line( DISPLAYSURF, (0,0,0), (0,799), (799,799), 2);
	pygame.draw.line( DISPLAYSURF, (0,0,0), (799,799), (799,0), 2);
	pygame.draw.line( DISPLAYSURF, (0,0,0), (799,0), (0,0), 2);

	pygame.image.save( DISPLAYSURF, "AstarSearch.PNG" );