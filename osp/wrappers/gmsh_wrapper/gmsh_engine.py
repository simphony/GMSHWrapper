from abc import abstractmethod
import os
import numpy as np
from numpy import linalg
import gmsh

from traits.api import (
    ABCHasStrictTraits, Enum, Property,
    Float, File, List, Dict, Tuple, Int
)


SUPPORTED_UNITS = ['mm', 'cm', 'm']
CONVERSIONS = {
    'mm': 0.001,
    'cm': 0.01,
    'm': 1,
    'mm^2': 0.001**2,
    'cm^2': 0.01**2,
    'm^2': 1,
    'mm^3': 0.001**3,
    'cm^3': 0.01**3,
    'm^3': 1,
}


def extent(min_extent=[0, 0, 0], max_extent=[0, 0, 0]):
    """
    Describes a maximum extent of a given shape
    """
    return {
        "x": {"min": min_extent[0], "max": max_extent[0]},
        "y": {"min": min_extent[1], "max": max_extent[1]},
        "z": {"min": min_extent[2], "max": max_extent[2]},
    }


class BaseMesh(ABCHasStrictTraits):

    units = Enum(SUPPORTED_UNITS)

    volume = Property(Float)

    convert_to_meters = Property(Float)

    filling_extent = Property(Dict)

    max_extent = Dict

    hexaedric_extent = Dict

    inside_location = List

    filling_fraction = Float

    z_length = Int(10)

    resolution = Int(5)

    @abstractmethod
    def _get_volume(self):
        """Returns volume of mesh"""

    @abstractmethod
    def _get_filling_extent(self):
        """
        Returnes a dictionary with the maximum extent of
        the filling material in each direction.
        """

    def _enlarge_extent(self):
        for index in max_extent.keys():
            if not self._check_extent(index):
                self._correct_extent(index)

    def _get_extent(self, index):
        return [
            self.max_extent[index][direct] for direct in ["min", "max"]
        ]

    def _correct_extent(self, index):
        min_value, max_value = self._shift_hexaedric_extent(index)
        while True:
            if max_value - min_value > 0:
                break
            else:
                max_value += self.resolution
        self.hexaedric_extent[index] = {"min": min_value, "max": max_value}

    def _shift_hexaedric_extent(self, index):
        min_value, max_value = self._get_extent(index)
        if max_value < 0:
            max_value = -np.ceil(-max_value)
        else:
            max_value = np.ceil(max_value)
        if min_value < 0:
            min_value = -np.ceil(-min_value)
        else:
            min_value = np.ceil(min_value)
        return min_value, max_value

    def _check_extent(self, index):
        if self._get_ncells_in_direction(index).is_integer():
            return True
        else:
            return False

    def _get_ncells_in_direction(self, index):
        return float(
            self.resolution * self._get_length_of_extent(index)
        )

    def _get_length_of_extent(self, index):
        min_value, max_value = self._get_extent(index)
        return max_value - min_value

    def _get_convert_to_meters(self):
        """Returns conversion factor depending on units"""
        return CONVERSIONS[self.units]


class RectangularMesh(BaseMesh):

    x_length = Int(1)

    y_length = Int(1)

    source_geo = os.path.join(
        os.path.dirname(__file__),
        "resources",
        "rectangle_backup.geo"
    )

    # OVERRIDE
    def _get_volume(self):
        return self.x_length * self.y_length * self.z_length

    def write_mesh(self, target_path):
        self._write_geo(target_path)
        self._write_stl(target_path)
        self._calc_properties()

    def _write_geo(self, target_path):
        target_geo = os.path.join(target_path, 'new_surface.geo')
        with open(self.source_geo, "r") as template,\
                open(target_geo, "w") as file:
            for line in template:
                if "x_length = " in line:
                    line = f"x_length = {self.x_length};\n"
                elif "z_length = " in line:
                    line = f"z_length = {self.z_length};\n"
                elif "y_length = " in line:
                    line = f"y_length = {self.y_length};\n"
                elif "resolution = " in line:
                    line = f"resolution = {self.resolution};\n"
                file.write(line)

    # OVERRIDE
    def _get_filling_extent(self):
        return extent(
            max_extent=[
                self.x_length,
                self.y_length,
                self.z_length*self.filling_fraction
            ]
        )

    def _write_stl(self, target_path):
        target_geo = os.path.join(
            target_path, 'new_surface.geo'
        )
        target_stl = os.path.join(
            target_path, 'new_surface.stl'
        )
        gmsh.initialize()
        gmsh.open(target_geo)
        gmsh.model.mesh.generate(3)
        gmsh.write(target_stl)
        gmsh.finalize()

    def _calc_properties(self):
        self.max_extent = extent(
            max_extent=[
                self.x_length,
                self.y_length,
                self.z_length
            ]
        )
        self.inside_location = [
                self.x_length*0.5,
                self.y_length*0.5,
                self.z_length*0.5
            ]
        self._enlarge_extent()


