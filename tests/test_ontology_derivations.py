"""What can be computed from the terms: the derivations declared by the spectro ontology (no GUI needed)"""
import numpy as np
import pytest

pytest.importorskip('pymodaq_ontology', reason='The ontology manager is needed')

from pymodaq_ontology.source_factory import SourceFactory
from pymodaq_ontology.terms import TermHierarchy

from pymodaq_plugins_mockexamples.extensions.spectro_concepts import TERMS_FILE
from pymodaq_plugins_mockexamples.hardware.mock_spectro import (MockSpectro, WAVELENGTHS, lamp_spectrum,
                                                                transmittance_of_sample, DARK_LEVEL)
from pymodaq_plugins_mockexamples.ontology_derivations import (Derivations, SAMPLE, REFERENCE, DARK, TRANSMITTANCE,
                                                               ABSORBANCE)

NS = 'http://example.org/mockexamples#'


@pytest.fixture
def derivations():
    source = SourceFactory.create('rdf', str(TERMS_FILE))
    terms = source.terms()  # also reads the graph
    return Derivations(source.graph, TermHierarchy(terms).is_a)


def spectra():
    return {iri: MockSpectro(kind).grab_spectrum() for iri, kind in
            ((SAMPLE, 'sample'), (REFERENCE, 'reference'), (DARK, 'dark'))}


def test_the_ontology_declares_the_derivations(derivations):
    assert derivations.rules[TRANSMITTANCE] == sorted([SAMPLE, REFERENCE, DARK])
    assert derivations.rules[ABSORBANCE] == [TRANSMITTANCE]


def test_nothing_is_computable_without_the_inputs(derivations):
    assert derivations.computable({}) == []
    assert derivations.missing({}) == {TRANSMITTANCE: sorted([SAMPLE, REFERENCE, DARK]),
                                       ABSORBANCE: [TRANSMITTANCE]}


def test_the_missing_input_is_named(derivations):
    available = spectra()
    del available[DARK]
    assert derivations.computable(available) == []
    assert derivations.missing(available)[TRANSMITTANCE] == [DARK]


def test_transmittance_then_absorbance(derivations):
    available = spectra()
    assert derivations.computable(available) == [TRANSMITTANCE, ABSORBANCE]
    results = derivations.compute(available)
    expected = transmittance_of_sample()
    band = np.argmin(np.abs(WAVELENGTHS - 550.))
    assert results[TRANSMITTANCE][band] == pytest.approx(expected[band], abs=0.05)
    assert results[ABSORBANCE][band] == pytest.approx(-np.log10(expected[band]), abs=0.1)


def test_a_kind_of_the_input_is_accepted(derivations):
    """Whatever term stands for the sample (here the more general Spectrum is NOT enough, a kind of sample is)"""
    assert derivations.is_a(SAMPLE, NS + 'Spectrum')
    available = spectra()
    available[NS + 'Spectrum'] = available.pop(SAMPLE)  # a general spectrum is not a sample spectrum
    assert derivations.computable(available) == []


def test_the_mock_spectra():
    assert MockSpectro('dark').grab_spectrum().mean() == pytest.approx(DARK_LEVEL, rel=0.1)
    assert MockSpectro('reference').grab_spectrum().max() > 10 * DARK_LEVEL
    assert lamp_spectrum().max() > 0
    with pytest.raises(ValueError):
        MockSpectro('unknown')
