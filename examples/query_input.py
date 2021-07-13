from osp.core.namespaces import emmo, cuba
from osp.wrappers.gmsh_wrapper import GMSHSession, Ontology
from osp.core.utils import import_cuds, sparql, pretty_print
from osp.core.ontology.namespace_registry import namespace_registry


cuds=import_cuds(Ontology.get_ttl("mold_rectangle_mesh"))
for i in cuds:
    if i.is_a(emmo.VolumeComputation):
        pretty_print(i)

result = sparql(f"""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>           
        PREFIX owl: <http://www.w3.org/2002/07/owl#>        
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>     
        SELECT *
        WHERE {{
            ?comp rdf:type <{emmo.VolumeComputation.iri}> .
            ?comp <{emmo.hasInput.iri}> ?inp .
            ?inp rdf:type ?oclass .
            ?oclass rdfs:subClassOf* <{emmo.TwoManifold.iri}>
        }}
    """)

for i in result(inp='cuds'):
    print(i["inp"])