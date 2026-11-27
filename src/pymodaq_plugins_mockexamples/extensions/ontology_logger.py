"""Demo extension: a DAQ_Logger whose saved data carry the terms of an ontology

It shows how an extension works with the ``OntologyManager`` of the ``pymodaq_ontology`` package:

* the manager lives in the Dashboard (menu *Ontology*): the user assigns a term to each channel of the instruments
* the extension asks the manager to annotate the data saved by its worker (``attach_worker``): the ``semantic_iri``
  extra attribute is written with the data
* it gives the manager a small ontology of its own (``resources/ontology/basic_ontology.ttl``) if none was loaded yet
* the terms know what they are a kind of (``broader``): choose a concept, for instance *Optical signal*, and the
  action *Select the channels of the concept* selects the instruments with a channel whose term is that concept or
  a kind of it (a *Photodiode signal* is an *Optical signal*), whatever the instruments are called

Without ``pymodaq_ontology`` the extension is a plain logger and says so.
"""
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from pymodaq_utils.logger import set_logger, get_module_name

from pymodaq.extensions.daq_logger.daq_logger import DAQLogger
from pymodaq_gui.utils.dock import DockArea

if TYPE_CHECKING:
    from pymodaq.dashboard import DashBoard

logger = set_logger(get_module_name(__file__))

EXTENSION_NAME = 'Ontology Logger'  # displayed in the Extensions menu of the Dashboard
CLASS_NAME = 'OntologyLogger'  # the name of the class below

TERMS_FILE = Path(__file__).parent.parent.joinpath('resources', 'ontology', 'basic_ontology.ttl')


class OntologyLogger(DAQLogger):
    """A logger annotating what it saves with the terms assigned in the ontology manager of the Dashboard"""
    h5_base_group_name = 'OntologyLogger'
    params = DAQLogger.params + [
        {'title': 'Concept:', 'name': 'concept', 'type': 'list', 'limits': {}},  # label -> IRI, filled by the manager
    ]

    def __init__(self, dockarea: DockArea = None, dashboard: 'DashBoard' = None):
        super().__init__(dockarea, dashboard)
        self.ontology_manager = getattr(dashboard, 'extra_managers', {}).get('ontology')
        if self.ontology_manager is None:
            self.update_status('pymodaq_ontology is not installed: the data are saved without annotation')
            return
        if self.ontology_manager.source is None:
            self._load_basic_ontology()
        self._update_concepts()
        self.ontology_manager.attach_worker(self.logging)

    def setup_actions(self):
        super().setup_actions()
        self.add_action('select_concept', 'Select the channels of the concept', 'hub',
                        tip='Select the instruments with a channel whose term is the concept or a kind of it')

    def connect_things(self):
        super().connect_things()
        self.connect_action('select_concept', self.select_channels_of_concept)

    def _update_concepts(self) -> None:
        """The terms of the ontology that have kinds (the concepts), by label"""
        hierarchy = self.ontology_manager.hierarchy
        concepts = {term.label: iri for iri, term in hierarchy.terms.items() if hierarchy.children(iri)}
        self.settings.child('concept').setLimits(concepts)

    def select_channels_of_concept(self) -> str:
        """Select the instruments with a channel of the chosen concept. Returns what was done, as text"""
        manager = self.ontology_manager
        if manager is None or not self.settings['concept']:
            message = 'No concept to select'
        else:
            manager.update_channels_from_dashboard()
            manager.probe()  # the channels of the detectors are found by a snap
            channels = manager.channels_of_concept(self.settings['concept'])
            detectors = sorted({c.module for c in channels if c.kind == 'detector'})
            actuators = sorted({c.module for c in channels if c.kind == 'actuator'})
            self.modules_manager.selected_detectors_name = detectors
            self.modules_manager.selected_actuators_name = actuators
            label = manager.terms[self.settings['concept']].label
            message = f'{len(channels)} channels of "{label}": detectors {detectors}, actuators {actuators}'
        self.update_status(message)
        return message

    def _load_basic_ontology(self, path: Optional[Path] = None) -> None:
        from pymodaq_ontology.source_factory import SourceFactory
        self.ontology_manager.set_source(SourceFactory.create('rdf', str(path or TERMS_FILE)))

    def _quit_fun(self) -> bool:
        can_quit = super()._quit_fun()
        if can_quit and self.ontology_manager is not None:
            self.ontology_manager.detach_worker(self.logging)
        return can_quit


def main():
    """Run the extension on its own (the Dashboard stays hidden), see ``-x EXPERIMENT_NAME -s STATE_NAME``"""
    import sys
    from pymodaq_gui.qt_utils import mkQApp
    from pymodaq.dashboard import load_dashboard_with_arguments
    from pymodaq.utils.gui_utils.loader_utils import create_extension

    app = mkQApp('Ontology Logger')
    win, dashboard, _ = load_dashboard_with_arguments(show_dashboard=False, load_extension=False)
    win.mainwindow.setVisible(False)
    win_ext, ext = create_extension(dashboard, OntologyLogger, show_extension=True)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
