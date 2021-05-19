from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.gmsh_engine import extent
from osp.wrappers.gmsh_wrapper.gmsh_cuds_translator import (
    Rectangle, Cylinder, Complex
)
from osp.core.namespaces import emmo, cuba

import numpy as np
import os
from tempfile import TemporaryDirectory
import unittest as unittest


path = os.path.dirname(os.path.abspath(__file__))


def cuds_to_meta_data(wrapper):
    mold = wrapper.get(oclass=emmo.MeshGeneration)
    geo_data = mold[0].get(oclass=emmo.GeometryData)
    gmsh_data = mold[0].get(oclass=emmo.MeshData)
    fill_data = mold[0].get(oclass=emmo.FillingData)
    inside_point = gmsh_data[0].get(oclass=emmo.InsidePosition)
    volume = geo_data[0].get(oclass=emmo.Volume)
    return [
        wrapper.session._syntactic_extent(gmsh_data[0]),
        wrapper.session._syntactic_extent(fill_data[0]),
        wrapper.session._to_meters(volume[0]),
        wrapper.session._get_vector_data(inside_point[0])
    ]


class TestGMSHSession(unittest.TestCase):

    def test_rectangle(self):
        with GMSHSession() as session, TemporaryDirectory() as temp_dir:

            wrapper = cuba.Wrapper(session=session)

            rec = Rectangle(
                temp_dir,
                values={
                    'x': 20,
                    'y': 10,
                    'z': 150,
                    'filling_fraction': 0.5,
                    'resolution': 1
                },
                units={
                    'lengths': "mm",
                    'resolution': "mm"
                },
                session=session
            )

            wrapper.add(rec.get_model(), rel=emmo.hasPart)
            wrapper.session.run()
            meta_data = cuds_to_meta_data(wrapper)

            stl_path = os.path.join(temp_dir, 'new_surface.stl')
            geo_path = os.path.join(temp_dir, 'new_surface.geo')
            stl_ref = os.path.join(path, 'rectangle_ref.stl')
            geo_ref = os.path.join(path, 'rectangle_ref.geo')

            self.assertTrue(os.path.exists(geo_path))
            self.assertTrue(os.path.exists(stl_path))
            self.compare_files(geo_path, geo_ref)
            self.compare_files(stl_path, stl_ref)

            rec_extent = extent(max_extent=[0.02, 0.01, 0.15])
            filling_extent = extent(max_extent=[0.02, 0.01, 0.075])

            for ax in rec_extent.keys():
                for direction in rec_extent[ax].keys():
                    self.assertEqual(
                        meta_data[0][ax][direction],
                        rec_extent[ax][direction]
                    )
                    self.assertEqual(
                        meta_data[1][ax][direction],
                        filling_extent[ax][direction]
                    )
            self.assertEqual(3e-5, meta_data[2])
            self.assertListEqual([0.01, 0.005, 0.075], meta_data[3])

    def test_cylinder(self):
        with GMSHSession() as session, TemporaryDirectory() as temp_dir:

            wrapper = cuba.Wrapper(session=session)

            cyl = Cylinder(
                temp_dir,
                values={
                    'length': 20,
                    'radius': 5,
                    'filling_fraction': 0.5,
                    'resolution': 0.14
                },
                units={
                    'lengths': "cm",
                    'resolution': "cm"
                },
                session=session
            )

            wrapper.add(cyl.get_model(), rel=emmo.hasPart)
            wrapper.session.run()
            meta_data = cuds_to_meta_data(wrapper)

            stl_path = os.path.join(temp_dir, 'new_surface.stl')
            geo_path = os.path.join(temp_dir, 'new_surface.geo')
            stl_ref = os.path.join(path, 'cylinder_ref.stl')
            geo_ref = os.path.join(path, 'cylinder_ref.geo')

            self.assertTrue(os.path.exists(geo_path))
            self.assertTrue(os.path.exists(stl_path))
            self.compare_files(geo_path, geo_ref)
            self.compare_files(stl_path, stl_ref)

            cyl_extent = extent([-0.05, -0.05, 0], [0.05, 0.05, 0.2])
            filling_extent = extent([-0.05, -0.05, 0], [0.05, 0.05, 0.1])

            for ax in cyl_extent.keys():
                for direction in cyl_extent[ax].keys():
                    self.assertEqual(
                        meta_data[0][ax][direction],
                        cyl_extent[ax][direction]
                    )
                    self.assertEqual(
                        meta_data[1][ax][direction],
                        filling_extent[ax][direction]
                    )
            self.assertAlmostEqual(
                0.2*0.05**2*np.pi,
                meta_data[2],
                delta=1.5e-6
            )
            self.assertListEqual([0, 0, 0.1], meta_data[3])

    def test_complex(self):
        with GMSHSession() as session:

            # initialize wrapper
            wrapper = cuba.Wrapper(session=session)

            # get file path of complex shape
            file_path = os.path.join(
                path, 'cone.stl'
            )

            # create CUDS for complex shape
            comp = Complex(
                file_path,
                values={
                    'inside_point': [0, 0, 5],
                    'filling_fraction': 0.5
                },
                units={'lengths': 'mm'},
                session=session
            )
            wrapper.add(comp.get_model(), rel=emmo.hasPart)
            session.run()

            complex_extent = extent(
                min_extent=[-5.0, -5.0, 0.0],
                max_extent=[5.0, 5.0, 10.0]
            )
            filling_extent = extent(
                min_extent=[-5.0, -5.0, 0.0],
                max_extent=[5.0, 5.0, 5.0]
            )

            meta_data = cuds_to_meta_data(wrapper)
            for ax in complex_extent.keys():
                for direction in complex_extent[ax].keys():
                    self.assertEqual(
                        meta_data[0][ax][direction],
                        complex_extent[ax][direction]
                    )
                    self.assertEqual(
                        meta_data[1][ax][direction],
                        filling_extent[ax][direction]
                    )
            volume = 1/3*(np.pi*0.05**2*0.1)*1e-3
            self.assertAlmostEqual(volume, meta_data[2], delta=1.5e-6)
            self.assertListEqual([0, 0, 5], meta_data[3])

            # volume_cutoff = 1/3*(0.05*(1-0.01))**2*np.pi*(0.01*0.5)

    def compare_files(self, target_path, ref_path):
        with open(target_path, "r") as target, \
                open(ref_path, "r") as ref:
            target_text = "".join(target.read().split())
            ref_text = "".join(ref.read().split())
            self.assertEqual(target_text, ref_text)
