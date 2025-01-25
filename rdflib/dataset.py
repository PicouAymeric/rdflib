"""
Dataset
-------

The RDF 1.1 Dataset, a small extension to the Conjunctive Graph. The
primary term is "graphs in the datasets" and not "contexts with quads"
so there is a separate method to set/retrieve a graph in a dataset and
to operate with dataset graphs. As a consequence of this approach,
dataset graphs cannot be identified with blank nodes, a name is always
required (RDFLib will automatically add a name if one is not provided
at creation time). This implementation includes a convenience method
to directly add a single quad to a dataset graph.

see :class:`~rdflib.dataset.Dataset`



Working with graphs
===================

Instantiating Graphs with default store (Memory) and default identifier
(a BNode):

    >>> g = Graph()
    >>> g.store.__class__
    <class 'rdflib.plugins.stores.memory.Memory'>
    >>> g.identifier.__class__
    <class 'rdflib.term.BNode'>

Instantiating Graphs with a Memory store and an identifier -
<https://rdflib.github.io>:

    >>> g = Graph('Memory', URIRef("https://rdflib.github.io"))
    >>> g.identifier
    rdflib.term.URIRef('https://rdflib.github.io')
    >>> str(g)  # doctest: +NORMALIZE_WHITESPACE
    "<https://rdflib.github.io> a rdfg:Graph;rdflib:storage
     [a rdflib:Store;rdfs:label 'Memory']."

Adding / removing reified triples to Graph and iterating over it directly or
via triple pattern:

    >>> g = Graph()
    >>> statementId = BNode()
    >>> print(len(g))
    0
    >>> g.add((statementId, RDF.type, RDF.Statement)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g.add((statementId, RDF.subject,
    ...     URIRef("https://rdflib.github.io/store/Dataset"))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g.add((statementId, RDF.predicate, namespace.RDFS.label)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g.add((statementId, RDF.object, Literal("Conjunctive Graph"))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> print(len(g))
    4
    >>> for s, p, o in g:
    ...     print(type(s))
    ...
    <class 'rdflib.term.BNode'>
    <class 'rdflib.term.BNode'>
    <class 'rdflib.term.BNode'>
    <class 'rdflib.term.BNode'>

    >>> for s, p, o in g.triples((None, RDF.object, None)):
    ...     print(o)
    ...
    Conjunctive Graph
    >>> g.remove((statementId, RDF.type, RDF.Statement)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> print(len(g))
    3

``None`` terms in calls to :meth:`~rdflib.graph.Graph.triples` can be
thought of as "open variables".

Graph support set-theoretic operators, you can add/subtract graphs, as
well as intersection (with multiplication operator g1*g2) and xor (g1
^ g2).

Note that BNode IDs are kept when doing set-theoretic operations, this
may or may not be what you want. Two named graphs within the same
application probably want share BNode IDs, two graphs with data from
different sources probably not.  If your BNode IDs are all generated
by RDFLib they are UUIDs and unique.

    >>> g1 = Graph()
    >>> g2 = Graph()
    >>> u = URIRef("http://example.com/foo")
    >>> g1.add([u, namespace.RDFS.label, Literal("foo")]) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g1.add([u, namespace.RDFS.label, Literal("bar")]) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g2.add([u, namespace.RDFS.label, Literal("foo")]) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g2.add([u, namespace.RDFS.label, Literal("bing")]) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> len(g1 + g2)  # adds bing as label
    3
    >>> len(g1 - g2)  # removes foo
    1
    >>> len(g1 * g2)  # only foo
    1
    >>> g1 += g2  # now g1 contains everything


Graph Aggregation - Datasets and ReadOnlyGraphAggregate within
the same store:

    >>> store = plugin.get("Memory", Store)()
    >>> g1 = Graph(store)
    >>> g2 = Graph(store)
    >>> g3 = Graph(store)
    >>> stmt1 = BNode()
    >>> stmt2 = BNode()
    >>> stmt3 = BNode()
    >>> g1.add((stmt1, RDF.type, RDF.Statement)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g1.add((stmt1, RDF.subject,
    ...     URIRef('https://rdflib.github.io/store/Dataset'))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g1.add((stmt1, RDF.predicate, namespace.RDFS.label)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g1.add((stmt1, RDF.object, Literal('Conjunctive Graph'))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g2.add((stmt2, RDF.type, RDF.Statement)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g2.add((stmt2, RDF.subject,
    ...     URIRef('https://rdflib.github.io/store/Dataset'))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g2.add((stmt2, RDF.predicate, RDF.type)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g2.add((stmt2, RDF.object, namespace.RDFS.Class)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g3.add((stmt3, RDF.type, RDF.Statement)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g3.add((stmt3, RDF.subject,
    ...     URIRef('https://rdflib.github.io/store/Dataset'))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g3.add((stmt3, RDF.predicate, namespace.RDFS.comment)) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> g3.add((stmt3, RDF.object, Literal(
    ...     'The top-level aggregate graph - The sum ' +
    ...     'of all named graphs within a Store'))) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> len(list(Dataset(store).subjects(RDF.type, RDF.Statement)))
    3
    >>> len(list(ReadOnlyGraphAggregate([g1,g2]).subjects(
    ...     RDF.type, RDF.Statement)))
    2

Datasets have a :meth:`~rdflib.dataset.Dataset.quads` method
which returns quads instead of triples, where the fourth item is the Graph
(or subclass thereof) instance in which the triple was asserted:

    >>> uniqueGraphNames = set(
    ...     [graph.identifier for s, p, o, graph in Dataset(store
    ...     ).quads((None, RDF.predicate, None))])
    >>> len(uniqueGraphNames)
    3
    >>> unionGraph = ReadOnlyGraphAggregate([g1, g2])
    >>> uniqueGraphNames = set(
    ...     [graph.identifier for s, p, o, graph in unionGraph.quads(
    ...     (None, RDF.predicate, None))])
    >>> len(uniqueGraphNames)
    2

Parsing N3 from a string

    >>> g2 = Graph()
    >>> src = '''
    ... @prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    ... @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    ... [ a rdf:Statement ;
    ...   rdf:subject <https://rdflib.github.io/store#Dataset>;
    ...   rdf:predicate rdfs:label;
    ...   rdf:object "Conjunctive Graph" ] .
    ... '''
    >>> g2 = g2.parse(data=src, format="n3")
    >>> print(len(g2))
    4

Using Namespace class:

    >>> RDFLib = Namespace("https://rdflib.github.io/")
    >>> RDFLib.Dataset
    rdflib.term.URIRef('https://rdflib.github.io/Dataset')
    >>> RDFLib["Graph"]
    rdflib.term.URIRef('https://rdflib.github.io/Graph')
"""
import pathlib
from typing import IO, Any, BinaryIO, Generator, Iterable, TextIO, TypeVar, overload
from rdflib.paths import Path
from rdflib.term import BNode, URIRef, Literal
from rdflib.graph import _ObjectType, _OptionalQuadType, _PredicateType, _QuadPatternType, _QuadSelectorType, _QuadType, _SubjectType, _TripleOrOptionalQuadType, _TripleOrQuadPathPatternType, _TripleOrQuadSelectorType, _TripleOrTriplePathType, _TriplePathType, Graph, _ContextIdentifierType, _OptionalIdentifiedQuadType, _TripleOrQuadPatternType, _TripleType, _assertnode
from rdflib.parser import InputSource, create_input_source
from rdflib.store import Store

