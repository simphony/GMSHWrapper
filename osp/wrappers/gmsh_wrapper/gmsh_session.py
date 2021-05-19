import os
from decimal import Decimal
import numpy as np
from osp.core.session import WrapperSession
from osp.core.namespaces import emmo
from osp.wrappers.gmsh_wrapper.gmsh_engine import (
    RectangularMesh, CylinderMesh, ComplexMesh, CONVERSIONS, extent
)


MAPPING = extent(
    min_extent=[
        emmo.hasMinimumXCoordinate,
        emmo.hasMinimumYCoordinate,
        emmo.hasMinimumZCoordinate
    ],
    max_extent=[
        emmo.hasMaximumXCoordinate,
        emmo.hasMaximumYCoordinate,
        emmo.hasMaximumZCoordinate
    ]
)


class GMSHSession(WrapperSession):

    """
    Session class for GMSH.
    """

    def __init__(self, **kwargs):
        super().__init__(engine=None, **kwargs)
        self._geometry = None
        self._target_path = None

    def __str__(self):
        return "OSP-wrapper for GMSH"

    def run(self):
        """Run the computation"""
        # get CUDS-root object
        root = self._registry.get(self.root)
        # get entity for GMSH computation
        computation = root.get(oclass=emmo.MeshGeneration)
        # check if mesh generation exits
        if computation:
            # get geometry data
            geo_data = computation[0].get(oclass=emmo.GeometryData)
            # get mesh data
            mesh_data = computation[0].get(oclass=emmo.MeshData)
            # get filling data
            fill_data = computation[0].get(oclass=emmo.FillingData)
            # check if geometry and mesh data exist
            if geo_data and mesh_data and fill_data:
                # run the GMSH Mold model
                self._parse_mold_data(geo_data[0], mesh_data[0], fill_data[0])
                if self._target_path:
                    self._geometry.write_mesh(self._target_path)
                else:
                    self._geometry.inspect_file()
                self._parse_extent(self._geometry.max_extent, mesh_data[0])
                self._parse_extent(self._geometry.filling_extent, fill_data[0])
                self._assign_inside_location(mesh_data[0])
                self._assign_volume(geo_data[0])
            elif not geo_data:
                raise ValueError('geometry data not found')
            elif not mesh_data:
                raise ValueError('GMSH meta data not found')
            elif not fill_data:
                raise ValueError('Filling meta data not found')
        else:
            raise ValueError('Currently, only mold models are supported')

    def _parse_mold_data(self, geo_data, mesh_data, fill_data):
        mesh_data = self._parse_mesh_data(mesh_data)
        fill_data = self._parse_fill_data(fill_data)
        geo = geo_data.get(oclass=emmo.TwoManifold)
        if geo:
            geo_file = geo_data.get(oclass=emmo.File)
            if geo[0].is_a(emmo.Rectangle) and not geo_file:
                geo_data = self._parse_rectangle_data(geo_data)
                self._geometry = RectangularMesh(
                    **geo_data, **mesh_data, **fill_data
                )
            elif geo[0].is_a(emmo.Cylinder) and not geo_file:
                geo_data = self._parse_cylinder_data(geo_data)
                self._geometry = CylinderMesh(
                    **geo_data, **mesh_data, **fill_data
                )
            elif geo[0].is_a(emmo.Complex) or geo_file:
                geo_data = {
                    'source_path': self._parse_geometry_file(geo_file[0]),
                    'units': self._get_si_unit(geo_data)
                }
                self._geometry = ComplexMesh(
                    **mesh_data, **geo_data, **fill_data
                )
        else:
            raise ValueError(
                'Target geometry not recognized or geometry file not found'
            )

    def _parse_extent(self, extent, entity):
        for axis in extent.keys():
            for direction in extent[axis].keys():
                length = emmo.Length()
                real = emmo.Real(
                    hasNumericalData=extent[axis][direction]
                )
                unit = emmo.Metre(hasSymbolData='m')
                length.add(real, rel=emmo.hasQuantityValue)
                length.add(unit, rel=emmo.hasReferenceUnit)
                entity.add(
                    length,
                    rel=MAPPING[axis][direction]
                )

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

    def _parse_mesh_data(self, mesh_data):
        mesh_dict = dict()
        resolution = mesh_data.get(oclass=emmo.Resolution)
        inside_point = mesh_data.get(oclass=emmo.InsidePosition)
        geo_file = mesh_data.get(oclass=emmo.File)
        if resolution:
            mesh_dict['resolution'] = self._to_meters(resolution[0])
        if inside_point:
            mesh_dict['inside_location'] = self._get_vector_data(
                inside_point[0]
            )
        if geo_file:
            self._target_path = self._parse_geometry_file(
                geo_file[0], only_dir=True
            )
        return mesh_dict

    def _parse_fill_data(self, fill_data):
        filling_fraction = fill_data.get(oclass=emmo.FillingFraction)
        if filling_fraction:
            filling_fraction = self._get_real_value(
                filling_fraction[0]
            )
        else:
            raise ValueError('Filling fraction not found')
        return {
            'filling_fraction': float(filling_fraction)
        }

    def _parse_rectangle_data(self, geometry_data):
        x_length = y_length = z_length = 1
        x_length_data = geometry_data.get(rel=emmo.hasXLength)
        y_length_data = geometry_data.get(rel=emmo.hasYLength)
        z_length_data = geometry_data.get(rel=emmo.hasZLength)
        if x_length_data:
            x_length = self._to_meters(x_length_data[0])
        if y_length_data:
            y_length = self._to_meters(y_length_data[0])
        if z_length_data:
            z_length = self._to_meters(z_length_data[0])
        return {
            'x_length': x_length,
            'y_length': y_length,
            'z_length': z_length,
            'units': 'm'
        }

    def _parse_cylinder_data(self, geometry_data):
        z_length = xy_radius = 1
        xy_radius_data = geometry_data.get(rel=emmo.hasXYRadius)
        z_length_data = geometry_data.get(rel=emmo.hasZLength)
        if xy_radius_data:
            xy_radius = self._to_meters(xy_radius_data[0])
        if z_length_data:
            z_length = self._to_meters(z_length_data[0])
        return {
            'z_length': z_length,
            'xy_radius': xy_radius,
            'units': 'm'
        }

    def _parse_geometry_file(self, geometry_file, only_dir=None):
        dir_seq = geometry_file.get(oclass=emmo.DirectorySequence)
        if dir_seq:
            directory = self._parse_directory_sequence(dir_seq[0])
        else:
            raise ValueError('File directory sequence not defined')
        if not only_dir:
            name_data = geometry_file.get(oclass=emmo.String)
            format_data = geometry_file.get(oclass=emmo.GeometryFileFormat)
            if name_data:
                name = name_data[0].hasSymbolData
            else:
                raise ValueError('File name not found')
            if format_data:
                if not format_data[0].is_a(emmo.STL):
                    raise ValueError('Only STL-files supported for the moment')
                file_format = 'stl'
            else:
                raise ValueError(
                    'File format not defined'
                )
            file_name = ".".join([name, file_format])
            return os.path.join(directory, file_name)
        else:
            return directory

    def _parse_directory_sequence(self, directory_seq):
        directory_data = directory_seq.get(oclass=emmo.Directory)
        if directory_data:
            folder = directory_seq.get(rel=emmo.hasSpatialFirst)
            if folder:
                directory = list()
                while True:
                    folder_name = folder[0].get(oclass=emmo.String)
                    if folder_name:
                        directory.append(
                            folder_name[0].hasSymbolData
                        )
                    else:
                        raise ValueError('Directory has no name')
                    if len(directory) == len(directory_data):
                        return os.path.join(*directory)
                    else:
                        folder = folder[0].get(rel=emmo.hasSpatialNext)
                        if not folder:
                            raise ValueError(
                                'Next element in sequence not found'
                            )
            else:
                raise ValueError(
                    'First element of array not found'
                )
        else:
            raise ValueError(
                'Array has no elements of type `emmo.Directory`'
            )

    def _to_meters(self, quantity):
        return float(
            np.product(
                (
                    Decimal(
                        self._get_real_value(quantity)
                    ),
                    Decimal(
                        self._get_conversion(quantity)
                    )
                )
            )
        )

    def _get_vector_data(self, position_vector):
        vector_data = position_vector.get(oclass=emmo.Length)
        if vector_data:
            element = position_vector.get(rel=emmo.hasSpatialFirst)
            if element:
                vector = list()
                while True:
                    vector.append(self._to_meters(element[0]))
                    if len(vector) == len(vector_data):
                        return vector
                    else:
                        element = element[0].get(
                            rel=emmo.hasSpatialNext
                        )
                        if not element:
                            raise ValueError(
                                'Next element in array not found'
                            )
            else:
                raise ValueError(
                    'First element of array not found'
                )
        else:
            raise ValueError(
                'Array has no elements of type `emmo.Length`'
            )

    def _get_conversion(self, quantity):
        return str(
            CONVERSIONS[
                self._get_si_unit(quantity)
            ]
        )

    def _get_real_value(self, physical_property):
        real = physical_property.get(oclass=emmo.Real)
        if real:
            return real[0].hasNumericalData
        else:
            raise ValueError(
                f'Real value not found in {physical_property.oclass}'
            )

    def _get_si_unit(self, entity):
        prefix = entity.get(oclass=emmo.SIMetricPrefix)
        unit_entity = entity.get(oclass=emmo.SIUnit)
        if prefix:
            if prefix[0].is_a(emmo.Milli):
                unit = 'm'
            elif prefix[0].is_a(emmo.Centi):
                unit = 'c'
            else:
                raise ValueError(
                    'Only Milli- and Centi-prefix currently supported'
                )
        else:
            unit = str()
        if unit_entity:
            if unit_entity[0].is_a(emmo.Metre) \
                    or unit_entity[0].is_a(
                        emmo.MeterPerUnitOne
                    ):
                unit += 'm'
            elif unit_entity[0].is_a(emmo.SquareMetre):
                unit += 'm^2'
            elif unit_entity[0].is_a(emmo.CubicMetre):
                unit += 'm^3'
            else:
                raise ValueError(
                    'SI-Unit of length must be metric'
                )
        else:
            raise ValueError(
                'Length has no SI-Unit'
            )
        return unit

    def _syntactic_extent(self, entity):
        extent_data = extent()
        for axis in MAPPING.keys():
            for direction in MAPPING[axis].keys():
                extent_data[axis][direction] = self._to_meters(
                    entity.get(rel=MAPPING[axis][direction])[0]
                )
        return extent_data

    # OVERRIDE
    def close(self):
        pass

    # OVERRIDE
    def _store(self, cuds_object):
        super()._store(cuds_object)

    # OVERRIDE
    def _load_from_backend(self, uids, expired):
        for uid in uids:
            try:
                yield self._registry.get(uid)
            except KeyError:
                yield None
