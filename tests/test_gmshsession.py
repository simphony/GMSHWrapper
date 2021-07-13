import unittest as unittest
from osp.core.namespaces import emmo
from osp.wrappers.gmsh_wrapper import GMSHSession, Ontology
from osp.core.utils import import_cuds


class TestRectangleGMSHSession(unittest.TestCase):


    def setUp(self):
        self.session = GMSHSession()
        import_cuds(
            Ontology.get_ttl("mold_rectangle_mesh"),
            session=self.session
        )

    def test_mesh_generation(self):
        self.assertTrue(
            self.session.mesh_generation.get("comp").is_a(emmo.MeshGeneration)
        )
        self.assertTrue(
            self.session.mesh_generation.get("inp").is_a(emmo.Rectangle)
        )
        self.assertTrue(
            self.session.mesh_generation.get("outp").is_a(emmo.TriangleMesh)
        )

    def test_filling_volume(self):
        self.assertTrue(
            self.session.filling_volume.get("comp").is_a(emmo.VolumeComputation)
        )
        self.assertTrue(
            self.session.filling_volume.get("inp").is_a(emmo.Filling)
        )
        self.assertTrue(
            self.session.filling_volume.get("quant").is_a(emmo.FillingFraction)
        )        
        self.assertTrue(
            self.session.filling_volume.get("real").is_a(emmo.Real)
        )
        self.assertTrue(
            self.session.filling_volume.get("unit").is_a(emmo.RatioQuantity)
        )

    def test_geometry(self):
        self.assertTrue(
            self.session.geometry.get("comp").is_a(emmo.VolumeComputation)
        )
        self.assertTrue(
            self.session.geometry.get("inp").is_a(emmo.Rectangle)
        )
        self.assertTrue(
            self.session.geometry.get("x").is_a(emmo.Length)
        )
        self.assertTrue(
            self.session.geometry.get("x_value").is_a(emmo.Real)
        )
        self.assertTrue(
            self.session.geometry.get("x_unit").is_a(emmo.Metre)
        )
        self.assertEqual(
            self.session.geometry.get("x_value").hasNumericalData,
            150.0
        )
        self.assertTrue(
            self.session.geometry.get("y").is_a(emmo.Length)
        )
        self.assertTrue(
            self.session.geometry.get("y_value").is_a(emmo.Real)
        )        
        self.assertTrue(
            self.session.geometry.get("y_unit").is_a(emmo.Metre)
        )
        self.assertEqual(
            self.session.geometry.get("y_value").hasNumericalData,
            930.0
        )        
        self.assertTrue(
            self.session.geometry.get("z_value").is_a(emmo.Real)
        )
        self.assertTrue(
            self.session.geometry.get("z").is_a(emmo.Length)
        )        
        self.assertTrue(
            self.session.geometry.get("z_unit").is_a(emmo.Metre)
        )
        self.assertEqual(
            self.session.geometry.get("z_value").hasNumericalData,
            740.0
        )
        self.assertEqual(
            self.session.geometry.get("x_prefix"),
            None
        )
        self.assertEqual(
            self.session.geometry.get("y_prefix"),
            None
        )
        self.assertEqual(
            self.session.geometry.get("z_prefix"),
            None
        )
        self.assertEqual(
            self.session.geometry.get("radius"),
            None
        )
        self.assertEqual(
            self.session.geometry.get("radius_value"),
            None
        )
        self.assertEqual(
            self.session.geometry.get("radius_unit"),
            None
        )
        self.assertEqual(
            self.session.geometry.get("radius_prefix"),
            None
        )
