from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.gmsh_cuds_translator import Complex
from osp.core.namespaces import emmo, cuba
from osp.core.utils import pretty_print
import os

file_path = os.path.join(
    os.path.dirname(__file__),
    "cone.stl"
)


with GMSHSession() as session:

    # initialize wrapper
    wrapper = cuba.Wrapper(session=session)

    # create complex
    comp = Complex(
        file_path,
        values={'inside_point': [0, 0, 5], 'filling_fraction': 0.75},
        units={'lengths': 'mm'},
        session=session
    )

    # add the model to the wrapper
    wrapper.add(comp.get_model(), rel=emmo.hasPart)

    # run the session
    print("Run the GMSH computation:")
    session.run()

    # get the mold with the computed output
    computation = wrapper.get(oclass=emmo.MeshGeneration)

    # pretty print the output
    print("Generated meta data:")
    pretty_print(computation[0])
