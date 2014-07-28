import pygame
from pygame.locals import *
import sys
import math

def parse(filename):

	file2write= open( 'analysis.txt', 'w' );

	file2read = open( filename, 'r' );
	lineNum   = 0;
	info_dict = dict();
	last_num  = 1000;
	counter = [0]*200;
	for line in file2read:
		info = line.split( '\t' );
		if len(info) < 3:
			continue;
		num_pnts = int(info[0]);
		num_disc = int(info[1]);
		x_coord  = int(info[2]);
		y_coord  = int(info[3]);
		dist     = float(info[4]);
		
		if num_pnts == last_num:
			counter[ int(dist) ] += 1;
		else:
			print "Finished parsing {0}".format(last_num);
			new_info = '';
			for i in range(0, len(counter)):
				if counter[i] == 0:
					continue;
				info_str = "{0}\t{1}\t{2}\n".format( last_num, i, counter[i] );
				new_info += info_str;
			file2write.write( new_info );

			counter = [0]*200;

		last_num = num_pnts;


	file2write.close();
	file2read.close();
	return;

if __name__ == "__main__":
	parse( "data_2.txt" );
