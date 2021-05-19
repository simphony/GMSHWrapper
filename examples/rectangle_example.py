from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.gmsh_cuds_translator import Rectangle
from osp.core.namespaces import emmo, cuba
from osp.core.utils import pretty_print
from tempfile import TemporaryDirectory


with GMSHSession() as session, TemporaryDirectory() as temp_dir:

    # initialize wrapper
    wrapper = cuba.Wrapper(session=session)

    # create rectangle
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

    print("Run the GMSH computation:")
    session.run()

    # get the entity with the computed output
    computation = wrapper.get(oclass=emmo.MeshGeneration)

    # pretty print the output
    print("Generated meta data:")
    pretty_print(computation[0])

    # print information of generated .stl-file
    print(f"You can now review the files under {temp_dir}")
