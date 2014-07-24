import pygame
from pygame.locals import *
import sys
import math

from obstacles import *
from robot import *
from samplingMA import *
from geometry import *


class World:
    '''World class'''
    def __init__( self, width, height, obstacles, robot ):
        self.WIDTH = width;
        self.HEIGHT = height;
        self.obstMgr = ObstManager( obstacles );
        self.robot = robot;

    def render(self, surface):
        self.obstMgr.intersects( self.robot );
        self.obstMgr.render(surface);
        self.robot.render(surface);


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

config = Config( v2( 150, 150 ), math.pi/3 )
diffDrive = DiffDriveRobot(80, config)

gameWorld = World( WIDTH, HEIGHT, obsts, diffDrive );


##################################################
#####           Render the world
##################################################
DISPLAYSURF.fill((240,235,240))
for event in pygame.event.get():
    if event.type == QUIT:
        pygame.quit()
        sys.exit()
gameWorld.render( DISPLAYSURF );
pygame.image.save( DISPLAYSURF, 'world.PNG' );


'''
while True:
    DISPLAYSURF.fill((240,235,240))

    #drawCircle( DISPLAYSURF, (850,850), 100 );

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    
    gameWorld.render( DISPLAYSURF );

    pygame.display.update();
    pass

pygame.quit();
'''

#mapper = CoordMapping(gameWorld.WIDTH, gameWorld.HEIGHT);
#cfg = Config( v2(400, 400), math.pi );
#cfg_ = mapper.map( cfg );

#print mapper.mapDist( 400 )


##################################################
#####                   Sample
##################################################


sampler = SamplerV2( gameWorld );

sampler.randsample(2000);
#sampler.sampleSlice( math.pi/4 );
sampler.save_data('spheres_complete.txt');