DATASET_DEFAULT_GRAPH_ID = URIRef("urn:x-rdflib:default")
_DatasetT = TypeVar("_DatasetT", bound="Dataset")


__all__ = [
    "Dataset",
    "_DatasetT"
]
class Dataset(Graph):
    """
    An RDFLib Dataset is an object that stores multiple Named Graphs - instances of
    RDFLib Graph identified by IRI - within it and allows whole-of-dataset or single
    Graph use.

    RDFLib's Dataset class is based on the `RDF 1.2. 'Dataset' definition
    <https://www.w3.org/TR/rdf12-datasets/>`_:

    ..

        An RDF dataset is a collection of RDF graphs, and comprises:

        - Exactly one default graph, being an RDF graph. The default graph does not
            have a name and MAY be empty.
        - Zero or more named graphs. Each named graph is a pair consisting of an IRI or
            a blank node (the graph name), and an RDF graph. Graph names are unique
            within an RDF dataset.

    Accordingly, a Dataset allows for `Graph` objects to be added to it with
    :class:`rdflib.term.URIRef` or :class:`rdflib.term.BNode` identifiers and always
    creats a default graph with the :class:`rdflib.term.URIRef` identifier
    :code:`urn:x-rdflib:default`.

    Dataset extends Graph's Subject, Predicate, Object (s, p, o) 'triple'
    structure to include a graph identifier - archaically called Context - producing
    'quads' of s, p, o, g.

    Triples, or quads, can be added to a Dataset. Triples, or quads with the graph
    identifer :code:`urn:x-rdflib:default` go into the default graph.

    Examples of usage and see also the examples/datast.py file:

    >>> # Create a new Dataset
    >>> ds = Dataset()
    >>> # simple triples goes to default graph
    >>> ds.add((
    ...     URIRef("http://example.org/a"),
    ...     URIRef("http://www.example.org/b"),
    ...     Literal("foo")
    ... ))  # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.dataset.Dataset'>)>
    >>>
    >>> # Create a graph in the dataset, if the graph name has already been
    >>> # used, the corresponding graph will be returned
    >>> # (ie, the Dataset keeps track of the constituent graphs)
    >>> g = ds.graph(URIRef("http://www.example.com/gr"))
    >>>
    >>> # add triples to the new graph as usual
    >>> g.add((
    ...     URIRef("http://example.org/x"),
    ...     URIRef("http://example.org/y"),
    ...     Literal("bar")
    ... )) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.graph.Graph'>)>
    >>> # alternatively: add a quad to the dataset -> goes to the graph
    >>> ds.add((
    ...     URIRef("http://example.org/x"),
    ...     URIRef("http://example.org/z"),
    ...     Literal("foo-bar"),
    ...     g
    ... )) # doctest: +ELLIPSIS
    <Graph identifier=... (<class 'rdflib.dataset.Dataset'>)>
    >>>
    >>> # querying triples return them all regardless of the graph
    >>> for t in ds.triples((None,None,None)):  # doctest: +SKIP
    ...     print(t)  # doctest: +NORMALIZE_WHITESPACE
    (rdflib.term.URIRef("http://example.org/a"),
     rdflib.term.URIRef("http://www.example.org/b"),
     rdflib.term.Literal("foo"))
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/z"),
     rdflib.term.Literal("foo-bar"))
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/y"),
     rdflib.term.Literal("bar"))
    >>>
    >>> # querying quads() return quads; the fourth argument can be unrestricted
    >>> # (None) or restricted to a graph
    >>> for q in ds.quads((None, None, None, None)):  # doctest: +SKIP
    ...     print(q)  # doctest: +NORMALIZE_WHITESPACE
    (rdflib.term.URIRef("http://example.org/a"),
     rdflib.term.URIRef("http://www.example.org/b"),
     rdflib.term.Literal("foo"),
     None)
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/y"),
     rdflib.term.Literal("bar"),
     rdflib.term.URIRef("http://www.example.com/gr"))
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/z"),
     rdflib.term.Literal("foo-bar"),
     rdflib.term.URIRef("http://www.example.com/gr"))
    >>>
    >>> # unrestricted looping is equivalent to iterating over the entire Dataset
    >>> for q in ds:  # doctest: +SKIP
    ...     print(q)  # doctest: +NORMALIZE_WHITESPACE
    (rdflib.term.URIRef("http://example.org/a"),
     rdflib.term.URIRef("http://www.example.org/b"),
     rdflib.term.Literal("foo"),
     None)
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/y"),
     rdflib.term.Literal("bar"),
     rdflib.term.URIRef("http://www.example.com/gr"))
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/z"),
     rdflib.term.Literal("foo-bar"),
     rdflib.term.URIRef("http://www.example.com/gr"))
    >>>
    >>> # resticting iteration to a graph:
    >>> for q in ds.quads((None, None, None, g)):  # doctest: +SKIP
    ...     print(q)  # doctest: +NORMALIZE_WHITESPACE
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/y"),
     rdflib.term.Literal("bar"),
     rdflib.term.URIRef("http://www.example.com/gr"))
    (rdflib.term.URIRef("http://example.org/x"),
     rdflib.term.URIRef("http://example.org/z"),
     rdflib.term.Literal("foo-bar"),
     rdflib.term.URIRef("http://www.example.com/gr"))
    >>> # Note that in the call above -
    >>> # ds.quads((None,None,None,"http://www.example.com/gr"))
    >>> # would have been accepted, too
    >>>
    >>> # graph names in the dataset can be queried:
    >>> for c in ds.graphs():  # doctest: +SKIP
    ...     print(c.identifier)  # doctest:
    urn:x-rdflib:default
    http://www.example.com/gr
    >>> # A graph can be created without specifying a name; a skolemized genid
    >>> # is created on the fly
    >>> h = ds.graph()
    >>> for c in ds.graphs():  # doctest: +SKIP
    ...     print(c)  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    DEFAULT
    https://rdflib.github.io/.well-known/genid/rdflib/N...
    http://www.example.com/gr
    >>> # Note that the Dataset.graphs() call returns names of empty graphs,
    >>> # too. This can be restricted:
    >>> for c in ds.graphs(empty=False):  # doctest: +SKIP
    ...     print(c)  # doctest: +NORMALIZE_WHITESPACE
    DEFAULT
    http://www.example.com/gr
    >>>
    >>> # a graph can also be removed from a dataset via ds.remove_graph(g)

    ... versionadded:: 4.0
    """
    default_context: Graph

    def __init__(
        self,
        store: Store | str = "default",
        default_union: bool = False,
        default_graph_base: str | None = None,
    ):
        super(Dataset, self).__init__(store=store, identifier=None)

        self.context_aware = True

        if not self.store.graph_aware:
            raise Exception("Dataset must be backed by a graph-aware store!")
        self.default_context = Graph(
            store=self.store,
            identifier=DATASET_DEFAULT_GRAPH_ID,
            base=default_graph_base,
        )

        self.default_union = default_union

    def __getnewargs__(self) -> tuple[Any, ...]:
        return (self.store, self.default_union, self.default_context.base)

    def __str__(self) -> str:
        pattern = (
            "[a rdflib:Dataset;rdflib:storage " "[a rdflib:Store;rdfs:label '%s']]"
        )
        return pattern % self.store.__class__.__name__

    @overload
    def _spoc(
        self,
        triple_or_quad: _QuadType,
        default: bool = False,
    ) -> _QuadType: ...

    @overload
    def _spoc(
        self,
        triple_or_quad: _TripleType | _OptionalQuadType,
        default: bool = False,
    ) -> _OptionalQuadType: ...

    @overload
    def _spoc(
        self,
        triple_or_quad: None,
        default: bool = False,
    ) -> tuple[None, None, None, Graph | None]: ...

    @overload
    def _spoc(
        self,
        triple_or_quad: _TripleOrQuadPatternType | None,
        default: bool = False,
    ) -> _QuadPatternType: ...

    @overload
    def _spoc(
        self,
        triple_or_quad: _TripleOrQuadSelectorType,
        default: bool = False,
    ) -> _QuadSelectorType: ...

    @overload
    def _spoc(
        self,
        triple_or_quad: _TripleOrQuadSelectorType | None,
        default: bool = False,
    ) -> _QuadSelectorType: ...

    def _spoc(
        self,
        triple_or_quad: _TripleOrQuadSelectorType | None,
        default: bool = False,
    ) -> _QuadSelectorType:
        """
        helper method for having methods that support
        either triples or quads
        """
        if triple_or_quad is None:
            return (None, None, None, self.default_context if default else None)
        if len(triple_or_quad) == 3:
            c = self.default_context if default else None
            # type error: Too many values to unpack (3 expected, 4 provided)
            (s, p, o) = triple_or_quad  # type: ignore[misc, unused-ignore]
        elif len(triple_or_quad) == 4:
            # type error: Need more than 3 values to unpack (4 expected)
            (s, p, o, c) = triple_or_quad  # type: ignore[misc, unused-ignore]
            c = self._graph(c)
        return s, p, o, c
    
    def __contains__(self, triple_or_quad: _TripleOrQuadSelectorType) -> bool:
        """Support for 'triple/quad in graph' syntax"""
        s, p, o, c = self._spoc(triple_or_quad)
        for t in self.triples((s, p, o), context=c):
            return True
        return False
    
    def add(
        self: _DatasetT,
        triple_or_quad: _TripleOrOptionalQuadType,
    ) -> _DatasetT:
        """
        Add a triple or quad to the store.

        if a triple is given it is added to the default context
        """

        s, p, o, c = self._spoc(triple_or_quad, default=True)

        _assertnode(s, p, o)

        # type error: Argument "context" to "add" of "Store" has incompatible type "Optional[Graph]"; expected "Graph"
        self.store.add((s, p, o), context=c, quoted=False)  # type: ignore[arg-type]
        return self

    @overload
    def _graph(self, c: Graph | _ContextIdentifierType | str) -> Graph: ...

    @overload
    def _graph(self, c: None) -> None: ...

    def _graph(self, c: Graph | _ContextIdentifierType | str | None) -> Graph | None:
        if c is None:
            return None
        if not isinstance(c, Graph):
            return self.get_context(c)
        else:
            return c

    def addN(  # noqa: N802
        self: _DatasetT, quads: Iterable[_QuadType]
    ) -> _DatasetT:
        """Add a sequence of triples with context"""

        self.store.addN(
            (s, p, o, self._graph(c)) for s, p, o, c in quads if _assertnode(s, p, o)
        )
        return self

    # type error: Argument 1 of "remove" is incompatible with supertype "Graph"; supertype defines the argument type as "tuple[Optional[Node], Optional[Node], Optional[Node]]"
    def remove(self: _DatasetT, triple_or_quad: _TripleOrOptionalQuadType) -> _DatasetT:  # type: ignore[override]
        """
        Removes a triple or quads

        if a triple is given it is removed from all contexts

        a quad is removed from the given context only

        """
        s, p, o, c = self._spoc(triple_or_quad)

        self.store.remove((s, p, o), context=c)
        return self


    @overload
    def triples(
        self,
        triple_or_quad: _TripleOrQuadPatternType,
        context: Graph | None = ...,
    ) -> Generator[_TripleType, None, None]: ...

    @overload
    def triples(
        self,
        triple_or_quad: _TripleOrQuadPathPatternType,
        context: Graph | None = ...,
    ) -> Generator[_TriplePathType, None, None]: ...

    @overload
    def triples(
        self,
        triple_or_quad: _TripleOrQuadSelectorType,
        context: Graph | None = ...,
    ) -> Generator[_TripleOrTriplePathType, None, None]: ...

    def triples(
        self,
        triple_or_quad: _TripleOrQuadSelectorType,
        context: Graph | None = None,
    ) -> Generator[_TripleOrTriplePathType, None, None]:
        """
        Iterate over all the triples in the entire conjunctive graph

        For legacy reasons, this can take the context to query either
        as a fourth element of the quad, or as the explicit context
        keyword parameter. The kw param takes precedence.
        """

        s, p, o, c = self._spoc(triple_or_quad)
        context = self._graph(context or c)

        if self.default_union:
            if context == self.default_context:
                context = None
        else:
            if context is None:
                context = self.default_context

        if isinstance(p, Path):
            if context is None:
                context = self

            for s, o in p.eval(context, s, o):
                yield s, p, o
        else:
            for (s, p, o), cg in self.store.triples((s, p, o), context=context):
                yield s, p, o

    # Old quads method from Dataset
    def _quads(
        self, triple_or_quad: _TripleOrQuadPatternType | None = None
    ) -> Generator[_OptionalQuadType, None, None]:
        """Iterate over all the quads in the entire conjunctive graph"""

        s, p, o, c = self._spoc(triple_or_quad)

        for (s, p, o), cg in self.store.triples((s, p, o), context=c):
            for ctx in cg:
                yield s, p, o, ctx


    def triples_choices(
        self,
        triple: (
            tuple[
                list[_SubjectType] | tuple[_SubjectType, ...],
                _PredicateType,
                _ObjectType | None,
            ]
            | tuple[
                _SubjectType | None,
                list[_PredicateType] | tuple[_PredicateType, ...],
                _ObjectType | None,
            ]
            | tuple[
                _SubjectType | None,
                _PredicateType,
                list[_ObjectType] | tuple[_ObjectType, ...],
            ]
        ),
        context: Graph | None = None,
    ) -> Generator[_TripleType, None, None]:
        """Iterate over all the triples in the entire conjunctive graph"""
        s, p, o = triple
        if context is None:
            if not self.default_union:
                context = self.default_context
        else:
            context = self._graph(context)
        # type error: Argument 1 to "triples_choices" of "Store" has incompatible type "tuple[Union[list[Node], Node], Union[Node, list[Node]], Union[Node, list[Node]]]"; expected "Union[tuple[list[Node], Node, Node], tuple[Node, list[Node], Node], tuple[Node, Node, list[Node]]]"
        # type error note: unpacking discards type info
        for (s1, p1, o1), cg in self.store.triples_choices((s, p, o), context=context):  # type: ignore[arg-type]
            yield s1, p1, o1

    def __len__(self) -> int:
        """Number of triples in the entire conjunctive graph"""
        return self.store.__len__()

    # Old contexts method from Dataset
    def _contexts(
        self, triple: _TripleType | None = None
    ) -> Generator[Graph, None, None]:
        """Iterate over all contexts in the graph

        If triple is specified, iterate over all contexts the triple is in.
        """
        for context in self.store.contexts(triple):
            if isinstance(context, Graph):
                # TODO: One of these should never happen and probably
                # should raise an exception rather than smoothing over
                # the weirdness - see #225
                yield context
            else:
                # type error: Statement is unreachable
                yield self.get_context(context)  # type: ignore[unreachable]

    def get_graph(self, identifier: _ContextIdentifierType) -> Graph | None:
        """Returns the graph identified by given identifier"""
        return [x for x in self.contexts() if x.identifier == identifier][0]

    def get_context(
        self,
        identifier: _ContextIdentifierType | str | None,
        quoted: bool = False,
        base: str | None = None,
    ) -> Graph:
        """Return a context graph for the given identifier

        identifier must be a URIRef or BNode.
        """
        return Graph(
            store=self.store,
            identifier=identifier,
            namespace_manager=self.namespace_manager,
            base=base,
        )

    def remove_context(self, context: Graph) -> None:
        """Removes the given context from the graph"""
        self.store.remove((None, None, None), context)

    def context_id(self, uri: str, context_id: str | None = None) -> URIRef:
        """URI#context"""
        uri = uri.split("#", 1)[0]
        if context_id is None:
            context_id = "#context"
        return URIRef(context_id, base=uri)


    # type error: Return type "tuple[Type[Dataset], tuple[Store, bool]]" of "__reduce__" incompatible with return type "tuple[Type[Graph], tuple[Store, IdentifiedNode]]" in supertype "Dataset"
    # type error: Return type "tuple[Type[Dataset], tuple[Store, bool]]" of "__reduce__" incompatible with return type "tuple[Type[Graph], tuple[Store, IdentifiedNode]]" in supertype "Graph"
    def __reduce__(self) -> tuple[type["Dataset"], tuple[Store, bool]]:
        return type(self), (self.store, self.default_union)

    def __getstate__(self) -> tuple[Store, _ContextIdentifierType, Graph, bool]:
        return self.store, self.identifier, self.default_context, self.default_union

    def __setstate__(
        self, state: tuple[Store, _ContextIdentifierType, Graph, bool]
    ) -> None:
        # type error: Property "store" defined in "Graph" is read-only
        # type error: Property "identifier" defined in "Graph" is read-only
        self.store, self.identifier, self.default_context, self.default_union = state  # type: ignore[misc]

    def graph(
        self,
        identifier: _ContextIdentifierType | Graph | str | None = None,
        base: str | None = None,
    ) -> Graph:
        if identifier is None:
            from rdflib.term import _SKOLEM_DEFAULT_AUTHORITY, rdflib_skolem_genid

            self.bind(
                "genid",
                _SKOLEM_DEFAULT_AUTHORITY + rdflib_skolem_genid,
                override=False,
            )
            identifier = BNode().skolemize()

        g = self._graph(identifier)
        g.base = base

        self.store.add_graph(g)
        return g

    def parse(
        self,
        source: (
            IO[bytes] | TextIO | InputSource | str | bytes | pathlib.PurePath | None
        ) = None,
        publicID: str | None = None,  # noqa: N803
        format: str | None = None,
        location: str | None = None,
        file: BinaryIO | TextIO | None = None,
        data: str | bytes | None = None,
        **args: Any,
    ) -> Graph:
        """
        Parse an RDF source adding the resulting triples to the Graph.

        See :meth:`rdflib.graph.Graph.parse` for documentation on arguments.

        The source is specified using one of source, location, file or data.

        If the source is in a format that does not support named graphs its triples
        will be added to the default graph
        (i.e. :attr:`.Dataset.default_context`).

        .. caution::

           This method can access directly or indirectly requested network or
           file resources, for example, when parsing JSON-LD documents with
           ``@context`` directives that point to a network location.

           When processing untrusted or potentially malicious documents,
           measures should be taken to restrict network and file access.

           For information on available security measures, see the RDFLib
           :doc:`Security Considerations </security_considerations>`
           documentation.

        *Changed in 7.0*: The ``publicID`` argument is no longer used as the
        identifier (i.e. name) of the default graph as was the case before
        version 7.0. In the case of sources that do not support named graphs,
        the ``publicID`` parameter will also not be used as the name for the
        graph that the data is loaded into, and instead the triples from sources
        that do not support named graphs will be loaded into the default graph
        (i.e. :attr:`.Dataset.default_context`).
        """
        source = create_input_source(
            source=source,
            publicID=publicID,
            location=location,
            file=file,
            data=data,
            format=format,
        )

        # NOTE on type hint: `xml.sax.xmlreader.InputSource.getPublicId` has no
        # type annotations but given that systemId should be a string, and
        # given that there is no specific mention of type for publicId, it
        # seems reasonable to assume it should also be a string. Furthermore,
        # create_input_source will ensure that publicId is not None, though it
        # would be good if this guarantee was made more explicit i.e. by type
        # hint on InputSource (TODO/FIXME).

        context = self.default_context
        context.parse(source, publicID=publicID, format=format, **args)
        
        self.graph(context)
        # TODO: FIXME: This should not return context, but self.
        return context

    def add_graph(self, g: _ContextIdentifierType | Graph | str | None) -> Graph:
        """alias of graph for consistency"""
        return self.graph(g)

    def remove_graph(
        self: _DatasetT, g: _ContextIdentifierType | Graph | str | None
    ) -> _DatasetT:
        if not isinstance(g, Graph):
            g = self.get_context(g)

        self.store.remove_graph(g)
        if g is None or g == self.default_context:
            # default graph cannot be removed
            # only triples deleted, so add it back in
            self.store.add_graph(self.default_context)
        return self

    def contexts(
        self, triple: _TripleType | None = None
    ) -> Generator[Graph, None, None]:
        default = False
        for c in self._contexts(triple):
            default |= c.identifier == DATASET_DEFAULT_GRAPH_ID
            yield c
        if not default:
            yield self.graph(DATASET_DEFAULT_GRAPH_ID)

    graphs = contexts

    def quads(  # type: ignore[override]
        self, quad: _TripleOrQuadPatternType | None = None
    ) -> Generator[_OptionalIdentifiedQuadType, None, None]:
        for s, p, o, c in self._quads(quad):
            # type error: Item "None" of "Optional[Graph]" has no attribute "identifier"
            if c.identifier == self.default_context:  # type: ignore[union-attr]
                yield s, p, o, None
            else:
                # type error: Item "None" of "Optional[Graph]" has no attribute "identifier"  [union-attr]
                yield s, p, o, c.identifier  # type: ignore[union-attr]

    # type error: Return type "Generator[tuple[Node, URIRef, Node, Optional[IdentifiedNode]], None, None]" of "__iter__" incompatible with return type "Generator[tuple[IdentifiedNode, IdentifiedNode, Union[IdentifiedNode, Literal]], None, None]" in supertype "Graph"
    def __iter__(  # type: ignore[override]
        self,
    ) -> Generator[_OptionalIdentifiedQuadType, None, None]:
        """Iterates over all quads in the store"""
        return self.quads((None, None, None, None))
