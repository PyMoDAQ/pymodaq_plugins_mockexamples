"""Demo extension: what the terms of the channels let the experiment do, whatever the instruments are called

It uses the ``OntologyManager`` of the ``pymodaq_ontology`` package (menu *Ontology* of the Dashboard). The user assigns
a term to the channels of the instruments (for instance *Dark spectrum*, *Reference spectrum*, *Sample spectrum*), and
the extension, which never reads the names of the modules, can then:

* tell what can be **computed** from the terms (the ontology says that a *Transmittance* is derived from the sample, the
  reference and the dark spectra, and an *Absorbance* from the transmittance), and what is **missing** if it cannot;
* compute and show it live, with the formulas coded here;
* check that what the channels give has the **unit** the term expects (counts for a spectrum).

Try it with the experiments ``spectro_lab_a`` and ``spectro_lab_b``: the same three simulated spectrometers with
different names. Assign the terms in each one, the extension works the same.

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

from pymodaq.utils.custom_ext import CustomExt
from pymodaq.utils.managers.modules import ModuleType

from pymodaq_plugins_mockexamples.ontology_derivations import Derivations, MOCK

logger = set_logger(get_module_name(__file__))

EXTENSION_NAME = 'Spectro Concepts'  # displayed in the Extensions menu of the Dashboard
CLASS_NAME = 'SpectroConcepts'  # the name of the class below

TERMS_FILE = Path(__file__).parent.parent.joinpath('resources', 'ontology', 'spectro_ontology.ttl')


class SpectroConcepts(CustomExt):

    params = [
        {'title': 'Average:', 'name': 'average', 'type': 'int', 'value': 1, 'min': 1},
        {'title': 'Status:', 'name': 'status', 'type': 'str', 'value': 'Idle', 'readonly': True},
    ]

    def __init__(self, parent: gutils.DockArea, dashboard):
        super().__init__(parent, dashboard)
        self.ontology_manager = getattr(dashboard, 'extra_managers', {}).get('ontology')
        self._busy = False
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
        self.add_action('check', 'What can I compute?', 'help',
                        tip='Tell what the terms of the channels allow, without acquiring')
        self.add_action('grab', 'Grab and compute', 'camera', tip='Grab all the detectors, compute and show')

    def connect_things(self):
        self.connect_action('check', self.show_what_is_possible)
        self.connect_action('grab', self.grab_and_compute)
        self.modules_manager.timeout_signal.connect(self._on_timeout)

    def _load_spectro_ontology(self) -> None:
        from pymodaq_ontology.source_factory import SourceFactory
        self.ontology_manager.set_source(SourceFactory.create('rdf', str(TERMS_FILE)))

    # ---- the ontology side: terms of the channels
    def terms_of_detectors(self) -> dict[str, str]:
        """Term assigned to each channel of the detectors, by channel key"""
        manager = self.ontology_manager
        manager.update_channels_from_dashboard()
        return {c.key: manager.assignment.get(c.key) for c in manager.channels if c.kind == 'detector'
                and manager.assignment.get(c.key)}

    def _derivations(self) -> Optional[Derivations]:
        """The derivations declared by the ontology of the manager (read again if the source changed)"""
        graph = getattr(self.ontology_manager.source, 'graph', None)
        if graph is None:
            return None
        if self.derivations is None or self.derivations.graph is not graph:
            self.derivations = Derivations(graph, self.ontology_manager.hierarchy.is_a)
        return self.derivations

    def _label(self, iri: str) -> str:
        term = self.ontology_manager.terms.get(iri)
        return term.label if term else iri

    def show_what_is_possible(self) -> str:
        """Say what can be computed from the terms assigned to the channels (without acquiring). Returns the text"""
        if self.ontology_manager is None:
            text = 'pymodaq_ontology is not installed'
        else:
            derivations = self._derivations()
            assigned = self.terms_of_detectors()
            terms = {iri: None for iri in assigned.values()}
            if derivations is None:
                text = 'The ontology loaded in the manager has no graph: load an RDF ontology'
            else:
                text = self._describe(assigned, derivations.computable(terms), derivations.missing(terms))
        self.what.setPlainText(text)
        self.set_status(text.splitlines()[0] if text else 'Idle')
        return text

    def _describe(self, assigned: dict[str, str], computable: list[str], missing: dict[str, list[str]]) -> str:
        lines = []
        if computable:
            lines.append('Can compute: ' + ', '.join(self._label(i) for i in computable))
        else:
            lines.append('Nothing can be computed yet')
        for output, inputs in missing.items():
            lines.append(f'{self._label(output)} needs: ' + ', '.join(self._label(i) for i in inputs))
        lines.append('')
        lines.append('Channels with a term:')
        lines.extend(f'  {key}  ->  {self._label(iri)}' for key, iri in assigned.items())
        return '\n'.join(lines)

    # ---- acquisition
    def grab_and_compute(self):
        if self._busy or self.ontology_manager is None:
            return
        self.modules_manager.selected_detectors_name = self.modules_manager.detectors_name
        self._busy = True
        self.set_action_enabled('grab', False)
        self.set_status('Grabbing')
        self.modules_manager.grab_data_with_callback(callback=self._on_data)

    def _on_data(self, data: DataToExport):
        self.modules_manager.forget_callback(self._on_data, ModuleType.Detector)
        try:
            self.compute_and_show(data)
        finally:
            self._busy = False
            self.set_action_enabled('grab', True)

    def arrays_by_term(self, data: DataToExport) -> tuple[dict[str, np.ndarray], list[str], list]:
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

    def compute_and_show(self, data: DataToExport) -> None:
        derivations = self._derivations()
        if derivations is None:
            self.set_status('No RDF ontology loaded in the manager')
            return
        arrays, problems, axis = self.arrays_by_term(data)
        results = derivations.compute(arrays)
        computed = [DataCalculated(self._label(iri), data=[array], axes=[axis] if axis is not None else [],
                                   labels=[self._label(iri)]) for iri, array in results.items()]
        self.viewer.show_data(DataToExport('spectro', data=[*data, *computed]))
        lines = [self._describe(self.terms_of_detectors(), derivations.computable(arrays),
                                derivations.missing(arrays))]
        lines.extend(f'Unit: {p}' for p in problems)
        self.what.setPlainText('\n'.join(lines))
        self.set_status(lines[0].splitlines()[0])

    def _on_timeout(self, missing_modules: list):
        self.modules_manager.forget_callback(self._on_data, ModuleType.Control)
        self._busy = False
        self.set_action_enabled('grab', True)
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
