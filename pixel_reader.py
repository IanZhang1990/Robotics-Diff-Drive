import pygame 
import math



class PixelReader:
	'''A class to read and analysis pixel info'''
	def __init__( self, surface ):
		self.surface = surface.convert();
		self.pxarray = pygame.PixelArray(surface);
		self.width   = self.surface.get_width();
		self.height  = self.surface.get_height();

	def count(self, color):
		'''Count the number of pixels with the give color'''
		counter = 0;
		for x in range( 0, self.width ):
			for y in range( 0, self.height ):
				#print self.pxarray[x,y];
				#print self.surface.map_rgb(color);
				if self.pxarray[x,y] == self.surface.map_rgb(color):
					counter += 1;
					pass;
				pass;
			pass;
		return float(counter);