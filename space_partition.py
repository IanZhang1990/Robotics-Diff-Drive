import math
import sys, os
from collections import defaultdict
import numpy;
import utility
from sampling import *

class Grid:
    def __init__(self, dimLens, center = None):
        """@param center: center of the grid;
         @param dimLens: length in each dimension"""
        self.center = center;
        self.dimLens = dimLens;
        self.container = [];

    def addSphere( self, sphere ):
        if( self.contains( sphere ) ):
            return;
        self.container.append( sphere );

    def contains( self, sphere):
        '''True if the grid contains the sphere'''
        for item in self.container:
            if item == sphere:
                return True;
            if item.center == sphere.center and item.radius == sphere.radius:
                return True;
        return False;

    def checkValid( self, point ):
        '''check if the point is inside any spheres of the grid'''
        for item in self.container:
            if item.contains( point ):
                return False;
        return True;

    def inside( self, point ):
        """determine if a point is inside the grid"""
        for i in range( 0, len(point) ):
            if math.fabs( self.center[i] - point[i] ) > self.dimLens[i]/2.0:
                return False;
        return True;

    def __findFarestPoint__( self, outPoint ):
        """from direction center-->outPoint, this method finds a point that is farest from
         the center of the grid, yet still inside the grid."""
        end = outPoint;
        endInside = self.inside( end );
        if endInside: return outPoint;
        start = self.center;
        startInside = self.inside( start );
        
        while( True ):
            if ( utility.euclideanDistSqr( start, end ) <= 4 ):
                return start;
            mid = utility.devide( utility.add( start, end ), 2);
            if self.inside( mid ):
                start = mid;
            else:
                end = mid;

    def intersects( self, sphere, dim ):
        """Determine if the grid intersect with a sphere"""
        nearest = self.__findFarestPoint__( sphere.center );
        dist = utility.euclideanDistSqr( nearest, sphere.center );
        if( dist < sphere.radius**2 ):
            return True;
        else:
            return False;


    def empty(self):
        '''empty the container'''
        self.container = [];

class SpacePartition:
    '''Space partitioning functions only in scaled c-space'''

    def __init__( self, maxDimLens, unitDimLens ):
        dim = len(maxDimLens);
        self.mMaxDimLens = maxDimLens;
        self.mUnitDimLens = unitDimLens;
        num = 1;
        dimNums = [0]*len(maxDimLens);
        for i in range( 0, len(maxDimLens) ):
            dimNums[i] = int(maxDimLens[i] / unitDimLens[i]);
            num *= dimNums[i];

        self.mGrids = [];
        for i in range( 0, num ):
            grid = Grid( unitDimLens );
            self.mGrids.append(grid);
        self.mGrids = numpy.array( self.mGrids );
        self.mGrids.shape = dimNums;

        for index, item in numpy.ndenumerate( self.mGrids ):
            center = [0] * dim;
            for i in range( 0, dim ):
                center[i] = int(index[i]) *unitDimLens[i] + unitDimLens[i]/2.0;
            item.center = center;

    def addSphere( self, sphere ):
        center = sphere.center;
        ctrIdx = self.indxHash( center );
        radius = sphere.radius;
        dim = len( center );
        for index, item in numpy.ndenumerate( self.mGrids ):
            if utility.euclideanDist(item.center, sphere.center) - self.mUnitDimLens[0] > sphere.radius:
                continue;
            if item.intersects( sphere, dim ):
                item.addSphere(sphere);
        return;

    def getContainingGrid( self, point ):
        """Given a point in n-D world, return the grid containing it."""
        idx = self.indxHash( point );
        return self.mGrids[idx];

    def checkValid( self, point ):
        '''Check if a point is inside any spheres'''
        grid = self.getContainingGrid( point );
        return grid.checkValid( point );

    def indxHash( self, point ):
        """Given a point in n-D world, return the index containing the point"""
        dim = len( point );
        dimIdx = [0] * dim;
        for i in range(0, dim):
            dimIdx[i] = int(point[i]) / int( self.mUnitDimLens[i] )
        return tuple(dimIdx);

    def empty( self ):
        '''empty all spheres in any grids'''
        for grid in self.mGrids:
            grid.empty();