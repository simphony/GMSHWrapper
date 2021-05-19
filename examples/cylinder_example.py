from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.gmsh_cuds_translator import Cylinder
from osp.core.namespaces import emmo, cuba
from osp.core.utils import pretty_print
from tempfile import TemporaryDirectory


with GMSHSession() as session, TemporaryDirectory() as temp_dir:

    # initialize wrapper
    wrapper = cuba.Wrapper(session=session)

    # create cylinder
    cylinder = Cylinder(
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

    wrapper.add(cylinder.get_model(), rel=emmo.hasPart)

    # run the session
    print("Run the GMSH computation:")
    session.run()

    # get the mold with the computed output
    computation = wrapper.get(oclass=emmo.MeshGeneration)

    # pretty print the output
    print("Generated meta data:")
    pretty_print(computation[0])

    # print information of generated .stl-file
    print(f"You can now review the files under {temp_dir}")
