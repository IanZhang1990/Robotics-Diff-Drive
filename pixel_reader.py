import pygame 
import math
from geometry import *


class PixelReader:
	'''A class to read and analysis pixel info'''
	def __init__( self, surface, world ):
		self.surface = surface.convert();
		self.pxarray = pygame.PixelArray(surface);
		self.width   = self.surface.get_width();
		self.height  = self.surface.get_height();
		self.obstMgr = world.obstMgr;
		self.records = [];

	def dist2wall(self, point, width, height):
		dist = 1000000000;
		near = None;
		if width - point.x > point.x:
			dist = float(point.x);
		else:
			dist = float(width - point.x);
		if height - point.y > point.y:
			if dist > point.y:
				dist = float(point.y);
		else:
			if dist > height - point.y:
				dist = float(height - point.y);
		return dist;

	def count(self, color):
		'''Count the number of pixels with the give color'''
		counter = 0;
		for x in range( 1, self.width ):
			for y in range( 1, self.height ):
				#print self.pxarray[x,y];
				#print self.surface.map_rgb(color);
				if self.pxarray[x,y] == self.surface.map_rgb(color):
				 	near, dist = self.obstMgr.closest_point(v2(x,y));
				 	if dist < 0:
				 		continue;

				 	dist2wall = self.dist2wall( v2(x,y), self.width, self.height );
				 	counter += 1;					
					self.records.append((v2(x,y), min(dist, dist2wall)));
					pass;
				pass;
			pass;
		return float(counter);