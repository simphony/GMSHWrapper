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
        self.run_mesh_conversions()
        # TODO
        # self._parse_extent(self._geometry.max_extent)
        # self._parse_extent(self._geometry.filling_extent)
        # self._assign_inside_location()
        # self._assign_volume()
    
    def run_mesh_generations(self):
        result = self.sparql(self.mesh_generation_query)
        for binding_set in result(**self.mesh_generation_datatypes):
            if binding_set["inp"]:
                if binding_set["inp"].is_a(emmo.Rectangle):
                    self._prepare_rectangle(binding_set)
                elif binding_set["inp"].is_a(emmo.Cylinder):
                    self._prepare_cylinder(binding_set)
                self.geometry.write_mesh(
                    self._set_full_target_path(binding_set)
                )

    def run_mesh_conversions(self):
        result = self.sparql(self.mesh_conversion_query)
        for binding_set in result(**self.mesh_conversion_datatypes):
            if binding_set["inp"]:
                self._add_number_of_elements(binding_set)

    def _add_number_of_elements(self, binding_set):
        for axis in self.geometry.hexaedric_extent.keys():
            rel = emmo[f"hasNumberOf{axis.upper()}Elements"]
            max_value = self.geometry.hexaedric_extent[axis]["max"]
            min_value = self.geometry.hexaedric_extent[axis]["min"]
            integer = int(max_value - min_value)
            n_elements = emmo.hasNumberOfElements()
            unit = emmo.PureNumberUnit()            
            n_elements_integer = emmo.Integer(hasNumericalData=integer)
            n_elements.add(n_elements_integer, rel=emmo.hasQuantityValue)
            n_elements.add(unit, rel=emmo.hasReferenceUnit)
            binding_set["outp"].add(n_elements, rel=rel)

    def _prepare_rectangle(self, binding_set):
        self.geometry = RectangularMesh(
            **self._set_engine_inputs(binding_set, ["x", "y", "z"])
        )
 
    def _prepare_cylinder(self, binding_set):
        self.geometry = CylinderMesh(
            **self._set_engine_inputs(binding_set, ["xy_radius", "z"])
        )

    def _set_engine_inputs(self, binding_set, axis_list):
        parameters = dict()
        prefix = dict()
        for ax in axis_list:
            parameters[f"{ax}_length"] = int(binding_set[f"{ax}_value"].hasNumericalData)
            ax_prefix = binding_set[f"{ax}_prefix"]
            if ax_prefix:
                prefix[ax_prefix.oclass] = ax_prefix
        prefix = list(prefix.values())
        if len(prefix) > 1:
            raise ValueError(
                f"""Instances of <{emmo.Length.iri}> must feature the same SiPrefixes.
            Passed prefixes are: {prefix}""")
        elif len(prefix) == 1:
            parameters["units"] = f"{prefix.hasSymbolData}m"
        else:
            parameters["units"] = "m"
        return parameters

    def _set_full_target_path(self, binding_set):
        return os.path.join(
            binding_set["file_path"].hasSymbolData, 
            binding_set["file_name"].hasSymbolData + binding_set["file_format"].hasSymbolData
        )

    def get_conversion(self, iri):
        cuds_query = self.session.load_from_iri(iri)
        result = self.sparql(self.get_restriction(iri))
        return [cuds.first(), next(result)["conversion"]]

    @property
    def mesh_generation_datatypes(self):
        parameters = [
            'inp', 'file_name', 'file_format', 'file_path',
            'x_value', 'y_value', 'z_value', 'xy_radius_value', 
            'x_prefix', 'y_prefix', 'z_prefix', 'xy_radius_prefix'
        ]
        datatypes = [*['cuds']*8, *[self.get_conversion]*4]
        mapping = zip(
            {key: None for key in parameters},
            datatypes
        )
        return dict(mapping)

    @property
    def mesh_conversion_datatypes(self):
        parameters = [
            'inp', 'outp', 'resolution_value', 'resolution_unit'
        ]
        datatypes = [*['cuds']*8, *[self.get_conversion]*4]
        mapping = zip(
            {key: None for key in parameters},
            datatypes
        )
        return dict(mapping)

    @property
    def filling_volume_datatypes(self):
        return {
            key: 'cuds' for key in ['inp', 'quant', 'real']
        }

    @property
    def mesh_volume_datatypes(self):
        return self.mesh_generation_datatypes

    def _assign_volume(self, enity):
        volume = emmo.Volume()
        real = emmo.Real(hasNumericalData=self.geometry.volume)
        unit = emmo.CubicMetre()
        volume.add(real, rel=emmo.hasQuantityValue)
        volume.add(unit, rel=emmo.hasReferenceUnit)
        if self.geometry.units == 'mm':
            volume.add(
                emmo.Milli(hasSymbolData='m'),
                rel=emmo.hasReferenceUnit
            )
        elif self.geometry.units == 'cm':
            volume.add(
                emmo.Centi(hasSymbolData='c'),
                rel=emmo.hasReferenceUnit
            )
        entity.add(volume, rel=emmo.hasQuantitativeProperty)

    def _assign_inside_location(self, mesh):
        inside_location = mesh.get(oclass=emmo.InsidePosition)
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
            mesh.add(inside_point)
