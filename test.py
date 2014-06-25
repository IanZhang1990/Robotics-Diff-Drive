from geometry import *

A = v2(0, 0);      B = v2(100, 0);
C = v2(-10, 20);    D = v2(0, 150);
AB = line_segment(A, B);
CD = line_segment(C, D);

print AB.intersects_segment(CD);

print AB.dist_line_seg(CD);