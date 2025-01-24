import pathlib
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Generator, Iterable, NoReturn, Optional, TextIO, TypeVar, Union, cast, overload
import warnings
import rdflib
from rdflib import plugin
from rdflib.namespace import NamespaceManager
from rdflib.paths import Path
from rdflib.term import BNode, IdentifiedNode, Identifier, URIRef, Literal
from rdflib.graph import _GraphT, _ObjectType, _PredicateType, _SubjectType, _TripleOrTriplePathType, _TriplePathPatternType, _TriplePathType, _TriplePatternType, _TripleSelectorType, Graph, _TripleType, _assertnode
from rdflib.parser import InputSource, create_input_source
from rdflib.store import Store
import typing_extensions as te

DATASET_DEFAULT_GRAPH_ID = URIRef("urn:x-rdflib:default")
_DatasetT = TypeVar("_DatasetT", bound="Dataset")
_BatchAddGraphT = TypeVar("_BatchAddGraphT", bound="BatchAddGraph")

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Mapping
    from rdflib.plugins.sparql.sparql import Query, Update

_ContextIdentifierType: te.TypeAlias = Union[IdentifiedNode]

_QuadType: te.TypeAlias = tuple[
    _SubjectType, _PredicateType, _ObjectType, _ContextIdentifierType
]
_OptionalQuadType: te.TypeAlias = tuple[
    _SubjectType, _PredicateType, _ObjectType, Optional[_ContextIdentifierType]
]
_TripleOrOptionalQuadType: te.TypeAlias = Union[_TripleType, _OptionalQuadType]
_OptionalIdentifiedQuadType: te.TypeAlias = tuple[
    _SubjectType, _PredicateType, _ObjectType, Optional[_ContextIdentifierType]
]
_QuadPatternType: te.TypeAlias = tuple[
    Optional[_SubjectType],
    Optional[_PredicateType],
    Optional[_ObjectType],
    Optional[_ContextIdentifierType],
]
_QuadPathPatternType: te.TypeAlias = tuple[
    Optional[_SubjectType],
    Path,
    Optional[_ObjectType],
    Optional[_ContextIdentifierType],
]
_TripleOrQuadPatternType: te.TypeAlias = Union[_TriplePatternType, _QuadPatternType]
_TripleOrQuadPathPatternType: te.TypeAlias = Union[
    _TriplePathPatternType, _QuadPathPatternType
]
_QuadSelectorType: te.TypeAlias = tuple[
    Optional[_SubjectType],
    Optional[Union[Path, _PredicateType]],
    Optional[_ObjectType],
    Optional[_ContextIdentifierType],
]
_TripleOrQuadSelectorType: te.TypeAlias = Union[_TripleSelectorType, _QuadSelectorType]

