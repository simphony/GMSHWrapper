import unittest as unittest
from tempfile import TemporaryDirectory
import os
from osp.core.namespaces import emmo, cuba
from osp.wrappers.gmsh_wrapper import GMSHSession, Ontology
from osp.core.utils import import_cuds, sparql


class TestCylinderGMSHSession(unittest.TestCase):


    def setUp(self):
        self.session = GMSHSession()
        self.wrapper = cuba.Wrapper(session=self.session)
        cuds=import_cuds(
            Ontology.get_ttl("mold_cylinder_mesh"),
            session=self.session
        )

    def test_mesh_generation(self):
        result = self.session.sparql(self.session.mesh_generation_query)
        for binding_set in result(**self.session.mesh_generation_datatypes):
            self.assertTrue(binding_set["inp"].is_a(emmo.Cylinder))
            self.assertTrue(binding_set["z_value"].is_a(emmo.Integer))
            self.assertTrue(binding_set["xy_radius_value"].is_a(emmo.Integer))
            self.assertEqual(binding_set["z_value"].hasNumericalData, 930)
            self.assertEqual(binding_set["xy_radius_value"].hasNumericalData, 150)
            self.assertEqual(binding_set["x_value"], None)
            self.assertEqual(binding_set["y_value"], None)
            self.assertEqual(binding_set["x_prefix"], None)
            self.assertEqual(binding_set["y_prefix"], None)
            self.assertEqual(binding_set["z_prefix"], None)

    def test_filling_volume(self):
        result = self.session.sparql(self.session.filling_volume_query)
        for binding_set in result(**self.session.filling_volume_datatypes):
            self.assertTrue(binding_set["inp"].is_a(emmo.Filling))
            self.assertTrue(binding_set["quant"].is_a(emmo.FillingFraction))
            self.assertTrue(binding_set["real"].is_a(emmo.Real))

    def test_mesh_volume(self):
        result = self.session.sparql(self.session.mesh_volume_query)
        for binding_set in result(**self.session.mesh_volume_datatypes):
            self.assertTrue(binding_set["inp"].is_a(emmo.Cylinder))
            self.assertTrue(binding_set["z_value"].is_a(emmo.Integer))
            self.assertTrue(binding_set["xy_radius_value"].is_a(emmo.Integer))
            self.assertEqual(binding_set["z_value"].hasNumericalData, 930)
            self.assertEqual(binding_set["xy_radius_value"].hasNumericalData, 150)
            self.assertEqual(binding_set["x_value"], None)
            self.assertEqual(binding_set["y_value"], None)
            self.assertEqual(binding_set["x_prefix"], None)
            self.assertEqual(binding_set["y_prefix"], None)
            self.assertEqual(binding_set["z_prefix"], None)

    def test_run_session(self):
        with TemporaryDirectory() as temp_dir:
            result = sparql(f"""SELECT * WHERE {{
                ?mesh <{emmo.standsFor.iri}> ?inp .
                ?file <{emmo.hasProperty.iri}> ?mesh ;
                      <{emmo.hasProperty.iri}> ?file_name ;
                      <{emmo.hasProperty.iri}> ?file_format ;
                      <{emmo.hasProperty.iri}> ?file_path .
                ?file_name rdf:type <{emmo.String.iri}> .
                ?file_path rdf:type <{emmo.UnixPath.iri}> .
                ?file_format rdf:type <{emmo.STL.iri}> 
                }}""",
                self.session
            )
            for binding_set in result(file_name='cuds', file_path='cuds', file_format='cuds'):
                binding_set["file_name"].hasSymbolData = "test_file"
                binding_set["file_path"].hasSymbolData = temp_dir

            self.session.run()

            result = sparql(f"""SELECT * WHERE {{
                ?comp rdf:type <{emmo.MeshParameterConversion.iri}> ;
                            <{emmo.hasInput.iri}> ?inp ;
                            <{emmo.hasOutput.iri}> ?outp .
                ?inp rdf:type <{emmo.TriangleMesh.iri}> .
                ?outp rdf:type <{emmo.CartesianMesh.iri}> ;
                      <{emmo.hasNumberOfXElements}> ?x_elements ;
                      <{emmo.hasNumberOfYElements}> ?y_elements ;
                      <{emmo.hasNumberOfZElements}> ?z_elements .
                ?x_elements rdf:type <{emmo.NumberOfElements.iri}> ;
                            <{emmo.hasQuantityValue.iri}> ?x_elements_value ; 
                            <{emmo.hasReferenceUnit.iri}> <{emmo.PureNumberUnit.iri}> .
                ?y_elements rdf:type <{emmo.NumberOfElements.iri}> ;
                            <{emmo.hasQuantityValue.iri}> ?y_elements_value ; 
                            <{emmo.hasReferenceUnit.iri}> <{emmo.PureNumberUnit.iri}> .
                ?z_elements rdf:type <{emmo.NumberOfElements.iri}> ;
                            <{emmo.hasQuantityValue.iri}> ?z_elements_value ; 
                            <{emmo.hasReferenceUnit.iri}> <{emmo.PureNumberUnit.iri}> .
                ?x_elements_value rdf:type <{emmo.Integer.iri}> . 
                ?y_elements_value rdf:type <{emmo.Integer.iri}> . 
                ?z_elements_value rdf:type <{emmo.Integer.iri}> . 
                }}""",
                self.session
            )

            for binding_set in result(x_elements_value='cuds',
                                      y_elements_value='cuds',
                                      z_elements_value='cuds'):
                self.assertEqual(binding_set["x_elements_value"].hasNumericalData, 30)
                self.assertEqual(binding_set["y_elements_value"].hasNumericalData, 30)
                self.assertEqual(binding_set["z_elements_value"].hasNumericalData, 93)

            self.assertTrue(
                os.path.exists(
                    os.path.join(temp_dir, "test_file.stl")
                )
            )
