import pygame 
import math
import random
from geometry import *
from priority_queue import *


def k_nearest(  pointset, point, radius ):
	'''Get k-nearest points in the point set to a givin point. k is determined by radius'''
    	pq = PriorityQueue();
  	for pnt in pointset:
   		dist = (pnt-point).r();
   		pq.push( pnt, dist );

	k = radius**2 / 50;
   	if k > len(pointset):
   		return pointset;
      	k_near = [];
       	for i in range(0,int(math.floor(k))):
       		k_near.append( pq.pop() );

       	return k_near;


DISPLAYSURF = pygame.display.set_mode((800, 800));
DISPLAYSURF.fill((255,255,255));

pygame.draw.line( DISPLAYSURF, (0,0,0), (0, 700), (800, 700), 4 );
pygame.draw.circle( DISPLAYSURF,(0,255,0), ( 400, 500 ), 200, 2 );

pntset = [];
for i in range(0,300):
	rand_x = random.randint( 0, 800 );
	rand_y = random.randint( 0, 700);
	pnt = v2(rand_x, rand_y);
	pygame.draw.line( DISPLAYSURF, (0,0,0), (rand_x, rand_y), (rand_x, rand_y), 2 );
	pntset.append( pnt );

bndsamples = [];
knear = k_nearest(pntset, v2(400, 500), 200);
for point in knear:
	dir = (point - v2(400,500));
	if dir.r() == 0:
		dir = v2(1,3);
	dir = dir.normalize();
	bndPoint = v2(400, 500) + dir * (200);
	pygame.draw.circle(DISPLAYSURF, (250, 0, 0), (int(bndPoint.x),int(bndPoint.y)), 3);
	bndsamples.append( bndPoint );

pygame.image.save( DISPLAYSURF, "boundaryPointDensity.PNG" );
