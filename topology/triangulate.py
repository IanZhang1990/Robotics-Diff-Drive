import sys, os, math
import pygame
import numpy

from scipy.spatial import Delaunay
from geometry import *

class Triangle:
	def __init__(self, vert1, vert2, vert3):
		'''v1, v2, v3 are all instances of geometry.v2(x,y)'''
		self.vertices = [vert1, vert2, vert3];
		self.spheres = [];
		self.ifValid = True;

	def addSpheres(self, spheres):
		self.spheres = spheres;

	def findSpheres( self, spheres ):
		for vert in self.vertices:
			for sphere in spheres:
				if (sphere[0]-vert.x)**2 + (sphere[1]-vert.y)**2 <= 2:
					self.spheres.append( sphere );

	def render(self, surface, mode = 1, color = ( 0, 255, 0 ) ):
		pointlist = [ (self.vertices[0].x, self.vertices[0].y), (self.vertices[1].x, self.vertices[1].y), (self.vertices[2].x, self.vertices[2].y) ];

		pygame.draw.polygon( surface, color, pointlist, mode );

class Triangulator:
	def __init__(self):
		self. triangles = [];

	def triangulate(self, points):
		'''points has the form: [(x1,y1), (x2,y2), ...., (xn, yn)]'''
		np_points = numpy.array( points );
		tris 	  = Delaunay( points );
		triIdx    = tris.vertices;
		for tri in triIdx:
			vert1 = v2(points[ tri[0] ][0], points[ tri[0] ][1] );
			vert2 = v2(points[ tri[1] ][0], points[ tri[1] ][1] );
			vert3 = v2(points[ tri[2] ][0], points[ tri[2] ][1] );
			self.triangles.append( Triangle(vert1, vert2, vert3) );

		return self.triangles;


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
		spheres.append( (pos[0], pos[1], radius) );
	return spheres;

def find_sphere( center, spheres ):
	"""Find the sphere that has the center"""
	for sphere in spheres:
		if (sphere[0]-center[0])**2 + (sphere[1]-center[1])**2 <= 1:
			return sphere;

if __name__ == "__main__":
	spheres = load_data( "balls.txt" );
	points = [];
	for sphere in spheres:
		points.append( (sphere[0], sphere[1] ) );

	triangulator = Triangulator();
	triangles = triangulator.triangulate(points);


	WIDTH = 800;
	HEIGHT = 800;

	pygame.init();
	DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT));
	DISPLAYSURF.fill((255,255,255));
	pygame.display.update();

    
	i = 0;
	for sphere in spheres:
		if i < 43:
			pygame.draw.circle( DISPLAYSURF, (200, 200, 200), (int(sphere[0]),int(sphere[1])), int(sphere[2]), 2 );
		else:
			pygame.draw.circle( DISPLAYSURF, (0, 200, 0), (int(sphere[0]),int(sphere[1])), int(sphere[2]), 2 );
		i += 1;

	#for tri in triangles:
	#	tri.render( DISPLAYSURF );


	for point in points:
		pygame.draw.circle( DISPLAYSURF, (255, 0, 0), (int(point[0]),int(point[1])), 3 );

	pygame.image.save( DISPLAYSURF, "Samples.PNG" );