__all__ = [
    "Dataset",
    "_DatasetT",
    "BatchAddGraph"
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
    default_context: Graph

    def __init__(
        self,
        store: Store | str = "default",
        default_union: bool = False,
        default_graph_base: str | None = None,
    ):
        super(Dataset, self).__init__(store)

        assert self.store.context_aware, (
            "Datasets must be backed by" " a context aware store."
        )
        self.context_aware = True
        self.default_union = default_union

        if not self.store.graph_aware:
            raise Exception("Dataset must be backed by a graph-aware store!")
        self.default_context = Graph(
            store=self.store,
            base=default_graph_base,
        )


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
        identifier: _ContextIdentifierType | str | None = None,
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

        c = self.conjonctiveParse(
            self, source, publicID, format, location, file, data, **args
        )
        self.graph(c)
        return c

    def add_graph(self, g: _ContextIdentifierType | Graph | str | None) -> Graph:
        """alias of graph for consistency"""
        return self.graph(g)

    def remove_graph(
        self: _DatasetT, g: _ContextIdentifierType | str | None
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

    def query(
        self,
        query_object: str | Query,
        processor: str | rdflib.query.Processor = "sparql",
        result: str | type[rdflib.query.Result] = "sparql",
        initNs: Mapping[str, Any] | None = None,  # noqa: N803
        initBindings: Mapping[str, Identifier] | None = None,  # noqa: N803
        use_store_provided: bool = True,
        **kwargs: Any,
    ) -> rdflib.query.Result:
        """
        Query this graph.

        A type of 'prepared queries' can be realised by providing initial
        variable bindings with initBindings

        Initial namespaces are used to resolve prefixes used in the query, if
        none are given, the namespaces from the graph's namespace manager are
        used.

        .. caution::

           This method can access indirectly requested network endpoints, for
           example, query processing will attempt to access network endpoints
           specified in ``SERVICE`` directives.

           When processing untrusted or potentially malicious queries, measures
           should be taken to restrict network and file access.

           For information on available security measures, see the RDFLib
           :doc:`Security Considerations </security_considerations>`
           documentation.

        :returntype: :class:`~rdflib.query.Result`

        """

        initBindings = initBindings or {}  # noqa: N806
        initNs = initNs or dict(self.namespaces())  # noqa: N806

        if hasattr(self.store, "query") and use_store_provided:
            try:
                return self.store.query(
                    query_object,
                    initNs,
                    initBindings,
                    "__UNION__",
                    **kwargs,
                )
            except NotImplementedError:
                pass  # store has no own implementation

        if not isinstance(result, rdflib.query.Result):
            result = plugin.get(cast(str, result), rdflib.query.Result)
        if not isinstance(processor, rdflib.query.Processor):
            processor = plugin.get(processor, rdflib.query.Processor)(self)

        # type error: Argument 1 to "Result" has incompatible type "Mapping[str, Any]"; expected "str"
        return result(processor.query(query_object, initBindings, initNs, **kwargs))  # type: ignore[arg-type]

    def update(
        self,
        update_object: Update | str,
        processor: str | rdflib.query.UpdateProcessor = "sparql",
        initNs: Mapping[str, Any] | None = None,  # noqa: N803
        initBindings: (  # noqa: N803
            Mapping[str, rdflib.query.QueryBindingsValueType] | None
        ) = None,
        use_store_provided: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Update this graph with the given update query.

        .. caution::

           This method can access indirectly requested network endpoints, for
           example, query processing will attempt to access network endpoints
           specified in ``SERVICE`` directives.

           When processing untrusted or potentially malicious queries, measures
           should be taken to restrict network and file access.

           For information on available security measures, see the RDFLib
           :doc:`Security Considerations </security_considerations>`
           documentation.
        """
        initBindings = initBindings or {}  # noqa: N806
        initNs = initNs or dict(self.namespaces())  # noqa: N806

        if hasattr(self.store, "update") and use_store_provided:
            try:
                return self.store.update(
                    update_object,
                    initNs,
                    initBindings,
                    "__UNION__",
                    **kwargs,
                )
            except NotImplementedError:
                pass  # store has no own implementation

        if not isinstance(processor, rdflib.query.UpdateProcessor):
            processor = plugin.get(processor, rdflib.query.UpdateProcessor)(self)

        return processor.update(update_object, initBindings, initNs, **kwargs)

    def addN(self: _DatasetT, quads: Iterable[_QuadType]) -> _DatasetT:  # noqa: N802
        """Add a sequence of triple with context"""

        self.__store.addN(
            (s, p, o, c)
            for s, p, o, c in quads
            if isinstance(c, Graph)
            and c.identifier is self.identifier
            and _assertnode(s, p, o)
        )
        return self


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
    def quads(
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

    def contexts(
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

    # FIXME to merge with parse
    def conjonctiveParse(
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
        Parse source adding the resulting triples to its own context (sub graph
        of this graph).

        See :meth:`rdflib.graph.Graph.parse` for documentation on arguments.

        If the source is in a format that does not support named graphs its triples
        will be added to the default graph
        (i.e. :attr:`ConjunctiveGraph.default_context`).

        :Returns:

        The graph into which the source was parsed. In the case of n3 it returns
        the root context.

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
        (i.e. :attr:`ConjunctiveGraph.default_context`).
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
        # TODO: FIXME: This should not return context, but self.
        return context

    def __reduce__(self) -> tuple[type[Graph], tuple[Store, _ContextIdentifierType]]:
        return _DatasetT, (self.store, self.identifier)
    
    
class BatchAddGraph:
    """
    Wrapper around graph that turns batches of calls to Graph's add
    (and optionally, addN) into calls to batched calls to addN`.

    :Parameters:

      - graph: The graph to wrap
      - batch_size: The maximum number of triples to buffer before passing to
        Graph's addN
      - batch_addn: If True, then even calls to `addN` will be batched according to
        batch_size

    graph: The wrapped graph
    count: The number of triples buffered since initialization or the last call to reset
    batch: The current buffer of triples

    """

    def __init__(self, graph: Graph, batch_size: int = 1000, batch_addn: bool = False):
        if not batch_size or batch_size < 2:
            raise ValueError("batch_size must be a positive number")
        self.graph = graph
        self.__graph_tuple = (graph,)
        self.__batch_size = batch_size
        self.__batch_addn = batch_addn
        self.reset()

    def reset(self) -> _BatchAddGraphT:
        """
        Manually clear the buffered triples and reset the count to zero
        """
        self.batch: list[_QuadType] = []
        self.count = 0
        return self

    def add(self, triple_or_quad: _TripleType | _QuadType) -> _BatchAddGraphT:
        """
        Add a triple to the buffer

        :param triple: The triple to add
        """
        if len(self.batch) >= self.__batch_size:
            self.graph.addN(self.batch)
            self.batch = []
        self.count += 1
        if len(triple_or_quad) == 3:
            # type error: Argument 1 to "append" of "list" has incompatible type "tuple[Node, ...]"; expected "tuple[Node, Node, Node, Graph]"
            self.batch.append(triple_or_quad + self.__graph_tuple)  # type: ignore[arg-type, unused-ignore]
        else:
            # type error: Argument 1 to "append" of "list" has incompatible type "Union[tuple[Node, Node, Node], tuple[Node, Node, Node, Graph]]"; expected "tuple[Node, Node, Node, Graph]"
            self.batch.append(triple_or_quad)  # type: ignore[arg-type, unused-ignore]
        return self

    def addN(self, quads: Iterable[_QuadType]) -> _BatchAddGraphT:  # noqa: N802
        if self.__batch_addn:
            for q in quads:
                self.add(q)
        else:
            self.graph.addN(quads)
        return self

    def __enter__(self) -> _BatchAddGraphT:
        self.reset()
        return self

    def __exit__(self, *exc) -> None:
        if exc[0] is None:
            self.graph.addN(self.batch)
            

class ModificationException(Exception):  # noqa: N818
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return (
            "Modifications and transactional operations not allowed on "
            "ReadOnlyGraphAggregate instances"
        )

class UnSupportedAggregateOperation(Exception):  # noqa: N818
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        return "This operation is not supported by ReadOnlyGraphAggregate " "instances"

# TODO check if this class is still relevant
class ReadOnlyGraphAggregate(Dataset):
    """Utility class for treating a set of graphs as a single graph

    Only read operations are supported (hence the name). Essentially a
    ConjunctiveGraph over an explicit subset of the entire store.
    """

    def __init__(self, graphs: list[Graph], store: Union[str, Store] = "default"):
        if store is not None:
            super(ReadOnlyGraphAggregate, self).__init__(store)
            Graph.__init__(self, store)
            self.__namespace_manager = None

        assert (
            isinstance(graphs, list)
            and graphs
            and [g for g in graphs if isinstance(g, Graph)]
        ), "graphs argument must be a list of Graphs!!"
        self.graphs = graphs

    def __repr__(self) -> str:
        return "<ReadOnlyGraphAggregate: %s graphs>" % len(self.graphs)

    def destroy(self, configuration: str) -> NoReturn:
        raise ModificationException()

    # Transactional interfaces (optional)
    def commit(self) -> NoReturn:
        raise ModificationException()

    def rollback(self) -> NoReturn:
        raise ModificationException()

    def open(self, configuration: str, create: bool = False) -> None:
        # TODO: is there a use case for this method?
        for graph in self.graphs:
            # type error: Too many arguments for "open" of "Graph"
            # type error: Argument 1 to "open" of "Graph" has incompatible type "ReadOnlyGraphAggregate"; expected "str"  [arg-type]
            # type error: Argument 2 to "open" of "Graph" has incompatible type "str"; expected "bool"  [arg-type]
            graph.open(self, configuration, create)  # type: ignore[call-arg, arg-type]

    # type error: Signature of "close" incompatible with supertype "Graph"
    def close(self) -> None:  # type: ignore[override]
        for graph in self.graphs:
            graph.close()

    def add(self, triple: _TripleOrOptionalQuadType) -> NoReturn:
        raise ModificationException()

    def addN(self, quads: Iterable[_QuadType]) -> NoReturn:  # noqa: N802
        raise ModificationException()

    # type error: Argument 1 of "remove" is incompatible with supertype "Graph"; supertype defines the argument type as "tuple[Optional[Node], Optional[Node], Optional[Node]]"
    def remove(self, triple: _TripleOrOptionalQuadType) -> NoReturn:  # type: ignore[override]
        raise ModificationException()

    # type error: Signature of "triples" incompatible with supertype "ConjunctiveGraph"
    @overload  # type: ignore[override]
    def triples(
        self,
        triple: _TriplePatternType,
    ) -> Generator[_TripleType, None, None]: ...

    @overload
    def triples(
        self,
        triple: _TriplePathPatternType,
    ) -> Generator[_TriplePathType, None, None]: ...

    @overload
    def triples(
        self,
        triple: _TripleSelectorType,
    ) -> Generator[_TripleOrTriplePathType, None, None]: ...

    def triples(
        self,
        triple: _TripleSelectorType,
    ) -> Generator[_TripleOrTriplePathType, None, None]:
        s, p, o = triple
        for graph in self.graphs:
            if isinstance(p, Path):
                for s, o in p.eval(self, s, o):
                    yield s, p, o
            else:
                for s1, p1, o1 in graph.triples((s, p, o)):
                    yield s1, p1, o1

    def __contains__(self, triple_or_quad: _TripleOrQuadSelectorType) -> bool:
        context = None
        if len(triple_or_quad) == 4:
            # type error: Tuple index out of range
            context = triple_or_quad[3]  # type: ignore [misc, unused-ignore]
        for graph in self.graphs:
            if context is None or graph.identifier == context.identifier:
                if triple_or_quad[:3] in graph:
                    return True
        return False

    # type error: Signature of "quads" incompatible with supertype "ConjunctiveGraph"
    def quads(  # type: ignore[override]
        self, triple_or_quad: _TripleOrQuadSelectorType
    ) -> Generator[
        tuple[_SubjectType, Path | _PredicateType, _ObjectType, Graph],
        None,
        None,
    ]:
        """Iterate over all the quads in the entire aggregate graph"""
        c = None
        if len(triple_or_quad) == 4:
            s, p, o, c = triple_or_quad
        else:
            s, p, o = triple_or_quad[:3]

        if c is not None:
            for graph in [g for g in self.graphs if g == c]:
                for s1, p1, o1 in graph.triples((s, p, o)):
                    yield s1, p1, o1, graph
        else:
            for graph in self.graphs:
                for s1, p1, o1 in graph.triples((s, p, o)):
                    yield s1, p1, o1, graph

    def __len__(self) -> int:
        return sum(len(g) for g in self.graphs)

    def __hash__(self) -> NoReturn:
        raise UnSupportedAggregateOperation()

    def __cmp__(self, other) -> int:
        if other is None:
            return -1
        elif isinstance(other, Graph):
            return -1
        elif isinstance(other, ReadOnlyGraphAggregate):
            return (self.graphs > other.graphs) - (self.graphs < other.graphs)
        else:
            return -1

    def __iadd__(self: _GraphT, other: Iterable[_TripleType]) -> NoReturn:
        raise ModificationException()

    def __isub__(self: _GraphT, other: Iterable[_TripleType]) -> NoReturn:
        raise ModificationException()

    # Conv. methods

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
        subject, predicate, object_ = triple
        for graph in self.graphs:
            # type error: Argument 1 to "triples_choices" of "Graph" has incompatible type "tuple[Union[list[Node], Node], Union[Node, list[Node]], Union[Node, list[Node]]]"; expected "Union[tuple[list[Node], Node, Node], tuple[Node, list[Node], Node], tuple[Node, Node, list[Node]]]"
            # type error note: unpacking discards type info
            choices = graph.triples_choices((subject, predicate, object_))  # type: ignore[arg-type]
            for s, p, o in choices:
                yield s, p, o

    def qname(self, uri: str) -> str:
        if hasattr(self, "namespace_manager") and self.namespace_manager:
            return self.namespace_manager.qname(uri)
        raise UnSupportedAggregateOperation()

    def compute_qname(self, uri: str, generate: bool = True) -> tuple[str, URIRef, str]:
        if hasattr(self, "namespace_manager") and self.namespace_manager:
            return self.namespace_manager.compute_qname(uri, generate)
        raise UnSupportedAggregateOperation()

    # type error: Signature of "bind" incompatible with supertype "Graph"
    def bind(  # type: ignore[override]
        self, prefix: str | None, namespace: Any, override: bool = True  # noqa: F811
    ) -> NoReturn:
        raise UnSupportedAggregateOperation()

    def namespaces(self) -> Generator[tuple[str, URIRef], None, None]:
        if hasattr(self, "namespace_manager"):
            for prefix, namespace in self.namespace_manager.namespaces():
                yield prefix, namespace
        else:
            for graph in self.graphs:
                for prefix, namespace in graph.namespaces():
                    yield prefix, namespace

    def absolutize(self, uri: str, defrag: int = 1) -> NoReturn:
        raise UnSupportedAggregateOperation()

    # type error: Signature of "parse" incompatible with supertype "ConjunctiveGraph"
    def parse(  # type: ignore[override]
        self,
        source: (
            IO[bytes] | TextIO | InputSource | str | bytes | pathlib.PurePath | None
        ),
        publicID: str | None = None,  # noqa: N803
        format: str | None = None,
        **args: Any,
    ) -> NoReturn:
        raise ModificationException()

    def n3(self, namespace_manager: NamespaceManager | None = None) -> NoReturn:
        raise UnSupportedAggregateOperation()

    def __reduce__(self) -> NoReturn:
        raise UnSupportedAggregateOperation()