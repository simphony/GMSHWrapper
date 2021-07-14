# GMSHWrapper

Native implementation of the wrappers and translators by the SimPhoNy team at [Fraunhofer IWM](https://www.iwm.fraunhofer.de/).

The `GMSHWrapper` is a [`SimPhoNy`](https://github.com/simphony)-package for ontologized modelling of finite-element geometries (`.stl`-format), volume calculation and mesh calculations of mold-models as inputs for CFD-simulations, using [`GMSH`](https://gmsh.info/).

*Contact*: [Matthias Büschelberger](mailto:matthias.bueschelberger@iwm.fraunhofer.de) from the Material Informatics team, Fraunhofer IWM

## Index
- [GMSHWrapper](#gmshwrapper)
  - [Capabilities](#capabilities)
  - [Installation](#installation)
  - [Unittests](#unittests)
  - [Useage and examples](#useage-and-examples)
  - [Run as flask-app](#run-as-flask-app)
  - [Run with docker](#run-with-docker)
  - [License](#license)

## Capabilities

The `GMSHWrapper` is currently able to automatically generate meshes for rectangles and cylinders by providing the numerical values of their lengths and resolution. The metric SI-units of these quantities (such as `mm`, `cm` or `dm`) will be defined via `String`-input. If the want to model the filling of a mold which is represented by a mesh, you can also provide a numerical value for the `filling_fraction` between 0-1. This value is associated to the relative z-value of the domain.

Apart from that, the wrapper provides the functionality to read an already available `.stl`-file with any arbitrary geometry-abstraction and to calculate its bulk 3D-volume as well as the volume of the 3D-mold-filling. This is achieved by calculating the sum of all determinates for each triangular facet after [Zhang & Chen (2001)](http://chenlab.ece.cornell.edu/Publication/Cha/icip01_Cha.pdf).

In addition to the volume-calculations, the maximum extents in `xyz`-directions of these forms are provided in the resulting [`CUDS`](https://simphony.readthedocs.io/en/latest/jupyter/cuds_api.html)-objects after the execution of the wrapper.

We recommend to use the `GMSHWrapper` in combination with the `CFDWrapper` for `SimPhoNy`, since the ontologized mesh-data in the form of `CUDS` can be used in order to automatically create domains for CFD-simulations with e.g. [`OpenFOAM®`](https://www.openfoam.com/).


## Installation
Please use a `git`-version >= 2.20 and `python` >= 3.6.12 for the installation.

### Step 1

We tested the wrapper for the `GMSH`-backend mainly on `Ubuntu`>=18.04 and `Debian GNU/Linux 10`. If you consider to use the same `os`, you will need to install the following additional packages via `apt-get`:

```
apt-get update && apt-get install -y ffmpeg libsm6 libxext6 libglu1-mesa-dev libgl1-mesa-glx
```

### Step 2

Now clone the wrapper-repository.

```
git clone --recurse-submodules https://github.com/simphony/GMSHWrapper.git
cd GMSHWrapper
pip install -r requirements.txt
python setup.py install
```
The installation of the namespaces of the `EMMO CFD` into `osp-core` will be automatically executed via `pico install` during this step.
The `GMSHWrapper` is expecting an `osp-core`-version >= 3.5.2. A compatible version will be installed via `pip` during the setup of the `CUDSTranslator`.

See the dependency matrix:


| Python Package | Minimum Version           |
| ------------------- | ----------------- |
| [`osp-core`](https://github.com/simphony/osp-core.git)                | dev       |
| [`EMMO-CFD`](https://github.com/simphony/emmo-cfd.git)                | dev       |

## Unittests

The package is providing scripts for unittesting in the `tests`-directories. Run via:

```
python -m unittest
```

## Useage and examples

For the following example, we are considering the following `python`-imports:

```
from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.ontology import Ontology
from osp.core.utils import pretty_print, import_cuds, sparql
from osp.core.namespaces import emmo
from tempfile import TemporaryDirectory
``` 

Now, we like to generate a `.stl`-file for a cylinder through semantic data structures of `RDF` and `CUDS` within `GMSHSession`.


```
# get path of ontology-file with individuals to be imported
ontology_file = Ontology.get_ttl("mold_cylinder_mesh")

# start the session and a temporary directory
with GMSHSession() as session, TemporaryDirectory() as temp_dir:

    # import cuds
    import_cuds(ontology_file, session=session)

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

    # now, let's set the lengths
    result = sparql(f"""SELECT * WHERE {{
        ?inp rdf:type <{emmo.Cylinder.iri}> .
        ?inp <{emmo.hasXYRadius.iri}> ?xy_radius .
        ?xy_radius rdf:type <{emmo.Length.iri}> .
        ?xy_radius <{emmo.hasQuantityValue.iri}> ?xy_radius_value .
        ?xy_radius <{emmo.hasReferenceUnit.iri}> ?xy_radius_unit .
        ?xy_radius_value rdf:type <{emmo.Integer.iri}> .
        ?xy_radius_unit rdf:type <{emmo.Metre.iri}>  .
        ?inp <{emmo.hasZLength.iri}> ?z .
        ?z rdf:type <{emmo.Length.iri}> .
        ?z <{emmo.hasQuantityValue.iri}> ?z_value .
        ?z <{emmo.hasReferenceUnit.iri}> ?z_unit .
        ?z_value rdf:type <{emmo.Integer.iri}> .
        ?z_unit rdf:type <{emmo.Metre.iri}>
    }}""")
    for binding_set in result(xy_radius_value='cuds', z_value='cuds'):
        binding_set["xy_radius_value"].hasNumericalData = 10
        binding_set["z_value"].hasNumericalData = 20 

    
    # run the session
    session.run()

    # query for the meshgeneration-entity
    result = sparql(f"""SELECT * WHERE {{
        ?computation rdf:type <{emmo.MeshGeneration.iri}>
    }}
    """)
    for binding_set in result(computation='cuds'):
        computation = binding_set["computation"]

    # pretty print the output
    pretty_print(computation)

```

The classical output of the GMSH-computation looks like that:
```
Info    : Reading '/tmp/tmpfo6c9ubd/new_surface.geo'...
Info    : Done reading '/tmp/tmpfo6c9ubd/new_surface.geo'
Info    : Meshing 1D...
Info    : [  0%] Meshing curve 1 (Circle)
Info    : [ 10%] Meshing curve 2 (Circle)
Info    : [ 20%] Meshing curve 3 (Circle)
Info    : [ 30%] Meshing curve 4 (Circle)
Info    : [ 40%] Meshing curve 8 (Extruded)
Info    : [ 50%] Meshing curve 9 (Extruded)
Info    : [ 50%] Meshing curve 10 (Extruded)
Info    : [ 60%] Meshing curve 11 (Extruded)
Info    : [ 70%] Meshing curve 13 (Extruded)
Info    : [ 80%] Meshing curve 14 (Extruded)
Info    : [ 90%] Meshing curve 18 (Extruded)
Info    : [100%] Meshing curve 22 (Extruded)
Info    : Done meshing 1D (Wall 0.0051848s, CPU 0.004891s)
Info    : Meshing 2D...
Info    : [  0%] Meshing surface 6 (Transfinite)
Info    : [ 20%] Meshing surface 15 (Extruded)
Info    : [ 40%] Meshing surface 19 (Extruded)
Info    : [ 50%] Meshing surface 23 (Extruded)
Info    : [ 70%] Meshing surface 27 (Extruded)
Info    : [ 90%] Meshing surface 28 (Extruded)
Info    : Done meshing 2D (Wall 0.365484s, CPU 0.365482s)
Info    : Meshing 3D...
Info    : Meshing volume 1 (Extruded)
Info    : Done meshing 3D (Wall 3.34237s, CPU 3.21258s)
Info    : Optimizing mesh...
Info    : Done optimizing mesh (Wall 0.0334727s, CPU 0.033285s)
Info    : 448989 nodes 470002 elements
Info    : Writing '/tmp/tmpfo6c9ubd/test_file.stl'...
Info    : Done writing '/tmp/tmpfo6c9ubd/test_file.stl'
```

As you may notice, the file can be found under `/tmp/tmpfo6c9ubd/test_file.stl`.

The results of the last `pretty_print` (CUDS of the `emmo.MeshGeneration`) may look like that:

```
- Cuds object:
  uid: 9a252bd5-86fe-413f-aea4-d80d2deb2b44
  type: emmo.MeshGeneration
  superclasses: emmo.Calculation, emmo.Computation, emmo.EMMO, emmo.Holistic, emmo.Item, emmo.MeshGeneration, emmo.Perspective, emmo.Physical, emmo.Process
  description:
    To Be Determined

   |_Relationship emmo.hasInput:
   | -  emmo.Cylinder cuds object:
   |    uid: b96002fb-9b61-4ad4-802c-710aa70ce682
   |     |_Relationship emmo.hasXYRadius:
   |     | -  emmo.Length cuds object:
   |     |    uid: 42eaf8c8-4e21-415c-a0fd-914a3e19f85b
   |     |     |_Relationship emmo.hasQuantityValue:
   |     |     | -  emmo.Integer cuds object:
   |     |     |    uid: 5358418b-8b30-4ca9-baea-0e8c4fd7a1f6
   |     |     |    hasNumericalData: 150
   |     |     |_Relationship emmo.hasReferenceUnit:
   |     |       -  emmo.Metre cuds object:
   |     |          uid: 271061e4-defe-49b2-b9fd-26cc68cb8990
   |     |          hasSymbolData: m
   |     |_Relationship emmo.hasZLength:
   |     | -  emmo.Length cuds object:
   |     |    uid: dfa298c0-2952-4239-8ad4-7c2b26db2870
   |     |     |_Relationship emmo.hasQuantityValue:
   |     |     | -  emmo.Integer cuds object:
   |     |     |    uid: 988de696-467d-4a25-93f2-08b663e24ee5
   |     |     |    hasNumericalData: 930
   |     |     |_Relationship emmo.hasReferenceUnit:
   |     |       -  emmo.Metre cuds object:
   |     |          uid: 36033e56-3250-4987-9261-7a6d187b66b8
   |     |          hasSymbolData: m
   |     |_Relationship emmo.standsFor:
   |       -  emmo.Mold cuds object:
   |          uid: 6be5c0d5-77a3-4fc9-b3be-44cf7eb46aca
   |           |_Relationship emmo.hasSpatialDirectPart:
   |             -  emmo.Filling cuds object:
   |                uid: b7e71658-dc81-4ef8-beb1-8fe705d57930
   |                 |_Relationship emmo.hasQuantitativeProperty:
   |                   -  emmo.FillingFraction cuds object:
   |                      uid: 3b2ac035-6494-435e-94a0-bf6049183083
   |                       |_Relationship emmo.hasQuantityValue:
   |                       | -  emmo.Real cuds object:
   |                       |    uid: 0842b20e-e1b2-451d-ac3c-0ebc6164f138
   |                       |_Relationship emmo.hasReferenceUnit:
   |                         -  emmo.RatioQuantity cuds object:
   |                            uid: ccbb0b6e-5262-454e-b8f7-aa51b7f24229
   |_Relationship emmo.hasOutput:
   | -  emmo.TriangleMesh cuds object:
   |    uid: 26bac46a-b75a-484e-a356-59a8661e1cfc
   |     |_Relationship emmo.standsFor:
   |       -  emmo.Cylinder cuds object:
   |          uid: b96002fb-9b61-4ad4-802c-710aa70ce682
   |          (already printed)
   |_Relationship emmo.hasProperParticipant:
     -  emmo.GMSH cuds object:
     .  uid: 0ae73cf7-b72a-458e-9ffa-d5f49a969196
```
Further details are provided in the `examples`-directory of this repository.

For the further use of the CUDS-objects with respect to `osp`-wrappers for the semantic interoperability to third-party tools, please visit the [SimPhoNy-Organisation on GitHub](https://github.com/simphony) or the [Fraunhofer-GitLab](https://gitlab.cc-asp.fraunhofer.de).


## Run as flask-app

If you want to run the `GMSHWrapper` as a `flask`-app, we can provide you also runner-script with this repository. For the following steps, we assume that you already setup the wrapper and its dependencies as explained under the **Installation**-section. 
If so, then simply run:

```
cd <gmshwrapper-repo>/flask
python RUN.py
```

The service will then listen under `0.0.0.0:7000`.

From now on, you may run the wrapper remotely and instantiate the `CUDS` locally. In order to send the `CUDS` to the server with the wrapper listening via `flask`, you may simply use the `TransportSessionClient` from `osp.core` and the `WrapperSession` as its base, since the `GMSHSession` is also based on the `WrapperSession`. 

First of all, import the following lines:

```
from osp.core.session.transport.transport_session_client import TransportSessionClient
from osp.core.session import WrapperSession
```

The examples shown in the **Useage and examples**-section also work with the `flask`-app, you simply have to exchange the following lines:

```
with TransportSessionClient(WrapperSession, '0.0.0.0', 7000) as session:
    wrapper = cuba.Wrapper(session=session)

    ...
    ...
    ...
```

With `0.0.0.0` and `7000`, we define the host and port, the `flask`-server the wrapper is listening to. The rest of the example(s) stay(s) exactly the same.

## Run with Docker

We provide a Docker image for the simplified and automated setup of this wrapper. You should have `Docker`>=20.10.5 installed on your `os`.

For building the image, simply run the following command under the *top level directory* of the wrapper-repository:

```
docker build -t <wrapper-image-name>:<tag> .
```

If you want to run the built image, simply run:

```
docker run -dit <wrapper-image-name>:<tag>
```
The container is then providing the mentioned `flask`-app from above as `ENTRYPOINT` under its port `7000`.

## Related projects

- [FORCE](https://www.the-force-project.eu/); Grant agreement number: 721027 <img src="https://www.the-force-project.eu/content/dam/iwm/the-force-project/images/Force_Logo.png" width="60">
- [OntoTrans](https://ontotrans.eu/); Grant agreement number: 862136 <img src="https://ontotrans.eu/wp-content/uploads/2020/05/ot_logo_rosa_gro%C3%9F.svg"  width="60">

## License

The package is licensed under GNU General Public License v3.
