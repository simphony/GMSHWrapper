xy_radius = 1;
z_length = 1;
resolution = 10;

nodesZLength = z_length/resolution;
nodesCirc = 0.5*3.14/resolution;

Point(1) = {0,0,0};
Point(2) = {xy_radius,0,0};
Point(3) = {0,xy_radius,0};
Point(4) = {-xy_radius,0,0};
Point(5) = {0,-xy_radius,0};
  
Circle(1) = {2,1,3};
Circle(2) = {3,1,4};
Circle(3) = {4,1,5};
Circle(4) = {5,1,2};
Transfinite Line{1, 2, 3, 4} = nodesCirc; 
Line Loop(5) = {1,2,3,4};

Extrude {0,0,z_length} {Line{1, 2, 3, 4}; Layers{nodesZLength}; Recombine;}
