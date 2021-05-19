from osp.wrappers.cuds_translator import CudsTranslator
from osp.core.namespaces import emmo
import emmo_cfd
import os


class BaseTranslator(CudsTranslator):

    gmsh_model = emmo_cfd.get_file("gmsh_model", ".sparql")
    mesh_data = emmo_cfd.get_file("mesh_data", ".sparql")
    filling_fraction = emmo_cfd.get_file("filling_fraction", ".sparql")
    geo_data = emmo_cfd.get_file("geo_data", ".sparql")

    def __init__(self, rdf_file, directory=None, session=None):
        self.imports = super().__init__(rdf_file, session=session, fmt="ttl")
        if directory:
            self.set_directory(directory)

    def set_directory(self, directory, file_name="new_surface"):
        dir_seq = emmo.DirectorySequence()
        dir_split = os.path.split(directory)
        previous_dir = list()
        for n, folder in enumerate(dir_split):
            directory = emmo.Directory()
            directory_name = emmo.String(hasSymbolData=folder)
            directory.add(directory_name, rel=emmo.hasSign)
            if n == 0:
                relation = emmo.hasSpatialFirst
            elif n == len(dir_split):
                relation = emmo.hasSpatialLast
            else:
                relation = emmo.hasSpatialDirectPart
            if n > 0:
                previous_dir[-1].add(
                    directory,
                    rel=emmo.hasSpatialNext
                )
            previous_dir.append(directory)
            dir_seq.add(directory, rel=relation)
        stl = emmo.STL()
        name = emmo.String(hasSymbolData=file_name)
        self.geo_file = emmo.File()
        self.geo_file.add(stl, name, dir_seq, rel=emmo.hasSign)

    def set_resolution(self, values, units):
        self.edit_quantity(
            self.resolution,
            values['resolution'],
            units['resolution']
        )

    def set_filling_fraction(self, values):
        self.edit_quantity(self.filling_fraction, values['filling_fraction'])

    def edit_quantity(self, query, value, unit=None):
        quantity, real = self.get_cuds(query)[0]
        real.hasNumericalData = value
        unit_entity = self.set_unit(unit)
        if unit_entity:
            quantity.add(unit_entity, rel=emmo.hasReferenceUnit)

    def set_unit(self, unit):
        if unit == "cm":
            return emmo.Centi(hasSymbolData=unit[0])
        elif unit == "dm":
            return emmo.Deci(hasSymbolData=unit[0])
        elif unit == "mm":
            return emmo.Milli(hasSymbolData=unit[0])
        elif unit == "µm":
            return emmo.Micro(hasSymbolData=unit[0])
        elif unit == "m" or not unit:
            pass
        else:
            raise ValueError('SI-Unit of length not supported or receognized')

    def add_directory(self):
        mesh_data = self.get_cuds(self.mesh_data)[0][0]
        mesh_data.add(self.geo_file, rel=emmo.hasSign)

    def get_model(self):
        return self.get_cuds(self.gmsh_model)[0][0]


class Rectangle(BaseTranslator):

    rdf_file = emmo_cfd.get_file("rectanglemesh", ".ttl")
    x_length = emmo_cfd.get_file("xlength", ".sparql")
    y_length = emmo_cfd.get_file("ylength", ".sparql")
    z_length = emmo_cfd.get_file("zlength", ".sparql")
    resolution = emmo_cfd.get_file("resolution", ".sparql")
    values = {'x': 1, 'y': 1, 'z': 1, 'filling_fraction': 1, 'resolution': 1}
    units = {'lengths': 'm', 'resolution': 'cm'}

    def __init__(self, directory, values=values, units=units, session=None):
        super().__init__(self.rdf_file, session=session, directory=directory)
        self.set_lengths(values, units)
        self.set_resolution(values, units)
        self.set_filling_fraction(values)
        self.add_directory()

    def set_lengths(self, values, units):
        self.edit_quantity(self.x_length, values['x'], units['lengths'])
        self.edit_quantity(self.y_length, values['y'], units['lengths'])
        self.edit_quantity(self.z_length, values['z'], units['lengths'])


class Cylinder(BaseTranslator):

    rdf_file = emmo_cfd.get_file("cylindermesh", ".ttl")
    radius = emmo_cfd.get_file("radius", ".sparql")
    length = emmo_cfd.get_file("zlength", ".sparql")
    resolution = emmo_cfd.get_file("resolution", ".sparql")
    values = {'radius': 1, 'length': 1, 'filling_fraction': 1, 'resolution': 1}
    units = {'lengths': 'm', 'resolution': 'cm'}

    def __init__(self, directory, values=values, units=units, session=None):
        super().__init__(self.rdf_file, session=session, directory=directory)
        self.set_lengths(values, units)
        self.set_resolution(values, units)
        self.set_filling_fraction(values)
        self.add_directory()

    def set_lengths(self, values, units):
        self.edit_quantity(self.radius, values['radius'], units['lengths'])
        self.edit_quantity(self.length, values['length'], units['lengths'])


class Complex(BaseTranslator):

    rdf_file = emmo_cfd.get_file("complexmesh", ".ttl")
    values = {'inside_point': [1, 1, 1], 'filling_fraction': 1}
    units = {'lengths': 'm'}

    def __init__(self, input_file, values=values, units=units, session=None):
        super().__init__(self.rdf_file, session=session)
        self.set_inside_point(values, units)
        self.set_reference_unit(units['lengths'])
        self.set_filling_fraction(values)
        self.add_input_file(input_file)

    def set_reference_unit(self, unit):
        geo_data = self.get_cuds(self.geo_data)[0][0]
        unit_entity = self.set_unit(unit)
        if unit_entity:
            geo_data.add(unit_entity, rel=emmo.hasReferenceUnit)

    def add_input_file(self, input_file):
        geo_data = self.get_cuds(self.geo_data)[0][0]
        directory, file_name = os.path.split(input_file)
        name, extension = os.path.splitext(file_name)
        self.set_directory(directory, file_name=name)
        geo_data.add(self.geo_file, rel=emmo.hasSign)

    def set_inside_point(self, values, units):
        x, y, z = values['inside_point']
        # add inside point as reference
        inside_point = emmo.InsidePosition()
        length_x = emmo.Length()
        real_x = emmo.Real(hasNumericalData=x)
        unit_x = emmo.Metre(hasSymbolData='m')
        length_y = emmo.Length()
        real_y = emmo.Real(hasNumericalData=y)
        unit_y = emmo.Metre(hasSymbolData='m')
        length_z = emmo.Length()
        real_z = emmo.Real(hasNumericalData=z)
        unit_z = emmo.Metre(hasSymbolData='m')

        length_x.add(real_x, rel=emmo.hasQuantityValue)
        length_x.add(unit_x, rel=emmo.hasReferenceUnit)
        length_y.add(real_y, rel=emmo.hasQuantityValue)
        length_y.add(unit_y, rel=emmo.hasReferenceUnit)
        length_z.add(real_z, rel=emmo.hasQuantityValue)
        length_z.add(unit_z, rel=emmo.hasReferenceUnit)
        length_x.add(length_y, rel=emmo.hasSpatialNext)
        length_y.add(length_z, rel=emmo.hasSpatialNext)
        inside_point.add(length_x, rel=emmo.hasSpatialFirst)
        inside_point.add(length_y, rel=emmo.hasSpatialDirectPart)
        inside_point.add(length_z, rel=emmo.hasSpatialLast)

        mesh_data = self.get_cuds(self.mesh_data)[0][0]
        mesh_data.add(inside_point, rel=emmo.hasPart)
