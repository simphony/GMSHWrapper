from osp.core.namespaces import emmo
from osp.core.session.sparql_backend import SPARQLBackend, SparqlResult, SparqlBindingSet


class GMSHSparqlBackend(SPARQLBackend):


    # OVERRIDE
    def _sparql(self, query_string):
        """Execute the given SPARQL query on the graph of the core session.
        Args:
            query_string (str): The SPARQL query as a string.
        """
        result = self.graph.query(query_string)
        return GMSHSparqlResult(result, self)


    @property
    def filling_volume_query(self):
        return f"""
        SELECT * WHERE {{
            ?comp rdf:type <{emmo.VolumeComputation.iri}> .
            ?comp <{emmo.hasInput.iri}> ?inp .
            ?inp rdf:type <{emmo.Filling.iri}> .
            ?inp <{emmo.hasQuantitativeProperty.iri}> ?quant.
            ?quant rdf:type <{emmo.FillingFraction.iri}> .
            ?quant <{emmo.hasQuantityValue.iri}> ?real .
            ?real rdf:type <{emmo.Real.iri}> .
            ?quant <{emmo.hasReferenceUnit.iri}> ?unit
        }}
        """

    @property
    def mesh_generation_query(self):
        return f"""
        SELECT * WHERE {{
            ?comp rdf:type <{emmo.MeshGeneration.iri}> .
            ?comp <{emmo.hasInput.iri}> ?inp .
            ?comp <{emmo.hasOutput.iri}> ?mesh . 
            ?inp rdf:type ?inp_type .
            ?inp_type rdfs:subClassOf* <{emmo.TwoManifold.iri}>
            {self.geometry_query} .
            {self.mesh_file_query}
        }}
        """

    @property
    def mesh_volume_query(self):
        return f"""
        SELECT * WHERE {{
            ?comp rdf:type <{emmo.VolumeComputation.iri}> .
            ?comp <{emmo.hasInput.iri}> ?inp .
            ?inp rdf:type ?inp_type .
            ?inp_type rdfs:subClassOf* <{emmo.TwoManifold.iri}> .
            {self.geometry_query} .
            {self.mesh_file_query}
        }}
        """

    @property
    def prefixes(self):
        return f"""
        @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix owl:   <http://www.w3.org/2002/07/owl#> .
        @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
        @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> . 
        """

    @property
    def geometry_query(self):
        return f"""
        optional{{
            {self.rectangle_query}
        }} .
        optional{{
            {self.cylinder_query}
        }}
        """

    @property
    def rectangle_query(self):
        return f"""
        ?inp rdf:type <{emmo.Rectangle.iri}> .
        
        ?inp <{emmo.hasXLength.iri}> ?x .
        ?x rdf:type <{emmo.Length.iri}> .
        ?x <{emmo.hasQuantityValue.iri}> ?x_value .
        ?x <{emmo.hasReferenceUnit.iri}> ?x_unit .
        ?x_value rdf:type <{emmo.Integer.iri}>  .
        ?x_unit rdf:type <{emmo.Metre.iri}>  .

        optional {{
            {self.x_conversion}
        }} .

        ?inp <{emmo.hasYLength.iri}> ?y .
        ?y rdf:type <{emmo.Length.iri}> .
        ?y <{emmo.hasQuantityValue.iri}> ?y_value .
        ?y <{emmo.hasReferenceUnit.iri}> ?y_unit .
        ?y_value rdf:type <{emmo.Integer.iri}> .
        ?y_unit rdf:type <{emmo.Metre.iri}>  .

        optional {{
            {self.y_conversion}
        }} .

        ?inp <{emmo.hasZLength.iri}> ?z .
        ?z rdf:type <{emmo.Length.iri}> .
        ?z <{emmo.hasQuantityValue.iri}> ?z_value .
        ?z <{emmo.hasReferenceUnit.iri}> ?z_unit .
        ?z_value rdf:type <{emmo.Integer.iri}> .
        ?z_unit rdf:type <{emmo.Metre.iri}>  .

        optional {{
            {self.z_conversion}
        }} .
        """

    @property
    def cylinder_query(self):
        return f"""
        ?inp rdf:type <{emmo.Cylinder.iri}> .

        ?inp <{emmo.hasXYRadius.iri}> ?xy_radius .
        ?xy_radius rdf:type <{emmo.Length.iri}> .
        ?xy_radius <{emmo.hasQuantityValue.iri}> ?xy_radius_value .
        ?xy_radius <{emmo.hasReferenceUnit.iri}> ?xy_radius_unit .
        ?xy_radius_value rdf:type <{emmo.Integer.iri}> .
        ?xy_radius_unit rdf:type <{emmo.Metre.iri}>  .

        optional {{
            {self.radius_conversion}
        }}  .

        ?inp <{emmo.hasZLength.iri}> ?z .
        ?z rdf:type <{emmo.Length.iri}> .
        ?z <{emmo.hasQuantityValue.iri}> ?z_value .
        ?z <{emmo.hasReferenceUnit.iri}> ?z_unit .
        ?z_value rdf:type <{emmo.Integer.iri}> .
        ?z_unit rdf:type <{emmo.Metre.iri}>  .

        optional {{
            {self.z_conversion}
        }} .
        """

    @property
    def radius_conversion(self):
        return f"""
        ?xy_radius_value <{emmo.hasVariable.iri}> ?xy_radius_prefix .
        ?xy_radius_prefix rdf:type ?type .
        ?type rdfs:subClassOf* <{emmo.SIMetricPrefix.iri}> .
        """

    @property
    def x_conversion(self):
        return f"""
        ?x_value <{emmo.hasVariable.iri}> ?x_prefix .
        ?x_prefix rdf:type ?type .
        ?type rdfs:subClassOf* <{emmo.SIMetricPrefix.iri}> .
        """

    @property
    def y_conversion(self):
        return f"""
        ?y_value <{emmo.hasVariable.iri}> ?y_prefix .
        ?y_prefix rdf:type ?type .
        ?type rdfs:subClassOf* <{emmo.SIMetricPrefix.iri}> .
        """

    @property
    def z_conversion(self):
        return f"""
        ?z_value <{emmo.hasVariable.iri}> ?z_prefix .
        ?z_prefix rdf:type ?type .
        ?type rdfs:subClassOf* <{emmo.SIMetricPrefix.iri}> .
        """

    def get_restriction(self, prefix_iri):
        return f"""{self.prefixes}
        SELECT * WHERE {{
            {prefix_iri} rdfs:subClassOf* ?restriction .
            ?restriction rdf:type owl:Restriction .
            ?restriction owl:onProperty ?property .
            ?property owl:inverseOf <{emmo.hasVariable.iri}> .
            ?restriction owl:allValuesFrom ?restriction2 .
            ?restriction2 rdf:type owl:Restriction .
            ?restriction2 owl:onProperty <{emmo.hasNumericalData.iri}> .
            ?restriction2 owl:hasValue ?conversion
        }}
        """

    @property
    def mesh_file_query(self):
        return f"""
        ?mesh <{emmo.standsFor.iri}> ?inp .
        ?file <{emmo.hasProperty.iri}> ?mesh .
        ?mesh rdf:type <{emmo.TriangleMesh.iri}> .
        ?file <{emmo.hasProperty.iri}> ?file_name .
        ?file <{emmo.hasProperty.iri}> ?file_format .
        ?file <{emmo.hasProperty.iri}> ?file_path .
        ?file_name rdf:type <{emmo.String.iri}> .
        ?file_path rdf:type <{emmo.UnixPath.iri}> .
        ?file_format rdf:type <{emmo.STL.iri}>   .     
        """


class GMSHSparqlResult(SparqlResult):

    def __init__(self, query_result, session):
        """Initialize the result."""
        self.result = query_result
        super().__init__(session)

    def close(self):
        """Close the connection."""
        pass

    def __iter__(self, **kwargs):
        """Iterate the result."""
        for row in self.result:
            yield GMSHSparqlBindingSet(
                row, self.session, kwargs
            )

    def __len__(self):
        """Compute the number of elements in the result."""
        return len(self.result)


class GMSHSparqlBindingSet(SparqlBindingSet):
    """A row in the result. Mapping from variable to value."""

    def __init__(self, row, session, datatypes):
        """Initialize the row."""
        self.binding_set = row
        super().__init__(session, datatypes)

    def _get(self, variable_name):
        return self.binding_set[variable_name]
