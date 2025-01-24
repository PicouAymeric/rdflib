import pathlib
from typing import IO, Any, BinaryIO, Generator, TextIO, TypeVar
from rdflib.term import BNode, URIRef, Literal
from rdflib.graph import ConjunctiveGraph, Graph, _ContextIdentifierType, _OptionalIdentifiedQuadType, _TripleOrQuadPatternType, _TripleType
from rdflib.parser import InputSource
from rdflib.store import Store

DATASET_DEFAULT_GRAPH_ID = URIRef("urn:x-rdflib:default")
_DatasetT = TypeVar("_DatasetT", bound="Dataset")


__all__ = [
    "Dataset",
    "_DatasetT"
]
class Dataset(ConjunctiveGraph):
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

    .. note:: Dataset builds on the `ConjunctiveGraph` class but that class's direct
        use is now deprecated (since RDFLib 7.x) and it should not be used.
        `ConjunctiveGraph` will be removed from future RDFLib versions.

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

    def __init__(
        self,
        store: Store | str = "default",
        default_union: bool = False,
        default_graph_base: str | None = None,
    ):
        super(Dataset, self).__init__(store=store, identifier=None)

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

    # type error: Return type "tuple[Type[Dataset], tuple[Store, bool]]" of "__reduce__" incompatible with return type "tuple[Type[Graph], tuple[Store, IdentifiedNode]]" in supertype "ConjunctiveGraph"
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

        c = ConjunctiveGraph.parse(
            self, source, publicID, format, location, file, data, **args
        )
        self.graph(c)
        return c

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
        for c in super(Dataset, self).contexts(triple):
            default |= c.identifier == DATASET_DEFAULT_GRAPH_ID
            yield c
        if not default:
            yield self.graph(DATASET_DEFAULT_GRAPH_ID)

    graphs = contexts

    # type error: Return type "Generator[tuple[Node, Node, Node, Optional[Node]], None, None]" of "quads" incompatible with return type "Generator[tuple[Node, Node, Node, Optional[Graph]], None, None]" in supertype "ConjunctiveGraph"
    def quads(  # type: ignore[override]
        self, quad: _TripleOrQuadPatternType | None = None
    ) -> Generator[_OptionalIdentifiedQuadType, None, None]:
        for s, p, o, c in super(Dataset, self).quads(quad):
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
