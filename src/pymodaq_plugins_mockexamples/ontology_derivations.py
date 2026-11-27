"""What can be computed from the terms of the channels: the derivations declared by an ontology

The ontology says that a term is ``mock:derivedFrom`` other terms (``Transmittance`` from the sample, the reference and
the dark spectra). This module reads these statements in the RDF graph and, given the arrays of the channels that have
a term, tells what can be computed, what is missing, and computes it. It knows nothing about the instruments: it works
on terms. A channel whose term is a kind of the input (a ``SampleSpectrum`` is a ``Spectrum``) is accepted wherever the
input is that more general term.
"""
from typing import Callable, Optional

import numpy as np
from rdflib import Graph, Namespace, URIRef

MOCK = Namespace('http://example.org/mockexamples#')
SAMPLE, REFERENCE, DARK = (str(MOCK[name]) for name in ('SampleSpectrum', 'ReferenceSpectrum', 'DarkSpectrum'))
TRANSMITTANCE, ABSORBANCE = str(MOCK.Transmittance), str(MOCK.Absorbance)


def _transmittance(inputs: dict[str, np.ndarray]) -> np.ndarray:
    dark = inputs[DARK]
    reference = inputs[REFERENCE] - dark
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(reference > 0, (inputs[SAMPLE] - dark) / reference, np.nan)


def _absorbance(inputs: dict[str, np.ndarray]) -> np.ndarray:
    with np.errstate(divide='ignore', invalid='ignore'):
        return -np.log10(np.where(inputs[TRANSMITTANCE] > 0, inputs[TRANSMITTANCE], np.nan))


FORMULAS: dict[str, Callable[[dict[str, np.ndarray]], np.ndarray]] = {
    TRANSMITTANCE: _transmittance,
    ABSORBANCE: _absorbance,
}


class Derivations:
    """The derivations of an ontology graph

    Parameters
    ----------
    graph: rdflib.Graph
        the ontology, with ``mock:derivedFrom`` statements
    is_a: callable
        ``is_a(term, other)``: whether the term is ``other`` or a kind of it (the hierarchy of the ontology manager)
    """

    def __init__(self, graph: Graph, is_a: Callable[[str, str], bool]):
        self.graph = graph
        self.is_a = is_a
        self.rules: dict[str, list[str]] = {}
        for output in set(graph.subjects(MOCK.derivedFrom, None)):
            self.rules[str(output)] = sorted(str(i) for i in graph.objects(output, MOCK.derivedFrom)
                                             if isinstance(i, URIRef))

    def _provider(self, wanted: str, available: dict[str, np.ndarray]) -> Optional[str]:
        """The available term standing for the wanted one: the same or a kind of it"""
        return next((term for term in sorted(available) if self.is_a(term, wanted)), None)

    def missing(self, available: dict[str, np.ndarray]) -> dict[str, list[str]]:
        """For each derived term that cannot be computed yet, the inputs that no channel (or derivation) provides"""
        have = dict(available)
        for output, _inputs in self._order(have):
            have[output] = None  # placeholder, only the terms are looked at here
        return {output: [i for i in inputs if self._provider(i, have) is None]
                for output, inputs in self.rules.items()
                if output not in have and any(self._provider(i, have) is None for i in inputs)}

    def _order(self, available: dict) -> list[tuple[str, list[str]]]:
        """The derivations that can be done, in an order where each one has its inputs"""
        have, done = dict(available), []
        progress = True
        while progress:
            progress = False
            for output, inputs in self.rules.items():
                if output not in have and all(self._provider(i, have) is not None for i in inputs):
                    have[output] = None
                    done.append((output, inputs))
                    progress = True
        return done

    def computable(self, available: dict[str, np.ndarray]) -> list[str]:
        """The derived terms that can be computed, each after its inputs"""
        return [output for output, _ in self._order(available)]

    def compute(self, available: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """The arrays of the derived terms that can be computed (those without a formula are left out)"""
        have = dict(available)
        results = {}
        for output, inputs in self._order(available):
            if output not in FORMULAS:
                continue
            arrays = {i: have[self._provider(i, have)] for i in inputs}
            have[output] = results[output] = FORMULAS[output](arrays)
        return results
