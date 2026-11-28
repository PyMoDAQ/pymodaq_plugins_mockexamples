"""Demo extension: what the terms of the channels let the experiment do, whatever the modules are called

It uses the ``OntologyManager`` of the ``pymodaq_ontology`` package (menu *Ontology* of the Dashboard). The bench of the
experiments ``spectro_lab_a`` and ``spectro_lab_b`` is one spectrometer, a beam block and a cuvette holder, with neutral
module names. The user assigns the term *Spectrum* to the
spectrometer, and associates each value of the actuators, as configured on the bench (1, 0, 12.5...), with a state of
the ontology (*Beam blocked*, *Beam open*, *Blank in beam*, *Sample in beam*) in the manager. The extension only knows
states, never the values nor the names of the modules, and can then:

* tell what it can **measure**: the ontology says in which state of the bench a spectrum is a *Dark spectrum* (beam
  blocked), a *Reference spectrum* (beam open, blank cuvette) or a *Sample spectrum*; the manager gives the moves that
  reach these states, or tells which state has no value yet;
* tell what it can then **compute** (a *Transmittance* is derived from the three spectra, an *Absorbance* from the
  transmittance) and run the whole protocol: set the bench, grab, three times, then compute and show, with the formulas
  coded here;
* check that what a channel gives has the **unit** its term expects (counts for a spectrum).

Without ``pymodaq_ontology`` the extension tells that it cannot work.
"""
from pathlib import Path
from typing import Optional

import numpy as np
from qtpy import QtWidgets

from rdflib import URIRef
from pymodaq_utils.logger import set_logger, get_module_name

from pymodaq_data import DataToExport
from pymodaq_data.data import DataCalculated

from pymodaq_gui import utils as gutils
from pymodaq_gui.plotting.data_viewers import ViewerDispatcher

from pymodaq.control_modules.enums import MoveType
from pymodaq.utils.custom_ext import CustomExt
from pymodaq.utils.data import DataActuator
from pymodaq.utils.managers.modules import ModuleType

from pymodaq_plugins_mockexamples.ontology_derivations import Derivations, MOCK, Step

logger = set_logger(get_module_name(__file__))

EXTENSION_NAME = 'Spectro Concepts'  # displayed in the Extensions menu of the Dashboard
CLASS_NAME = 'SpectroConcepts'  # the name of the class below

TERMS_FILE = Path(__file__).parent.parent.joinpath('resources', 'ontology', 'spectro_ontology.ttl')


