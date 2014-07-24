from geometry import *
from robot import *
import pygame

class Polygon:
	"""Polygon class. An obstacle is defined as a polygon."""
	def __init__( self, ptlist ):
		"""@param ptlist: points list or tuple list, anti-clockwise ordered."""
		self.vertices = ptlist;
		self.lines = [];
		for i in range(1, len(ptlist)):
			line  = line_segment(ptlist[i-1], ptlist[i]);
			self.lines.append(line);

		start = ptlist[-1];
		end   = ptlist[0];
		self.lines.append( line_segment( start, end ) );
		pass;

	def render(self, surface, color):
		"""render the polygon to surface."""
		#for line in self.lines:
		#	line.render(surface, color, 1);
		#pass;
		pointlist = [];
		for vertex in self.vertices:
			pointlist.append( (int(vertex.x), int(vertex.y)) );
		pygame.draw.polygon(surface, color, pointlist);
		pass;

	def intersects(self, robot):
		"""polygon-line intersectiong test. Because our diff drive robot is modeled as a line segment"""
		bot = robot.getLine();
		for line in self.lines:
			if line.intersects_segment( bot ):
				return True;
		return False;

	def dist2robot(self, robot):
		bot = robot.getLine();
		dists = []
		for line in self.lines:
			dists.append(line.dist_line_seg(bot));
		return min(dists);

	def inside( self, point ):
		'''Assume the polygon is a simple polygon. determine if point is inside the polygon'''
		ray = line_segment( point, v2( 3000, 3000 ) );
		intersectTimes = 0;
		for line in self.lines:
			if line.intersects_segment( ray ):
				intersectTimes += 1;

		if intersectTimes % 2 == 1:
			return True;
		else:
			return False;

	def closest_point(self, point):
		'''get the nearest point in the polygon to a point'''
		nearestPoint = None;
		minDist = 100000000;
		for line in self.lines:
			temp = line.closest_point( point );
			dist = math.sqrt( (point.x-temp.x)**2 + (point.y-temp.y)**2);
			if dist < minDist:
				nearestPoint = temp;
				minDist = dist;
		return nearestPoint, minDist;


class ObstManager:
	'''Obstacle manager that controls all the obstacles in the space'''
	def __init__(self, obstacles):
		'''@param obstacles: a list of obstacles'''
		self.obsts = obstacles;

	def intersects(self, robot):
		'''determine if the robot intersects with any obstacles in the space'''
		if self.inside( robot.position() ):
			return True;
		for obst in self.obsts:
			if( robot.intersects(obst) ):
				return True;
		return False;

	def dist2obsts(self, robot):
		'''return the min dist from the robot to any obstacles.'''
		dists = [];
		for obst in self.obsts:
			dists.append( obst.dist2robot(robot) );
		return min(dists);

	def time2obsts(self, robot):
		'''return the min time for a robot to collide with any obstacles'''
		dist = self.dist2obsts(robot);
		return dist / 5.0;

	def closest_point(self, point):
		'''get the nearest point in obstacles to a point. 
		!!!This works only in 2d c-space!!!'''
		minDist = 10000000000;
		nearest = None;
		for obst in self.obsts:
			near, dist = obst.closest_point(point);
			if dist < minDist:
				nearest = near;
				minDist = dist;

		inside = 1;
		if self.inside(point):
			inside = -1;
		return nearest, minDist*inside;

	def inside( self, pnt ):
		'''test if a point is inside any polygon.
		!!!This works only in 2d c-space!!!'''
		for obst in self.obsts:
			if obst.inside(pnt):
				return True;
		return False;

	def render(self, surf):
		for obst in self.obsts:
			obst.render( surf, (60,60,60) );
		