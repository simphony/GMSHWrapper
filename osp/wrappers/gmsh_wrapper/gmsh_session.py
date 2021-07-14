import os
from decimal import Decimal
import numpy as np
from osp.core.session import WrapperSession

from osp.core.namespaces import emmo
from osp.wrappers.gmsh_wrapper.gmsh_engine import (
    RectangularMesh, CylinderMesh, ComplexMesh
)
from osp.core.utils import import_cuds
from .ontology import Ontology
from .sparql_backend import GMSHSparqlBackend


class GMSHSession(WrapperSession, GMSHSparqlBackend):

    """
    Session class for GMSH.
    """

    def __str__(self):
        return "OSP-wrapper for GMSH"

    # OVERRIDE
    def __init__(self, engine=None, **kwargs):
        super().__init__(engine, **kwargs)
        self.graph.load(
            Ontology.get_owl("gmshwrapper-inferred")
        )

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        for uid in uids:
            if uid in self._registry:
                yield self._registry.get(uid)
            else:
                yield None

    # OVERRIDE
    def run(self):
        self.run_mesh_generations()
        # TODO
        # self._parse_extent(self._geometry.max_extent)
        # self._parse_extent(self._geometry.filling_extent)
        # self._assign_inside_location()
        # self._assign_volume()
    
    def run_mesh_generations(self):
        for binding_set in self.mesh_generation:
            if binding_set["comp"]:
                if binding_set["inp"].is_a(emmo.Rectangle):
                    write_path = self.prepare_rectangle(binding_set)
                elif binding_set["inp"].is_a(emmo.Cylinder):
                    write_path = self.prepare_cylinder(binding_set)
                self.geometry.write(write_path)

    def prepare_rectangle(self, binding_set):
        parameters = dict()
        for ax in ["x", "y", "z"]:
            if binding_set[f"{ax}_conversion"]:
                parameters[f"{ax}_length"] = self._to_meters(
                    binding_set[f"{ax}_value"],
                    binding_set[f"{ax}_conversion"]
                )
            else:
                parameters[f"{ax}_length"] = binding_set[f"{ax}_value"]
        parameters["unit"] = binding_set["m"]
        self.geometry = Rectangle(**parameters)
        return os.path.join(
            binding_set["file_path"].hasSymbolData, 
            binding_set["file"].hasSymbolData + binding_set["file_format"].hasSymbolData
        )

    def prepare_cylinder(self, binding_set):
        parameters = dict()
        for ax in ["xy_radius", "z"]:
            if binding_set[f"{ax}_conversion"]:
                parameters[f"{ax}_length"] = self._to_meters(
                    binding_set[f"{ax}_value"],
                    binding_set[f"{ax}_conversion"]
                )
            else:
                parameters[f"{ax}_length"] = binding_set[f"{ax}_value"]
        parameters["unit"] = binding_set["m"]
        self.geometry = Cylinder(**parameters)
        return os.path.join(
            binding_set["file_path"].hasSymbolData, 
            binding_set["file"].hasSymbolData + binding_set["file_format"].hasSymbolData
        )

    @property
    def mesh_generation_datatypes(self):
        return {
            key: 'cuds' for key in [
                *['comp', 'inp', 'mesh'],
                *['x', 'x_value', 'x_unit', 'x_prefix', 'x_conversion'],
                *['y', 'y_value', 'y_unit', 'y_prefix', 'y_conversion'],
                *['z', 'z_value', 'z_unit', 'z_prefix', 'z_conversion'],
                *['xy_radius', 'xy_radius_value', 'xy_radius_unit'],
                *['xy_radius_prefix', 'xy_radius_conversion'],
                *['file', 'file_name', 'file_format', 'file_path']
            ]
        }

    @property
    def filling_volume_datatypes(self):
        return {
            key: 'cuds' for key in [
                'comp', 'inp', 'quant', 'real', 'unit'
            ]
        }

    @property
    def mesh_volume_datatypes(self):
        return self.mesh_generation_datatypes

    def _assign_volume(self, geo_data):
        volume = emmo.Volume()
        real = emmo.Real(hasNumericalData=self._geometry.volume)
        unit = emmo.CubicMetre()
        volume.add(real, rel=emmo.hasQuantityValue)
        volume.add(unit, rel=emmo.hasReferenceUnit)
        if self._geometry.units == 'mm':
            volume.add(
                emmo.Milli(hasSymbolData='m'),
                rel=emmo.hasReferenceUnit
            )
        elif self._geometry.units == 'cm':
            volume.add(
                emmo.Centi(hasSymbolData='c'),
                rel=emmo.hasReferenceUnit
            )
        geo_data.add(volume, rel=emmo.hasQuantitativeProperty)

    def _assign_inside_location(self, mesh_data):
        inside_location = mesh_data.get(oclass=emmo.InsidePosition)
        if not inside_location:
            previous_length = list()
            inside_point = emmo.InsidePosition()
            for n, element in enumerate(self._geometry.inside_location):
                length = emmo.Length()
                real = emmo.Real(hasNumericalData=element)
                unit = emmo.Metre(hasSymbolData='m')
                length.add(real, rel=emmo.hasQuantityValue)
                length.add(unit, rel=emmo.hasReferenceUnit)
                if n == 0:
                    relation = emmo.hasSpatialFirst
                elif n == 2:
                    relation = emmo.hasSpatialLast
                else:
                    relation = emmo.hasSpatialDirectPart
                if n > 0:
                    previous_length[-1].add(
                        length,
                        rel=emmo.hasSpatialNext
                    )
                previous_length.append(length)
                inside_point.add(length, rel=relation)
            mesh_data.add(inside_point)

    def _to_meters(self, value, conversion):
        return float(
            np.product(
                (
                    Decimal(value),
                    Decimal(conversion)
                )
            )
        )
