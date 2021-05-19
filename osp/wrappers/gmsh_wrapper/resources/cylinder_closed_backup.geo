xy_radius = 5;
z_length = 3;
resolution = 0.1;

cl = resolution;
nodesZLength = z_length/resolution;

Point(1) = {0,0,0,cl};
Point(2) = {xy_radius,0,0,cl};
Point(3) = {0,xy_radius,0,cl};
Point(4) = {-xy_radius,0,0,cl};
Point(5) = {0,-xy_radius,0,cl};
 
Circle(1) = {2,1,3};
Circle(2) = {3,1,4};
Circle(3) = {4,1,5};
Circle(4) = {5,1,2};
 
Line Loop(5) = {1,2,3,4};
Plane Surface(6) = {5};

allSurfaces[] = Surface "*" ;
Transfinite Surface{6};
Recombine Surface{allSurfaces[]};

Extrude {0,0,z_length} {Surface{6}; Layers{nodesZLength}; Recombine;}