class CylinderMesh(BaseMesh):

    base = Tuple((0, 0, 0))

    direction = Tuple((0, 0, 1.0))

    xy_radius = Int(150)

    source_geo = os.path.join(
        os.path.dirname(__file__),
        "resources",
        "cylinder_closed_backup.geo"
    )

    # OVERRIDE
    def _get_volume(self):
        return np.pi * self.xy_radius**2 * self.z_length

    # OVERRIDE
    def _get_filling_extent(self):
        return extent(
            min_extent=[
                -self.xy_radius,
                -self.xy_radius,
                0
            ],
            max_extent=[
                self.xy_radius,
                self.xy_radius,
                self.z_length * self.filling_fraction
            ]
        )

    def write_mesh(self, target_path):
        self._write_geo(target_path)
        self._write_stl(target_path)
        self._calc_properties()

    def _write_geo(self, target_path):
        target_geo = os.path.join(target_path, 'new_surface.geo')
        with open(self.source_geo, "r") as template,\
                open(target_geo, "w") as file:
            for line in template:
                if "xy_radius = " in line:
                    line = f"xy_radius = {self.xy_radius};\n"
                elif "z_length = " in line:
                    line = f"z_length = {self.z_length};\n"
                elif "resolution = " in line:
                    line = f"resolution = {self.resolution};\n"
                file.write(line)

    def _write_stl(self, target_path):
        target_geo = os.path.join(
            target_path, 'new_surface.geo'
        )
        target_stl = os.path.join(
            target_path, 'new_surface.stl'
        )
        gmsh.initialize()
        gmsh.open(target_geo)
        gmsh.model.mesh.generate(3)
        gmsh.write(target_stl)
        gmsh.finalize()

    def _calc_properties(self):
        self.inside_location = [
            0, 0, 0.5*self.z_length
        ]
        self.max_extent = extent(
            min_extent=[
                -self.xy_radius,
                -self.xy_radius,
                0
            ],
            max_extent=[
                self.xy_radius,
                self.xy_radius,
                self.z_length
            ]
        )
        self._enlarge_extent()


