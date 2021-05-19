from setuptools import setup, find_packages
from setuptools.command.install import install
from packageinfo import VERSION, NAME
import os
import subprocess
import emmo_cfd

path = os.path.dirname(os.path.realpath(__file__))
requirementPath = os.path.join(path, 'requirements.txt')


with open(requirementPath) as file:
    install_requires = file.read().splitlines()


class _install(install):

    def run(self):
        subprocess.run(
            [
                "pico",
                "install",
                emmo_cfd.get_file("gmshwrapper", ".yml"),
                "--overwrite"
            ]
        )
        install.run(self)


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='Material Informatics Team, Fraunhofer IWM.',
    keywords='simphony, cuds, Fraunhofer IWM, GMSH',
    description='The wrapper of GMSH for SimPhoNy',
    install_requires=install_requires,
    package_data={
        "osp.wrappers.gmsh_wrapper.resources": ["*"]
    },
    cmdclass={
        'install': _install
    },
    include_package_data=True,
    packages=find_packages()
)
