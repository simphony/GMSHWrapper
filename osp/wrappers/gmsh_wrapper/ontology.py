import os


PATH = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "emmo_cfd"
)


class Ontology:

    @classmethod
    def get_ttl(cls, name):
        return cls.get_file(name, extension=".ttl")

    @classmethod
    def get_owl(cls, name):
        return cls.get_file(name, extension=".owl")

    @classmethod
    def get_yml(cls, name):
        return cls.get_file(name, extension=".yml")

    @classmethod
    def get_file(cls, name, extension):
        return cls.parse_dir(PATH, extension)[name]

    @classmethod
    def parse_dir(cls, path, extension, libary=dict()):
        for element in os.listdir(path):
            element_path = os.path.join(path, element)
            name, ext = os.path.splitext(element)
            if os.path.isfile(element_path):
                if ext == extension:
                    libary[name] = element_path
            else:
                libary = cls.parse_dir(element_path, extension, libary=libary)
        return libary
