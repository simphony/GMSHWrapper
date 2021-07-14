import os
from tempfile import TemporaryDirectory
from unittest import TestCase
import warnings

import numpy as np

from osp.wrappers.gmsh_wrapper.gmsh_engine import (
    RectangularMesh, CylinderMesh, ComplexMesh, extent
)

path = os.path.dirname(os.path.abspath(__file__))


class TestMeshes(TestCase):

    def setUp(self):
        # Define rectangular mesh and its properties
        self.rectangular = RectangularMesh(
            x_length=20,
            y_length=10,
            z_length=150,
            resolution=1,
            filling_fraction=0.5,
            units="mm"
        )
        self.rectangular_max_extent = extent(
            max_extent=[0.02, 0.01, 0.15]
        )
        self.rectangular_filling_extent = extent(
            max_extent=[0.02, 0.01, 0.075]
        )
        self.rectangular_inside_location = [0.01, 0.005, 0.075]
        self.rectangular_volume = 3e-5
        self.rectangular_stl_ref = os.path.join(
            path, 'rectangle_ref.stl'
        )
        self.rectangular_geo_ref = os.path.join(
            path, 'rectangle_ref.geo'
        )
        # Define cylindrical mesh and its properties
        self.cylinder = CylinderMesh(
            xy_radius_length=5,
            z_length=20,
            resolution=1,
            filling_fraction=0.5,
            units="cm"
        )
        self.cylinder_max_extent = extent(
            [-0.05, -0.05, 0], [0.05, 0.05, 0.2]
        )
        self.cylinder_filling_extent = extent(
            [-0.05, -0.05, 0], [0.05, 0.05, 0.1]
        )
        self.cylinder_inside_location = [0, 0, 0.1]
        self.cylinder_volume = 0.025**2*0.2*np.pi
        self.cylinder_stl_ref = os.path.join(
            path, 'cylinder_ref.stl'
        )
        self.cylinder_geo_ref = os.path.join(
            path, 'cylinder_ref.geo'
        )

        # Define complex mesh and its properties
        self.complex_xy_radius = 5
        self.complex_z_length = 10
        self.complex_cutoff = 0.5
        self.complex = ComplexMesh(
            source_path=os.path.join(path, "cone.stl"),
            inside_location=[0.0, 0.0, 5.0],
            filling_fraction=0.5,
            units="cm"
        )
        self.complex_max_extent = extent(
            [-0.05, -0.05, 0.0], [0.05, 0.05, 0.10]
        )
        self.complex_filling_extent = extent(
            [-0.05, -0.05, 0.0], [0.05, 0.05, 0.05]
        )
        self.complex_inside_location = [0.0, 0.0, 0.05]
        self.complex_volume = 1/3*(np.pi*5**2*10)
        self.complex_volume_cutoff = \
            1/3*(5/10*10*0.5)**2*np.pi*(10*0.5)

    def test_rectangular(self):
        with TemporaryDirectory() as temp_dir:
            stl_path = os.path.join(temp_dir, 'new_surface.stl')
            geo_path = os.path.join(temp_dir, 'new_surface.geo')
            self.rectangular.write_mesh(stl_path)
            self.rectangular.calc_properties()
            self.assertTrue(os.path.exists(stl_path))
            self.assertTrue(os.path.exists(geo_path))
            for ax in self.rectangular_max_extent.keys():
                for direction in self.rectangular_max_extent[ax].keys():
                    self.assertEqual(
                        self.rectangular.max_extent[ax][direction],
                        self.rectangular_max_extent[ax][direction]
                    )
                    self.assertEqual(
                        self.rectangular.filling_extent[ax][direction],
                        self.rectangular_filling_extent[ax][direction]
                    )
            self.assertListEqual(
                self.rectangular.inside_location,
                self.rectangular_inside_location
            )
            self.assertEqual(
                self.rectangular_volume,
                self.rectangular.volume
            )


    def test_cylinder(self):
        with TemporaryDirectory() as temp_dir:
            stl_path = os.path.join(temp_dir, 'new_surface.stl')
            geo_path = os.path.join(temp_dir, 'new_surface.geo')
            self.cylinder.write_mesh(stl_path)
            self.cylinder.calc_properties()
            self.assertTrue(os.path.exists(stl_path))
            self.assertTrue(os.path.exists(geo_path))
            for ax in self.cylinder_max_extent.keys():
                for direction in self.cylinder_max_extent[ax].keys():
                    self.assertEqual(
                        self.cylinder.max_extent[ax][direction],
                        self.cylinder_max_extent[ax][direction]
                    )
                    self.assertEqual(
                        self.cylinder.filling_extent[ax][direction],
                        self.cylinder_filling_extent[ax][direction]
                    )
            self.assertListEqual(
                self.cylinder.inside_location,
                self.cylinder_inside_location
            )
            self.assertAlmostEqual(
                self.cylinder_volume,
                self.cylinder.volume,
                places=1
            )


    def test_complex(self):
        warnings.warn(
                "The destinction between true and "
                "apparent filling_fractions is currently "
                "not supported for ComplexMesh-geometries"
        )
        # NOTE: in case that ComplexMesh::cutoff_volume() will
        # deliver reasonable values in the future, please uncomment
        # the following code:
        # self.assertAlmostEqual(
        #    self.complex_volume_cutoff,
        #    self.complex.cutoff_volume(self.complex_cutoff),
        #    delta=3
        # )
        self.complex.inspect_file()
        for ax in self.complex_max_extent.keys():
            for direction in self.complex_max_extent[ax].keys():
                self.assertAlmostEqual(
                    self.complex.max_extent[ax][direction],
                    self.complex_max_extent[ax][direction],
                )
                self.assertAlmostEqual(
                    self.complex.filling_extent[ax][direction],
                    self.complex_filling_extent[ax][direction],
                )
        self.assertListEqual(
            self.complex.inside_location,
            self.complex_inside_location
        )
        self.assertAlmostEqual(
            self.complex_volume,
            self.complex.volume,
            delta=3
        )
