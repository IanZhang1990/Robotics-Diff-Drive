import sys, os, math
import numpy

class Matrix:
	def __init__(self, mat):
		'''load from a simple 2d matrix to a numpy matrix'''
		self.mat = numpy.matrix( mat );
		self.origin_mat = mat;

	def mat_rank(self):
		return numpy.linalg.matrix_rank(self.mat);

mat = [[1, 1, 1,1],[1, 1, 1,1],[1, 1, 1,1],[1, 1, 1,1]];
nummat = Matrix( mat );
print nummat.mat_rank();
