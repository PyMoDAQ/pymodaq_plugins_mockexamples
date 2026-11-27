"""Demo extension: a DAQ_Logger whose saved data carry the terms of an ontology

It shows how an extension works with the ``OntologyManager`` of the ``pymodaq_ontology`` package:

* the manager lives in the Dashboard (menu *Ontology*): the user assigns a term to each channel of the instruments
* the extension asks the manager to annotate the data saved by its worker (``attach_worker``): the ``semantic_iri``
  extra attribute is written with the data
* it gives the manager a small ontology of its own (``resources/ontology/basic_terms.toml``) if none was loaded yet

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

TERMS_FILE = Path(__file__).parent.parent.joinpath('resources', 'ontology', 'basic_terms.toml')


class OntologyLogger(DAQLogger):
    """A logger annotating what it saves with the terms assigned in the ontology manager of the Dashboard"""
    h5_base_group_name = 'OntologyLogger'

    def __init__(self, dockarea: DockArea = None, dashboard: 'DashBoard' = None):
        super().__init__(dockarea, dashboard)
        self.ontology_manager = getattr(dashboard, 'extra_managers', {}).get('ontology')
        if self.ontology_manager is None:
            self.update_status('pymodaq_ontology is not installed: the data are saved without annotation')
            return
        if self.ontology_manager.source is None:
            self._load_basic_terms()
        self.ontology_manager.attach_worker(self.logging)

    def _load_basic_terms(self, path: Optional[Path] = None) -> None:
        from pymodaq_ontology.source_factory import SourceFactory
        self.ontology_manager.set_source(SourceFactory.create('terms', str(path or TERMS_FILE)))

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
