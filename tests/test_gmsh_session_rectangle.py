import unittest as unittest
from tempfile import TemporaryDirectory
import os
from osp.core.namespaces import emmo, cuba
from osp.wrappers.gmsh_wrapper import GMSHSession, Ontology
from osp.core.utils import import_cuds, sparql


class TestRectangleGMSHSession(unittest.TestCase):


    def setUp(self):
        self.session = GMSHSession()
        import_cuds(
            Ontology.get_ttl("mold_rectangle_mesh"),
            session=self.session
        )

    def test_mesh_generation(self):
        result = self.session.sparql(self.session.mesh_generation_query)
        for binding_set in result(**self.session.mesh_generation_datatypes):
            self.assertTrue(binding_set["inp"].is_a(emmo.Rectangle))
            self.assertTrue(binding_set["x_value"].is_a(emmo.Integer))
            self.assertTrue(binding_set["y_value"].is_a(emmo.Integer))
            self.assertTrue(binding_set["z_value"].is_a(emmo.Integer))
            self.assertEqual(binding_set["z_value"].hasNumericalData, 740)
            self.assertEqual(binding_set["y_value"].hasNumericalData, 930)
            self.assertEqual(binding_set["x_value"].hasNumericalData, 150)
            self.assertEqual(binding_set["x_prefix"], None)
            self.assertEqual(binding_set["y_prefix"], None)
            self.assertEqual(binding_set["z_prefix"], None)
            self.assertEqual(binding_set["xy_radius_value"], None)
            self.assertEqual(binding_set["xy_radius_prefix"], None)

    def test_filling_volume(self):
        result = self.session.sparql(self.session.filling_volume_query)
        for binding_set in result(**self.session.filling_volume_datatypes):
            self.assertTrue(binding_set["inp"].is_a(emmo.Filling))
            self.assertTrue(binding_set["quant"].is_a(emmo.FillingFraction))        
            self.assertTrue(binding_set["real"].is_a(emmo.Real))

    def test_mesh_volume(self):
        result = self.session.sparql(self.session.mesh_volume_query)
        for binding_set in result(**self.session.mesh_volume_datatypes):
            self.assertTrue(binding_set["inp"].is_a(emmo.Rectangle))
            self.assertTrue(binding_set["x_value"].is_a(emmo.Integer))
            self.assertTrue(binding_set["y_value"].is_a(emmo.Integer))
            self.assertTrue(binding_set["z_value"].is_a(emmo.Integer))
            self.assertEqual(binding_set["z_value"].hasNumericalData, 740)
            self.assertEqual(binding_set["y_value"].hasNumericalData, 930)
            self.assertEqual(binding_set["x_value"].hasNumericalData, 150)
            self.assertEqual(binding_set["x_prefix"], None)
            self.assertEqual(binding_set["y_prefix"], None)
            self.assertEqual(binding_set["z_prefix"], None)
            self.assertEqual(binding_set["xy_radius_value"], None)
            self.assertEqual(binding_set["xy_radius_prefix"], None)

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
                }}""",
                self.session
            )
            for binding_set in result(file_name='cuds', file_path='cuds'):
                binding_set["file_name"].hasSymbolData = "test_file"
                binding_set["file_path"].hasSymbolData = temp_dir
            self.session.run()
            self.assertTrue(
                os.path.exists(
                    os.path.join(temp_dir, "test_file.stl")
                )
            )
