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
git clone https://github.com/simphony/GMSHWrapper.git
cd GMSHWrapper
pip install -r requirements.txt
python setup.py install
```
The installation of the namespaces of the `EMMO CFD` into `osp-core` will be automatically executed via `pico install` during this step.
The `GMSHWrapper` is expecting an `osp-core`-version >= 3.5.2. A compatible version will be installed via `pip` during the setup of the `CUDSTranslator`.

See the dependency matrix:


| Python Package | Minimum Version           |
| ------------------- | ----------------- |
| [`osp-core`](https://github.com/simphony/osp-core)                | 3.5.2-beta       |
| [`CUDSTranslator`](https://github.com/simphony/CUDSTranslator.git)                | v0.1       |
| [`EMMO-CFD`](https://github.com/simphony/emmo-cfd.git)                | v0.1       |

## Unittests

The package is providing scripts for unittesting in the `tests`-directories. Run via:

```
python -m unittest
```

## Useage and examples

For the following examples, we are considering the following `python`-imports:

```
from osp.wrappers.gmsh_wrapper.gmsh_session import GMSHSession
from osp.wrappers.gmsh_wrapper.gmsh_cuds_translator import Rectangle, Cylinder, Complex
from osp.core.namespaces import emmo, cuba
``` 

In the first example, we like to generate a `.stl`-file for a rectangle through semantic data structures of `RDF` and `CUDS` within `GMSHSession`.
For the instantiation of `CUDS`-objects, we use the `Rectangle`-class which is a child from the `CUDSTranslator`.


```
# start session
with GMSHSession() as session:

    # initialize wrapper
    wrapper = cuba.Wrapper(session=session)

    # create rectangle
    rec = Rectangle(
        'path/to/my/output/directory',
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

    # get the CUDS if emmo.MeshGenetation
    my_model = rec.get_model()

    # add the CUDS to the wrapper
    wrapper.add(my_model, rel=emmo.hasPart)

    # run the computation
    session.run()

    # get the CUDS of type emmo.MeshGeneration again
    my_model_with_outputs = wrapper.get(oclass=emmo.MeshGeneration)[0]

```
The `python`-variable of `my_model` is the `CUDS`-objects of type `MeshGeneration`, which is linked to the ontologized parameters such as lengths, os-paths, resolution etc.
The variable of `my_model_with_outputs` is the exacly same `CUDS` of type `MeshGeneration`, but with the derived meta-data from the computation. The `.stl` of interest has been generated under the desired output-directory.

In the second example, we would like to generate a `.stl`-file for a cylinder:

```
with GMSHSession() as session:

    # initialize wrapper
    wrapper = cuba.Wrapper(session=session)

    # create cylinder
    cyl = Cylinder(
        'path/to/my/output/directory',
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

    # get the CUDS of type emmo.MeshGenetation
    my_model = cyl.get_model()

    # add the model to the wrapper
    wrapper.add(my_model, rel=emmo.hasPart)

    # run the computation
    session.run()

    # get the CUDS of type emmo.MeshGeneration again
    my_model_with_outputs = wrapper.get(oclass=emmo.MeshGeneration)[0]
```

Now, we may print the results `CUDS` with the results of the computation:

```
from osp.core.utils import pretty_print

pretty_print(my_model_with_outputs)
```

The results of this `pretty_print` may look like that:

```
- Cuds object:
  uuid: 85dd67da-b904-4ee7-9980-7089e709fdec
  type: emmo.MeshGeneration
  superclasses: emmo.Calculation, emmo.Computation, emmo.EMMO, emmo.Holistic, emmo.Item, emmo.MeshGeneration, emmo.Perspective, emmo.Physical, emmo.Process
  description:
    To Be Determined

   |_Relationship emmo.hasInput:
   | -  emmo.GeometryData cuds object:
   |    uuid: fe058209-c4cd-4322-8246-aa80902eadee
   |     |_Relationship emmo.hasQuantitativeProperty:
   |     | -  emmo.Volume cuds object:
   |     |    uuid: cf3bf314-1dc7-40fb-8b8f-dd427949eca6
   |     |     |_Relationship emmo.hasQuantityValue:
   |     |     | -  emmo.Real cuds object:
   |     |     |    uuid: f96b30e3-b447-4268-a974-ebf3b9a4a146
   |     |     |    hasNumericalData: 3e-05
   |     |     |_Relationship emmo.hasReferenceUnit:
   |     |       -  emmo.CubicMetre cuds object:
   |     |          uuid: d755b63f-da2d-4008-96aa-e9fcddfa6043
   |     |_Relationship emmo.hasXLength:
   |     | -  emmo.Length cuds object:
   |     |    uuid: 73cb4f47-9aed-4583-9c75-6930c1769fee
   |     |     |_Relationship emmo.hasQuantityValue:
   |     |     | -  emmo.Real cuds object:
   |     |     |    uuid: 7c3715f8-02b1-426f-a140-f84372fcc6d0
   |     |     |    hasNumericalData: 20
   |     |     |_Relationship emmo.hasReferenceUnit:
   |     |       -  emmo.Metre cuds object:
   |     |       .  uuid: 20cb1885-0a68-4ff0-9dce-8b687264465e
   |     |       .  hasSymbolData: m
   |     |       .   |_Relationship emmo.hasPhysicalDimension:
   |     |       .     -  emmo.LengthDimension cuds object:
   |     |       .        uuid: 5a2fcc3e-bd8d-4114-a4a3-1e279c02f34b
   |     |       -  emmo.Milli cuds object:
   |     |          uuid: df556889-5dfc-443a-9494-01defb51dc0e
   |     |          hasSymbolData: m
   |     |_Relationship emmo.hasYLength:
   |     | -  emmo.Length cuds object:
   |     |    uuid: 96c8ec21-ba56-403e-ba9b-dfbcbd123d09
   |     |     |_Relationship emmo.hasQuantityValue:
   |     |     | -  emmo.Real cuds object:
   |     |     |    uuid: 52544bcc-f8ad-4f22-b13e-1c1d47875303
   |     |     |    hasNumericalData: 10
   |     |     |_Relationship emmo.hasReferenceUnit:
   |     |       -  emmo.Metre cuds object:
   |     |       .  uuid: 8de6607f-30b1-4c23-a4a9-b20964bcc194
   |     |       .  hasSymbolData: m
   |     |       .   |_Relationship emmo.hasPhysicalDimension:
   |     |       .     -  emmo.LengthDimension cuds object:
   |     |       .        uuid: 13389cdb-9feb-45dd-8b6f-903344cbe190
   |     |       -  emmo.Milli cuds object:
   |     |          uuid: 3b838849-091f-4530-8ca5-2c6fcdc31ea6
   |     |          hasSymbolData: m
   |     |_Relationship emmo.hasZLength:
   |     | -  emmo.Length cuds object:
   |     |    uuid: d6060369-1c9e-4324-81dd-9acb539f120f
   |     |     |_Relationship emmo.hasQuantityValue:
   |     |     | -  emmo.Real cuds object:
   |     |     |    uuid: 3c355bcd-37be-4410-8be1-22215b31f397
   |     |     |    hasNumericalData: 150
   |     |     |_Relationship emmo.hasReferenceUnit:
   |     |       -  emmo.Metre cuds object:
   |     |       .  uuid: a0ccb3d1-bc72-401c-80ca-c39304844cbe
   |     |       .  hasSymbolData: m
   |     |       .   |_Relationship emmo.hasPhysicalDimension:
   |     |       .     -  emmo.LengthDimension cuds object:
   |     |       .        uuid: b7a8836e-765d-4653-9383-f10fda339495
   |     |       -  emmo.Milli cuds object:
   |     |          uuid: ea57e239-88f9-4bd1-8c5e-0b92027fa9ab
   |     |          hasSymbolData: m
   |     |_Relationship emmo.standsFor:
   |       -  emmo.Rectangle cuds object:
   |          uuid: c1f05768-bd1c-4533-b16f-39b3029ab653
   |_Relationship emmo.hasOutput:
   | -  emmo.MeshData cuds object:
   |    uuid: d93dc3f2-9157-4ce6-b52b-f47c2f62a669
   |     |_Relationship emmo.hasSign:
   |     | -  emmo.File cuds object:
   |     |    uuid: 28f7a919-1572-4c77-a04d-9e70a0484e32
   |     |     |_Relationship emmo.hasSign:
   |     |       -  emmo.DirectorySequence cuds object:
   |     |       .  uuid: 69ef1fcb-cc15-422d-99da-363cc6d4a2e2
   |     |       .   |_Relationship emmo.hasSpatialDirectPart:
   |     |       .   | -  emmo.Directory cuds object:
   |     |       .   | .  uuid: 25fbcc95-c3e7-41d6-b4a2-3b1a94dc9749
   |     |       .   | .   |_Relationship emmo.hasSign:
   |     |       .   | .     -  emmo.String cuds object:
   |     |       .   | .        uuid: cb949958-9821-4ce5-bc58-e8c86ef5b8d5
   |     |       .   | .        hasSymbolData: tmpy1cnsxds
   |     |       .   |_Relationship emmo.hasSpatialFirst:
   |     |       .     -  emmo.Directory cuds object:
   |     |       .        uuid: 4a329c23-cc43-49d6-98fe-5d8b8f92dd1e
   |     |       .         |_Relationship emmo.hasSign:
   |     |       .         | -  emmo.String cuds object:
   |     |       .         |    uuid: 31836603-ff5b-44da-aa95-cb3506b1998b
   |     |       .         |    hasSymbolData: /tmp
   |     |       .         |_Relationship emmo.hasSpatialNext:
   |     |       .           -  emmo.Directory cuds object:
   |     |       .              uuid: 25fbcc95-c3e7-41d6-b4a2-3b1a94dc9749
   |     |       .              (already printed)
   |     |       -  emmo.STL cuds object:
   |     |       .  uuid: a422a69a-53bd-4bf4-9479-6e7390fbda64
   |     |       -  emmo.String cuds object:
   |     |          uuid: edc8c517-bd9a-46ea-b7e0-a9e50ae48bfc
   |     |          hasSymbolData: new_surface
   |     |_Relationship emmo.hasSpatialDirectPart:
   |       -  emmo.Resolution cuds object:
   |          uuid: d1b7039e-648b-4d30-94ab-820dc1c61971
   |           |_Relationship emmo.hasQuantityValue:
   |           | -  emmo.Real cuds object:
   |           |    uuid: cdca569a-9e40-43ff-9b82-f80bba14f31e
   |           |    hasNumericalData: 1
   |           |_Relationship emmo.hasReferenceUnit:
   |             -  emmo.MeterPerUnitOne cuds object:
   |             .  uuid: 94d610c7-3c76-4193-a691-1ee1df94b2e6
   |             .  hasSymbolData: "m/cell"
   |             .   |_Relationship emmo.hasPhysicalDimension:
   |             .     -  emmo.ResolutionDimension cuds object:
   |             .        uuid: fa706511-42d9-415c-b10d-6715b96f4cf4
   |             -  emmo.Milli cuds object:
   |                uuid: 3e096513-bfbe-4235-b634-6cbf87ba61d2
   |                hasSymbolData: m
   |_Relationship emmo.hasProperParticipant:
     -  emmo.FillingData cuds object:
     .  uuid: 6bdfa23e-77b1-4876-8409-7c6bfb19b845
     .   |_Relationship emmo.hasSpatialDirectPart:
     .     -  emmo.FillingFraction cuds object:
     .     .  uuid: a65b0245-6578-4bb2-9e6e-70f015ea2cc3
     .     .   |_Relationship emmo.hasQuantityValue:
     .     .   | -  emmo.Real cuds object:
     .     .   |    uuid: 6562d18c-a981-458d-83c8-c53db9d56b4e
     .     .   |    hasNumericalData: 0.5
     .     .   |_Relationship emmo.hasReferenceUnit:
     .     .     -  emmo.VolumeFractionUnit cuds object:
     .     .        uuid: 03366452-4cfe-4bae-8ae9-3b9f9df9e0c9
     .     .         |_Relationship emmo.hasPhysicalDimension:
     .     .           -  emmo.DimensionOne cuds object:
     .     .              uuid: a1a778c6-6ecd-4358-85ac-e3d156873859
     -  emmo.GMSH cuds object:
     .  uuid: 32b4a27a-5daf-4611-8cd6-81a49daf8261
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

## License

The package is licensed under GNU General Public License v3.
