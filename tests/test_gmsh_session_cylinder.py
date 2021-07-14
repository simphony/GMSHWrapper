import unittest as unittest
from osp.core.namespaces import emmo
from osp.wrappers.gmsh_wrapper import GMSHSession, Ontology
from osp.core.utils import import_cuds


class TestCylinderGMSHSession(unittest.TestCase):


    def setUp(self):
        self.session = GMSHSession()
        cuds=import_cuds(
            Ontology.get_ttl("mold_cylinder_mesh"),
            session=self.session
        )

    def test_mesh_generation(self):
        for binding_set in self.session.mesh_generation:
            self.assertTrue(binding_set["comp"].is_a(emmo.MeshGeneration))
            self.assertTrue(binding_set["inp"].is_a(emmo.Cylinder))
            self.assertTrue(binding_set["mesh"].is_a(emmo.TriangleMesh))
            self.assertTrue(binding_set["z"].is_a(emmo.Length))
            self.assertTrue(binding_set["z_unit"].is_a(emmo.Metre))
            self.assertEqual(binding_set["z_value"].hasNumericalData, 930.0)
            self.assertTrue(binding_set["z_value"].is_a(emmo.Real))
            self.assertTrue(binding_set["xy_radius"].is_a(emmo.Length))
            self.assertTrue(binding_set["xy_radius_value"].is_a(emmo.Real))
            self.assertTrue(binding_set["xy_radius_unit"].is_a(emmo.Metre))
            self.assertEqual(binding_set["x"], None)
            self.assertEqual(binding_set["y"], None)
            self.assertEqual(binding_set["x_value"], None)
            self.assertEqual(binding_set["y_value"], None)
            self.assertEqual(binding_set["x_unit"], None)
            self.assertEqual(binding_set["y_unit"], None)
            self.assertEqual(binding_set["x_prefix"], None)
            self.assertEqual(binding_set["y_prefix"], None)
            self.assertEqual(binding_set["z_prefix"], None)
            self.assertEqual(binding_set["x_conversion"], None)
            self.assertEqual(binding_set["y_conversion"], None)
            self.assertEqual(binding_set["z_conversion"], None)

    def test_filling_volume(self):
        for binding_set in self.session.filling_volume:
            self.assertTrue(binding_set["comp"].is_a(emmo.VolumeComputation))
            self.assertTrue(binding_set["inp"].is_a(emmo.Filling))
            self.assertTrue(binding_set["quant"].is_a(emmo.FillingFraction))        
            self.assertTrue(binding_set["real"].is_a(emmo.Real))
            self.assertTrue(binding_set["unit"].is_a(emmo.RatioQuantity))

    def test_mesh_volume(self):
        for binding_set in self.session.mesh_volume:
            self.assertTrue(binding_set["comp"].is_a(emmo.VolumeComputation))
            self.assertTrue(binding_set["inp"].is_a(emmo.Cylinder))
            self.assertTrue(binding_set["z"].is_a(emmo.Length))
            self.assertTrue(binding_set["z_unit"].is_a(emmo.Metre))
            self.assertEqual(binding_set["z_value"].hasNumericalData, 930.0)
            self.assertTrue(binding_set["z_value"].is_a(emmo.Real))
            self.assertTrue(binding_set["xy_radius"].is_a(emmo.Length))
            self.assertTrue(binding_set["xy_radius_value"].is_a(emmo.Real))
            self.assertTrue(binding_set["xy_radius_unit"].is_a(emmo.Metre))
            self.assertEqual(binding_set["x"], None)
            self.assertEqual(binding_set["y"], None)
            self.assertEqual(binding_set["x_value"], None)
            self.assertEqual(binding_set["y_value"], None)
            self.assertEqual(binding_set["x_unit"], None)
            self.assertEqual(binding_set["y_unit"], None)
            self.assertEqual(binding_set["x_prefix"], None)
            self.assertEqual(binding_set["y_prefix"], None)
            self.assertEqual(binding_set["z_prefix"], None)
            self.assertEqual(binding_set["x_conversion"], None)
            self.assertEqual(binding_set["y_conversion"], None)
            self.assertEqual(binding_set["z_conversion"], None)

    def test_run_session(self):
        with TemporaryDirectory() as temp_dir:
            result = sparql(f"""SELECT * WHERE {{
                ?mesh <{emmo.standsFor.iri}> ?inp .
                ?file <{emmo.hasProperty.iri}> ?mesh .
                ?file <{emmo.hasProperty.iri}> ?file_name .
                ?file <{emmo.hasProperty.iri}> ?file_format .
                ?file <{emmo.hasProperty.iri}> ?file_path .
                ?file_name rdf:type <{emmo.String.iri}> .
                ?file_path rdf:type <{emmo.UnixPath.iri}> .
                ?file_format rdf:type <{emmo.STL.iri}> 
                }}
                """,
                self.session
            )
            for binding_set in result(file_name='cuds', file_path='cuds', file_format='cuds'):
                binding_set["file_name"].hasSymbolData = "test_file"
                binding_set["file_path"].hasSymbolData = temp_dir
            self.session.run()
