
import pygame;
import math;
from geometry import *

class Config:
	'''Diff Drive configuration'''
	def __init__(self, pos, orient):
		"""@param pos: middle point position of the robot. (v2)
		@param orient: the orientation of the robot"""
		self.pos = pos;
		self.orient = orient;

	@property
	def x(self):
		return self.pos.x;

	@property
	def y(self):
		return self.pos.y;

class DiffDriveRobot:
	'''Differential Drive Robot class. A diff drive robot will be simplidied 
	as a line segment with wheels in two ends'''

	def __init__(self, length, config):
		'''@param length: the length of the robot
		@param config: robot configuration
		'''
		self.length = float(length);
		self.config = config;
		self.collision = False;

	def position(self):
		return self.config.pos;
	def orientation(self):
		return self.config.orient;

	pos = position;			# alias
	orient = orientation;	# alias

	def getLine(self):
		start = v2( self.config.pos.x - self.length/2.0*math.sin(self.config.orient),
				  self.config.pos.y + self.length/2.0*math.cos(self.config.orient));
		end   = v2( self.config.pos.x + self.length/2.0*math.sin(self.config.orient),
				  self.config.pos.y - self.length/2.0*math.cos(self.config.orient));

		return line_segment(start, end);

	def intersects(self, polygon):
		botline = self.getLine();
		self.collision = False;
		self.collision = polygon.inside( self.config.pos )
		if self.collision:
			return True;

		for line in polygon.lines:
			if line.intersects_segment(botline):
				self.collision = True;

		return self.collision;

	def setConfig(self, config):
		'''Set robot to a config'''
		self.config = config;
		return self.getLine();

	def render( self, surf ):
		'''Render the differential drive to the screen'''
		if self.collision == False:
			color = (80, 255, 80);
		else:
			color = (255,0,0);

		line = self.getLine();
		line.render( surf, color, 5 );

		temp = v2( self.config.pos.x + self.length/5.0*math.cos(self.config.orient),
				  self.config.pos.y + self.length/5.0*math.sin(self.config.orient));
		pygame.draw.line( surf, color, (self.config.pos.x, self.config.pos.y), (temp.x, temp.y), 4 )

		return;