class ComplexMesh(BaseMesh):

    source_path = File

    # OVERRIDE
    def _get_volume(self):
        return self._calc_volume(np.inf)

    # OVERRIDE
    def _get_filling_extent(self):
        filling_level = (
            self.max_extent["z"]["max"] - self.max_extent["z"]["min"]
        ) * self.filling_fraction + self.max_extent["z"]["min"]
        return extent(
            min_extent=[
                self.max_extent["x"]["min"],
                self.max_extent["y"]["min"],
                self.max_extent["z"]["min"]
            ],
            max_extent=[
                self.max_extent["x"]["max"],
                self.max_extent["y"]["max"],
                filling_level
            ]
        )

    def _calc_volume(self, cutoff_level):
        """
        This method calculates the metric volume of an abstract geometry
        described by an .stl-file. This is achieved by calculating the sum
        of all determinates for each triangular facet, multiplied by 1/6.
        The method is a common mathematical approach for volume calculation
        of objects constructed by delauney-triangulation.

        Please see this publication for further information:

        Zhang, C., & Chen, T. (2001, October).
        Efficient feature extraction for 2D/3D objects in mesh representation.
        In Proceedings 2001 International Conference on Image Processing
        (Cat. No. 01CH37205) (Vol. 3, pp. 935-938). IEEE.

        Link: http://chenlab.ece.cornell.edu/Publication/Cha/icip01_Cha.pdf

        The `cutoff_level` is an experimental feature, which neglects any facet
        above a certain z-value-threshold. This may deliver the opportunity
        to calculate the volume of any arbituary shape until a certain
        `filling_extent`.

        However, to achieve reasonable results, this method needs to be
        improved, since the sum-of-determinantes-approach is only valid
        for closed solid surfaces. A better approximation could be produced
        by passing `gmsh` the points of intersection between regarded shape
        and the horizontal cutoff-surface, which could then be used to
        calculate a closed triangular surface again.

        Parameters
        ----------
        cutoff_level : float
            z-value-threshold until which height the volume of
            the geometry shall be calculated. The metric units
            need to be equal to the ones of the .stl-file.

            (e.g. when `ComplexMesh.units = 'mm'` and
            `cutoff_level = 10`, then the volume of the
            body until a height of 10 mm will be calculated.)

        Returns
        -------
        float
            calculated volume of the abstract .stl-geometry
            underneath the `cutoff_level` in L^3 whereas
            L is the length unit given by `ComplexMesh.units`.

            (e.g. when `ComplexMesh.units = 'mm'`, the given
            volume is in mm^3.)
        """
        with open(self.source_path, "r") as source:
            volume = 0
            points = list()
            for line in source:
                line_split = line.split(sep=" ")
                line_split[-1] = line_split[-1].replace("\n", "")
                if "vertex" in line_split:
                    coords = list(
                        map(
                            float,
                            line_split[-3:]
                        )
                    )
                    if coords[-1] <= cutoff_level:
                        points.append(coords)
                elif "endloop" in line_split \
                        or "outer loop" in line_split:
                    points = list()
                if len(points) == 3:
                    volume += linalg.det(np.array(points))/6
        return abs(volume)

    def cutoff_volume(self, cutoff_value):
        """
        Transforms the relative `cutoff_value` (standing for a
        relative height between 0 and 1) to the absolute cutoff-height
        (e.g. 10 mm) and calculates the correlating true, absolute volume
        underneath this threshold.
        For this method, the .stl-file needs to be inspected first
        with respect to its absolute extent.

        The distinction between relative and absolute cutoff_level
        delivers the opportunity to pass a certain volumetric
        `filling_extent` (e.g. 50% of the body's total volume).

        However, the apparent and true `filling_extent` of a
        complex geometry are unequally distributed over the
        body's height since the correlating `cross_section`
        is not constant.

        Eventually, this function may deliver the true relative
        `filling_extent` of a mold volume with respect to a
        given relative, apparent `filling_extent`.
        Please see `PUFoamDataSource::_calculate_filling_fraction`
        for further information.

        As already mentioned in the docstring of `ComplexMesh::_calc_volume`,
        the validation of this function needs to be improved.

        Parameters
        ----------
        cutoff_level : float
            z-value-threshold until which relative height
            the volume of the geometry shall be calculated.

        Returns
        -------
        float
            calculated volume of the abstract .stl-geometry
            underneath the `cutoff_level` in L^3 whereas
            L is the length unit given by `ComplexMesh.units`.
        """
        if not self.max_extent:
            self._inspect_file()
        cutoff_level = (
            self.z_length*cutoff_value +
            self.max_extent["z"]["min"]
        )
        return self._calc_volume(cutoff_level)

    def inspect_file(self):
        gmsh.initialize()
        gmsh.open(self.source_path)
        bounding_box = gmsh.model.getBoundingBox(2, 1)
        self.max_extent = extent(
            min_extent=bounding_box[:3],
            max_extent=bounding_box[3:]
        )
        gmsh.finalize()
        self._enlarge_extent()
