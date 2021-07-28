from setuptools import setup, find_packages
from setuptools.command.install import install
from packageinfo import VERSION, NAME
from shutil import copytree, rmtree
import subprocess
import os
import json


requirements_file = 'requirements.txt'
wrapper_path = ["osp", "wrappers", "gmsh_wrapper"]
yml_path = ["inferred", "emmo_cfd.yml"]
ontology_submodule = ["ontology", "emmo_cfd"]
ontology_path = [*wrapper_path, "emmo_cfd"]
wrapper_module = ".".join(wrapper_path)
ontology_module = ".".join(ontology_path)


class OntologyInstaller(install):

    path = os.path.dirname(
        os.path.realpath(__file__)
    )

    def run(self):
        self.install_ontology()
    
    def install_ontology(self):
        if os.path.exists(self.ontology_paths[1]):
            rmtree(self.ontology_paths[1])
        copytree(*self.ontology_paths)
        subprocess.run(
            self.installer_command, shell=True, executable='/bin/bash'
        )

    @property
    def installer_command(self):
        return " ".join([
            "pico", "install", self.installer_path
        ])


    @property
    def installer_path(self):
        return os.path.join(*ontology_path, *yml_path)

    @property
    def ontology_paths(self):
        return (
                os.path.join(self.path, *ontology_submodule),
                os.path.join(self.path, *ontology_path)
        )


class OntologyUpdater(OntologyInstaller):

    # OVERRIDE
    @property
    def installer_command(self):
        return " ".join([
            "pico", "install", "--overwrite", self.installer_path,
        ])


class OntologyUninstaller(OntologyInstaller):
    
    # OVERRIDE
    @property
    def installer_command(self):
        return " ".join([
            "pico", "uninstall", self.installer_path,
        ])


class BaseInstaller(OntologyInstaller):

    # OVERRIDE
    def run(self):
        self.install_ontology()
        install.run(self)

    @classmethod
    def install_requires(cls):
        requirement_path = os.path.join(cls.path, requirements_file)
        with open(requirement_path) as file:
            return file.read().splitlines()


class EDMInstaller(BaseInstaller):

    # OVERRIDE
    @property
    def installer_command(self):
        return " ".join([
            *self.edm, "pico", "install", self.installer_path
        ])

    @property
    def edm(self):
            return ["edm", "run", "-e","force-py36","--"]


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='Material Informatics Team, Fraunhofer IWM.',
    keywords='simphony, cuds, Fraunhofer IWM, GMSH',
    description='The wrapper of GMSH for SimPhoNy',
    install_requires=BaseInstaller.install_requires(),
    package_data={
        "osp.wrappers.gmsh_wrapper.resources": ["*"],
        f"{wrapper_module}": ["*json"],
        f"{ontology_module}": ["*ttl"],
        f"{ontology_module}.inferred": ["*ttl", "*owl", "*yml"]
    },
    cmdclass={
        'install_ontology': OntologyInstaller,
        'update_ontology': OntologyUpdater,
        'uninstall_ontology': OntologyUninstaller,
        'install': BaseInstaller,
        'edm_install': EDMInstaller
    },
    packages=find_packages(),
    include_package_data=True
)
