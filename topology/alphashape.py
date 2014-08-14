
import sys, os, math;
import pygame;

from triangulate import *;
from geometry import *



class HypergraphNode:
	def __init__(self):
		self.triangles = [];
		self.nodes     = [];

	def addTriangle(self, triangle):
		if triangle not in self.triangles:
			self.triangles.append( triangle );

	def addNode(self, node):
		if node not in self.nodes:
			self.nodes.append( node );

def isEdgeValid( edge ):
	'''edge = (ball1, ball2, weight)'''
	A = v2(edge[0][0],edge[0][1]);
	B = v2(edge[1][0],edge[1][1]);
	return (A-B).r() <= edge[0][2] + edge[1][2];  

def triangleFilter( triangles, alpha = 0.5, surf = None ):
	edges = [];
	edge_points = [];

	for triangle in triangles:

		ball1 = triangle.spheres[0];
		ball2 = triangle.spheres[1];
		ball3 = triangle.spheres[2];

		pa = triangle.vertices[0];
		pb = triangle.vertices[1];
		pc = triangle.vertices[2];

		#Lengths of sides of triangle
		a = (pa-pb).r();
		b = (pb-pc).r();
		c = (pc-pa).r();

		# Semiperimeter of triangle 
		s = (a+b+c) / 2.0;

		# Area of triangle 
		area = math.sqrt( s*(s-a)*(s-b)*(s-c) );

		circum_r = a*b*c/(4.0*area);

		# Radius filter
		if circum_r < ball1[2] or circum_r < ball2[2] or circum_r < ball3[2]:
			edges.append( (ball1, ball2, 0) );
			edges.append( (ball2, ball3, 0) );
			edges.append( (ball1, ball3, 0) );

	return edges;

def isTriangleValid( triangle, surface ):
	ball1 = triangle.spheres[0];
	ball2 = triangle.spheres[1];
	ball3 = triangle.spheres[2];
	A = v2(ball1[0], ball1[1]);		r_a = ball1[2];
	B = v2(ball2[0], ball2[1]);		r_b = ball2[2];
	C = v2(ball3[0], ball3[1]);		r_c = ball3[2];

	#if (A-B).r() > (r_a+r_b) or (A-C).r() > (r_a + r_c) or (B-C).r() > (r_b+r_c):
	#	return False; 

	# 1. First Radical Axis
	l1 = (A-B).r();
	mid1 = A + (B-A).normalize() * ( l1**2 + r_a**2 - r_b**2 ) / (2 * l1); 
	k1 = 0.0;
	if (A-B).y == 0:
		k1 = 100000000000.0;
	elif (A-B).x == 0:
		k1 = 0.0;
	else:
		k1 = -1.0 / ( (B.y-A.y)/(B.x-A.x) );

	# 2. Second Radical Axis
	l2 = (A-C).r();
	mid2 = A + (C-A).normalize() * ( l2**2 + r_a**2 - r_c**2 ) / (2 * l2);
	k2 = 0.0;
	if (A-C).y == 0:
		k2 = 1000000000000.0;
	elif (A-C).x == 0:
		k2 = 0.0;
	else:
		k2 = -1.0 / ( (A.y-C.y)/(A.x-C.x) );

	# 3. Radical center is the intersection of two axises
	inter_x = (k1*mid1.x - k2*mid2.x + mid2.y - mid1.y) / (k1-k2);
	inter_y = k1*( inter_x - mid1.x ) + mid1.y;
	rad_center = v2( inter_x, inter_y );

	pygame.draw.circle( surface, (255,0,255), (int(rad_center.x), int(rad_center.y)), 3 );


	# Determine if the intersection is inside any spheres
	for sphere in triangle.spheres:
		center = v2(sphere[0],sphere[1]);
		radius = sphere[2];
		if (rad_center-center).r() <= radius:
			return True

	#pygame.draw.circle( surface, (0,0,0), (int(mid1.x), int(mid1.y)), 3 );
	#pygame.draw.circle( surface, (0,0,0), (int(mid2.x), int(mid2.y)), 3 );
	
	return False;

def find_sphere( center, spheres ):
	"""Find the sphere that has the center"""
	for sphere in spheres:
		if (sphere[0]-center[0])**2 + (sphere[1]-center[1])**2 <= 1:
			return sphere;

def buildDualShape(spheres):
	####################################
	### 0. get all centers as points 
	points = [];
	for sphere in spheres:
		points.append( (sphere[0], sphere[1] ) );

	####################################
	### 1.  triangulation 
	triangulator = Triangulator();
	triangles = triangulator.triangulate(points);


	####################################
	### 1.1  render everything 
	WIDTH = 800;
	HEIGHT = 800;

	pygame.init();
	DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT));
	DISPLAYSURF.fill((255,255,255));
	pygame.display.update();

	for sphere in spheres:
		pygame.draw.circle( DISPLAYSURF, (200, 200, 200), (int(sphere[0]),int(sphere[1])), int(sphere[2]), 1 );

	#for tri in triangles:
	#	tri.render( DISPLAYSURF, 1 );


	for point in points:
		pygame.draw.circle( DISPLAYSURF, (255, 0, 0), (int(point[0]),int(point[1])), 3 );

	
	##############################################
	### 2.  Determine if we should keep a triangle
	for triangle in triangles:
		triangle.findSpheres( spheres );

	edges = triangleFilter( triangles, 0.015, DISPLAYSURF );
	'''
	for triangle in triangles:
		triangle.findSpheres( spheres );
		triangle.ifValid = isTriangleValid( triangle, DISPLAYSURF );
		if triangle.ifValid:
			triangle.render( DISPLAYSURF, 0 );
	'''
	##############################################
	### 3.  Determine if we should keep an edge
	for edge in edges:
		if not isEdgeValid(edge):
			edges.remove( edge );
	
	for triangle in triangles:
		edge1 = ( triangle.spheres[0], triangle.spheres[1], 0 );
		edge2 = ( triangle.spheres[0], triangle.spheres[2], 0 );
		edge3 = ( triangle.spheres[1], triangle.spheres[2], 0 );
		if isEdgeValid( edge1 ):
			edges.append( edge1 );
		if isEdgeValid( edge2 ):
			edges.append( edge2 );
		if isEdgeValid( edge3 ):
			edges.append( edge3 );
	
	for edge in edges:
		pygame.draw.line( DISPLAYSURF, (0,0,200), ( int(edge[0][0]),int(edge[0][1]) ), ( int(edge[1][0]),int(edge[1][1]) ), 2 );
	pygame.image.save( DISPLAYSURF, "AlphaShape.PNG" );	


def load_data( filename):
	'''load spheres information from file'''
	file2read = open( filename, 'r' );
	lineNum = 0;
	spheres = [];
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
		if lineNum > 43:
			break;
		spheres.append( (pos[0], pos[1], radius) );
	return spheres;

if __name__ == "__main__":
	
	spheres = load_data( "balls.txt" );

	buildDualShape( spheres );