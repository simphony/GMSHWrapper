x_length = 2;
y_length = 1;
z_length = 5;
resolution = 0.01;

nodesXLength = x_length/resolution+1;
nodesYLength = y_length/resolution+1;
nodesZLength = z_length/resolution;

Point(101) = {0, 0, 0};
Point(102) = {0, y_length, 0};
Point(103) = {x_length, y_length, 0};
Point(104) = {x_length, 0, 0};

Line(201) = {101, 102};
Line(202) = {102, 103};
Line(203) = {103, 104};
Line(204) = {104, 101};

Line Loop(2011) = {201, 202, 203, 204};
Plane Surface(301) = 2011;

Transfinite Line{201, 203} = nodesYLength;
Transfinite Line{202, 204} = nodesXLength;

allSurfaces[] = Surface "*" ;
Transfinite Surface{allSurfaces[]};
Recombine Surface{allSurfaces[]};

Extrude{0, 0, z_length} {Surface{301}; Layers{nodesZLength}; Recombine;}

Mesh.Algorithm3D = 1;
Mesh 3;
Coherence Mesh;