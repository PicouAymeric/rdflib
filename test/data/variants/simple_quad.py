from rdflib import Dataset, Graph
from test.utils.namespace import EGDO


def populate_graph(graph: Graph) -> None:
    assert isinstance(graph, Dataset)

    egdo_graph = graph.get_context(EGDO.graph)
    egdo_graph.add((EGDO.subject, EGDO.predicate, EGDO.object))


__all__ = ["populate_graph"]
