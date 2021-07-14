from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.ontology import Ontology
from osp.core.utils import pretty_print, import_cuds, sparql
from osp.core.namespaces import emmo
from tempfile import TemporaryDirectory


ontology_file = Ontology.get_ttl("mold_cylinder_mesh")


with GMSHSession() as session, TemporaryDirectory() as temp_dir:

    # import cuds
    import_cuds(ontology_file, session=session)

    result = sparql(f"""SELECT * WHERE {{
        ?computation rdf:type <{emmo.MeshGeneration.iri}>
    }}
    """)
    for binding_set in result(computation='cuds'):
        computation = binding_set["computation"]

    # pretty print the output
    print("\nLet us have a look on the imported individuals:")
    pretty_print(computation)

    # first of all, set the file location
    result = sparql(f"""SELECT * WHERE {{
        ?comp rdf:type <{emmo.MeshGeneration.iri}> .
        ?comp <{emmo.hasOutput.iri}> ?mesh .
        ?file <{emmo.hasProperty.iri}> ?mesh .
        ?file <{emmo.hasProperty.iri}> ?file_name .
        ?file <{emmo.hasProperty.iri}> ?file_format .
        ?file <{emmo.hasProperty.iri}> ?file_path .
        ?file_name rdf:type <{emmo.String.iri}> .
        ?file_path rdf:type <{emmo.UnixPath.iri}> .
        ?file_format rdf:type <{emmo.STL.iri}> 
        }}""",
        session
    )
    for binding_set in result(file='cuds', file_name='cuds', file_path='cuds'):
        binding_set["file_name"].hasSymbolData = "test_file"
        binding_set["file_path"].hasSymbolData = temp_dir

    # pretty print the file
    print("\nSee how we defined our output file")
    pretty_print(binding_set["file"])

    # now, let's set the lengths
    result = sparql(f"""SELECT * WHERE {{
        ?inp rdf:type <{emmo.Rectangle.iri}> .
        ?inp <{emmo.hasXLength.iri}> ?x .
        ?x rdf:type <{emmo.Length.iri}> .
        ?x <{emmo.hasQuantityValue.iri}> ?x_value .
        ?x <{emmo.hasReferenceUnit.iri}> ?x_unit .
        ?x_value rdf:type <{emmo.Integer.iri}>  .
        ?x_unit rdf:type <{emmo.Metre.iri}>  .
        ?inp <{emmo.hasYLength.iri}> ?y .
        ?y rdf:type <{emmo.Length.iri}> .
        ?y <{emmo.hasQuantityValue.iri}> ?y_value .
        ?y <{emmo.hasReferenceUnit.iri}> ?y_unit .
        ?y_value rdf:type <{emmo.Integer.iri}> .
        ?y_unit rdf:type <{emmo.Metre.iri}>  .
        ?inp <{emmo.hasZLength.iri}> ?z .
        ?z rdf:type <{emmo.Length.iri}> .
        ?z <{emmo.hasQuantityValue.iri}> ?z_value .
        ?z <{emmo.hasReferenceUnit.iri}> ?z_unit .
        ?z_value rdf:type <{emmo.Integer.iri}> .
        ?z_unit rdf:type <{emmo.Metre.iri}>  .
    }}""")

    for binding_set in result(xy_radius_value='cuds', z_value='cuds'):
        binding_set["x_value"].hasNumericalData = 10
        binding_set["x_value"].hasNumericalData = 30
        binding_set["z_value"].hasNumericalData = 20 

    # pretty print the output
    print("\nPrint data before mesh generation:")
    pretty_print(computation) 
    
    # run the session
    print("\nRun the GMSH computation:")
    session.run()
