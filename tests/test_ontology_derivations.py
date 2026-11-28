"""What the terms let the experiment do: the statements of the spectro ontology (no GUI needed)"""
import numpy as np
import pytest

pytest.importorskip('pymodaq_ontology', reason='The ontology manager is needed')

from pymodaq_ontology.source_factory import SourceFactory
from pymodaq_ontology.terms import TermHierarchy

from pymodaq_plugins_mockexamples.extensions.spectro_concepts import TERMS_FILE
from pymodaq_plugins_mockexamples.hardware.spectro_bench import (SpectroBench, WAVELENGTHS, transmittance_of_sample,
                                                                 DARK_LEVEL)
from pymodaq_plugins_mockexamples.ontology_derivations import (Derivations, Step, SAMPLE, REFERENCE, DARK,
                                                               TRANSMITTANCE, ABSORBANCE)

NS = 'http://example.org/mockexamples#'
SPECTRUM, BEAM_BLOCK, HOLDER = NS + 'Spectrum', NS + 'BeamBlock', NS + 'SampleHolder'


@pytest.fixture
def derivations():
    source = SourceFactory.create('rdf', str(TERMS_FILE))
    terms = source.terms()  # also reads the graph
    return Derivations(source.graph, TermHierarchy(terms).is_a)


def spectra():
    bench = SpectroBench()
    out = {}
    for iri, (block, sample) in ((DARK, (1, 0)), (REFERENCE, (0, 0)), (SAMPLE, (0, 1))):
        bench.beam_block, bench.sample_position = block, sample
        out[iri] = bench.grab_spectrum()
    return out


def test_the_ontology_declares_the_derivations(derivations):
    assert derivations.rules[TRANSMITTANCE] == sorted([SAMPLE, REFERENCE, DARK])
    assert derivations.rules[ABSORBANCE] == [TRANSMITTANCE]


def test_the_ontology_declares_the_state_of_the_bench_for_each_measurement(derivations):
    assert derivations.requirements[DARK] == [(BEAM_BLOCK, 1.)]
    assert derivations.requirements[REFERENCE] == [(BEAM_BLOCK, 0.), (HOLDER, 0.)]
    assert derivations.requirements[SAMPLE] == [(BEAM_BLOCK, 0.), (HOLDER, 1.)]


def test_the_plan_finds_the_actuators_by_their_terms(derivations):
    """A spectrometer and two actuators with names that say nothing"""
    steps, problems = derivations.plan([SPECTRUM], {'M2': BEAM_BLOCK, 'M1': HOLDER})
    assert problems == {}
    assert steps == [Step(DARK, [('M2', 1.)]), Step(REFERENCE, [('M2', 0.), ('M1', 0.)]),
                     Step(SAMPLE, [('M2', 0.), ('M1', 1.)])]


def test_the_plan_names_what_is_missing(derivations):
    steps, problems = derivations.plan([SPECTRUM], {'M2': BEAM_BLOCK})  # no cuvette holder
    assert [s.term for s in steps] == [DARK]
    assert problems == {REFERENCE: [HOLDER], SAMPLE: [HOLDER]}


def test_a_channel_with_an_unrelated_term_measures_nothing(derivations):
    assert derivations.plan([NS + 'Temperature'], {'M2': BEAM_BLOCK, 'M1': HOLDER}) == ([], {})


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


def test_a_general_spectrum_is_not_a_sample_spectrum(derivations):
    available = spectra()
    available[SPECTRUM] = available.pop(SAMPLE)
    assert derivations.computable(available) == []


def test_the_bench_follows_its_actuators():
    bench = SpectroBench()
    bench.beam_block = 1
    assert bench.grab_spectrum().mean() == pytest.approx(DARK_LEVEL, rel=0.1)
    bench.beam_block, bench.sample_position = 0, 0
    blank = bench.grab_spectrum()
    bench.sample_position = 1
    assert bench.grab_spectrum()[np.argmin(np.abs(WAVELENGTHS - 550.))] < 0.4 * blank[np.argmin(np.abs(WAVELENGTHS - 550.))]
    assert SpectroBench.shared() is SpectroBench.shared()