class SpectroConcepts(CustomExt):

    params = [
        {'title': 'Status:', 'name': 'status', 'type': 'str', 'value': 'Idle', 'readonly': True},
    ]

    def __init__(self, parent: gutils.DockArea, dashboard):
        super().__init__(parent, dashboard)
        self.ontology_manager = getattr(dashboard, 'extra_managers', {}).get('ontology')
        self._busy = False
        self._queue, self._results, self._problems, self._step, self._axis = [], {}, [], None, None
        self.derivations: Optional[Derivations] = None
        self.setup_ui()
        if self.ontology_manager is None:
            self.set_status('pymodaq_ontology is not installed: nothing to compute')
        elif self.ontology_manager.source is None:
            self._load_spectro_ontology()

    def setup_docks_and_widgets(self):
        self.docks['settings'] = gutils.Dock('Settings')
        self.dockarea.addDock(self.docks['settings'])
        self.docks['settings'].addWidget(self.settings_tree)
        self.docks['what'] = gutils.Dock('What the terms allow')
        self.dockarea.addDock(self.docks['what'], 'bottom', self.docks['settings'])
        self.what = QtWidgets.QPlainTextEdit(readOnly=True)
        self.docks['what'].addWidget(self.what)
        self.viewer = ViewerDispatcher(self.dockarea, title='Data')

    def setup_menus_and_toolbars(self, menubar: QtWidgets.QMenuBar = None):
        self.create_dashboard_toolbar(add_break=False)

    def setup_actions(self):
        self.add_action('check', 'What can I measure?', 'help',
                        tip='Tell what the terms of the channels allow to measure and compute, without acquiring')
        self.add_action('run', 'Measure and compute', 'camera',
                        tip='Set the bench for each measurement, grab, then compute and show')

    def connect_things(self):
        self.connect_action('check', self.show_what_is_possible)
        self.connect_action('run', self.run_protocol)
        self.modules_manager.timeout_signal.connect(self._on_timeout)

    def _load_spectro_ontology(self) -> None:
        from pymodaq_ontology.source_factory import SourceFactory
        self.ontology_manager.set_source(SourceFactory.create('rdf', str(TERMS_FILE)))

    # ---- the ontology side: terms of the channels
    def terms_of(self, kind: str) -> dict[str, str]:
        """Term assigned to each channel of the detectors or of the actuators, by channel key"""
        manager = self.ontology_manager
        manager.update_channels_from_dashboard()
        return {c.key: manager.assignment.get(c.key) for c in manager.channels if c.kind == kind
                and manager.assignment.get(c.key)}

    def _derivations(self) -> Optional[Derivations]:
        """The statements of the ontology of the manager (read again if the source changed)"""
        graph = getattr(self.ontology_manager.source, 'graph', None)
        if graph is None:
            return None
        if self.derivations is None or self.derivations.graph is not graph:
            self.derivations = Derivations(graph, self.ontology_manager.hierarchy.is_a)
        return self.derivations

    def _label(self, iri: str) -> str:
        term = self.ontology_manager.terms.get(iri)
        return term.label if term else iri

    def make_plan(self) -> tuple[list[Step], dict[str, list[str]], Optional[Derivations]]:
        derivations = self._derivations()
        if derivations is None:
            return [], {}, None
        detector_terms = set(self.terms_of('detector').values())
        steps, problems = derivations.plan(detector_terms, self.ontology_manager.moves_for_states)
        return steps, problems, derivations

    def show_what_is_possible(self) -> str:
        """Say what can be measured and computed with the terms assigned to the channels (without acquiring)"""
        if self.ontology_manager is None:
            text = 'pymodaq_ontology is not installed'
        else:
            steps, problems, derivations = self.make_plan()
            if derivations is None:
                text = 'The ontology loaded in the manager has no graph: load an RDF ontology'
            else:
                text = self._describe(steps, problems, derivations)
        self.what.setPlainText(text)
        self.set_status(text.splitlines()[0] if text else 'Idle')
        return text

    def _describe(self, steps: list[Step], problems: dict[str, list[str]], derivations: Derivations) -> str:
        lines = []
        if steps:
            lines.append('Can measure: ' + ', '.join(self._label(step.term) for step in steps))
        else:
            lines.append('Nothing can be measured yet (assign a term to the spectrometer)')
        for step in steps:
            moves = ', '.join(f'{module} = {value:g}' for module, value in step.moves)
            lines.append(f'  {self._label(step.term)}: {moves}')
        for term, controls in problems.items():
            states = ', '.join(self._label(c) for c in controls)
            lines.append(f'{self._label(term)} needs a value of an actuator for: {states}')
        available = {step.term: None for step in steps}
        computable = derivations.computable(available)
        if computable:
            lines.append('Then can compute: ' + ', '.join(self._label(i) for i in computable))
        return '\n'.join(lines)

    # ---- the protocol: set the bench, grab, for each measurement
    def run_protocol(self):
        if self._busy or self.ontology_manager is None:
            return
        steps, problems, derivations = self.make_plan()
        if not steps or problems:
            self.show_what_is_possible()
            return
        self._queue, self._results, self._problems, self._busy = list(steps), {}, [], True
        self.set_action_enabled('run', False)
        self._next_step()

    def _next_step(self):
        if not self._queue:
            self._finish()
            return
        self._step = self._queue.pop(0)
        self.set_status(f'Measuring {self._label(self._step.term)}')
        detectors = sorted({c.module for c in self.ontology_manager.channels if c.kind == 'detector'
                            and self.ontology_manager.assignment.get(c.key)})
        self.modules_manager.selected_actuators_name = [module for module, _ in self._step.moves]
        self.modules_manager.selected_detectors_name = detectors
        target = DataToExport('target', data=[
            DataActuator(module, data=value, units=self.modules_manager.get_mod_from_name(
                module, ModuleType.Actuator).units) for module, value in self._step.moves])
        self.modules_manager.move_actuators_with_callback(target, mode=MoveType.ABS, callback=self._on_move_done)

    def _on_move_done(self, positions: DataToExport):
        self.modules_manager.forget_callback(self._on_move_done, ModuleType.Actuator)
        self.modules_manager.grab_data_with_callback(callback=self._on_data)

    def _on_data(self, data: DataToExport):
        self.modules_manager.forget_callback(self._on_data, ModuleType.Detector)
        arrays, problems, axis = self.arrays_by_term(data)
        # the channel with the general term (Spectrum) gives the spectrum of the measurement (Dark spectrum...)
        derivations = self._derivations()
        spectrum = next((array for term, array in arrays.items() if derivations.is_a(self._step.term, term)), None)
        if spectrum is not None:
            self._results[self._step.term] = spectrum
            self._axis = axis
        self._problems.extend(p for p in problems if p not in self._problems)
        self._next_step()

    def arrays_by_term(self, data: DataToExport) -> tuple[dict[str, np.ndarray], list[str], object]:
        """The array of each term assigned to a channel of the data, the unit problems and the axis of the first one"""
        from pymodaq_ontology.channels import Channel
        from pymodaq_ontology.terms import DETECTOR
        assigned = self.ontology_manager.assignment
        graph = self.ontology_manager.source.graph
        arrays, problems, axis = {}, [], None
        for dwa in data.data:
            labels = list(dwa.labels) if getattr(dwa, 'labels', None) else []
            for index, array in enumerate(dwa.data):
                label = labels[index] if index < len(labels) else f'CH{index:02d}'
                key = Channel(module=dwa.origin, kind=DETECTOR, data_name=dwa.name, label=label).key
                iri = assigned.get(key)
                if not iri:
                    continue
                arrays[iri] = np.asarray(array, dtype=float)
                if axis is None and dwa.axes:
                    axis = dwa.axes[0]
                expected = graph.value(URIRef(iri), MOCK.unit)
                if expected is not None and str(expected) != '1' and dwa.units and str(expected) != dwa.units:
                    problems.append(f'{key}: {dwa.units} where {self._label(iri)} expects {expected}')
        return arrays, problems, axis

    def _finish(self):
        derivations = self._derivations()
        results = derivations.compute(self._results)
        measured = [DataCalculated(self._label(iri), data=[array], axes=[self._axis] if self._axis is not None else [],
                                   labels=[self._label(iri)], units='counts') for iri, array in self._results.items()]
        computed = [DataCalculated(self._label(iri), data=[array], axes=[self._axis] if self._axis is not None else [],
                                   labels=[self._label(iri)]) for iri, array in results.items()]
        self.viewer.show_data(DataToExport('spectro', data=[*measured, *computed]))
        lines = ['Measured: ' + ', '.join(self._label(i) for i in self._results),
                 'Computed: ' + (', '.join(self._label(i) for i in results) or 'nothing')]
        lines.extend(f'Unit: {p}' for p in self._problems)
        self.what.setPlainText('\n'.join(lines))
        self.set_status(lines[1])
        self._busy = False
        self.set_action_enabled('run', True)

    def _on_timeout(self, missing_modules: list):
        for callback in (self._on_move_done, self._on_data):
            self.modules_manager.forget_callback(callback, ModuleType.Control)
        self._busy = False
        self.set_action_enabled('run', True)
        self.set_status(f'Timeout: {", ".join(missing_modules)}')

    def set_status(self, status: str):
        self.settings.child('status').setValue(status)

    def _quit_fun(self) -> bool:
        if self._busy:
            self.update_status('Wait for the end of the grab before quitting')
            return False
        self.modules_manager.timeout_signal.disconnect(self._on_timeout)
        return True


def main():
    """Run the extension on its own (the Dashboard stays hidden), see ``-x EXPERIMENT_NAME -s STATE_NAME``"""
    import sys
    from pymodaq_gui.qt_utils import mkQApp
    from pymodaq.dashboard import load_dashboard_with_arguments
    from pymodaq.utils.gui_utils.loader_utils import create_extension

    app = mkQApp('Spectro Concepts')
    win, dashboard, _ = load_dashboard_with_arguments(show_dashboard=False, load_extension=False)
    win.mainwindow.setVisible(False)
    win_ext, ext = create_extension(dashboard, SpectroConcepts, show_extension=True)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
