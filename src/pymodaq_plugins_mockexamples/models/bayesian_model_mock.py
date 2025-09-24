import numpy as np
from qtpy.QtWidgets import QWidget, QApplication
from typing import List

from pymodaq_gui.parameter import Parameter
from pymodaq.extensions.optimizers_base.utils import OptimizerModelDefault
from pymodaq_gui import utils as gutils
from pymodaq_gui.plotting.data_viewers import Viewer1D, Viewer2D
from pymodaq.utils.data import DataActuator, DataToActuators, DataRaw


class BayesianModelMock(OptimizerModelDefault):
    params = OptimizerModelDefault.params + [
        {'title': 'Update data', 'name': 'update_data', 'type': 'bool_push', 'label': 'Update Data'}
    ]

    def ini_model(self):
        self._mock_dwa: DataRaw = None

    def runner_initialized(self):
        """ To be subclassed

        Initialize whatever is needed by your custom model after the optimization runner is
        initialized
        """
        if 'Mock Data' not in self.optimization_controller.dockarea.docks:
            dock_mock = gutils.Dock('Mock Data')
            dock_widget = QWidget()
            dock_mock.addWidget(dock_widget)
            self.optimization_controller.dockarea.addDock(
                dock_mock, 'bottom',
                self.optimization_controller.dockarea.docks[
                    self.optimization_controller.explored_viewer_name])


            controller = self.modules_manager.get_mod_from_name('ComplexData').controller
            self._mock_dwa = controller.get_data_grid()
            if controller.signal_type == 'Lorentzian':
                self.viewer_mock = Viewer1D(dock_widget)
                self.viewer_mock.get_action('errors').trigger()
            else:
                self.viewer_mock = Viewer2D(dock_widget)

            self.viewer_mock.show_data(self._mock_dwa)
            self.viewer_mock.get_action('crosshair').trigger()

            if isinstance(self.viewer_mock, Viewer2D):
                self.viewer_mock.view.collapse_lineout_widgets()

            QApplication.processEvents()
            container = dock_mock.container()
            container.setSizes((int(container.height()/2),
                                int(container.height()/2)))

    def update_settings(self, param: Parameter):
        super().update_settings(param)
        if param.name() == 'update_data':
            controller = self.modules_manager.get_mod_from_name('ComplexData').controller
            dwa = controller.get_data_grid()
            self._mock_dwa = self.viewer_mock.show_data(dwa)

    def convert_output(self, outputs: List[np.ndarray], best_individual=None) -> DataToActuators:
        """ Convert the output of the Optimisation Controller in units to be fed into the actuators
        Parameters
        ----------
        outputs: list of numpy ndarray
            output value from the controller from which the model extract a value of the same units
            as the actuators
        best_individual: np.ndarray
            the coordinates of the best individual so far

        Returns
        -------
        DataToActuators: derived from DataToExport. Contains value to be fed to the actuators
        with a mode            attribute, either 'rel' for relative or 'abs' for absolute.

        """

        return DataToActuators('outputs', mode='abs',
                               data=[DataActuator(self.modules_manager.actuators_name[ind],
                                                  data=float(outputs[ind])) for ind in
                                     range(len(outputs))])

    def update_plots(self):
        """ Called when updating the live plots """
        # best
        # try:
        #     if best_individual is not None:
        #         pos_list = [float(coord) for coord in best_individual]
        #         if isinstance(self.viewer_mock, Viewer2D):
        #             pos_list = self.viewer_mock.view.unscale_axis(*list(pos_list))
        #             pos_list = list(pos_list)
        #         else:
        try:

            if isinstance(self.viewer_mock, Viewer1D):
                axis_grid = self._mock_dwa.axes
                axis_array = axis_grid[0].get_data()
                actuators = self.modules_manager.selected_actuators_name
                dwa_measured, dwa_prediction = (
                    self.optimization_controller.algorithm.get_1D_dwa_gp(
                        axis_grid[0].get_data(), actuator_name=actuators[0]))
                dwa_measured.extra_attributes += ['symbol', 'symbol_size', 'color']
                dwa_measured.symbol = 'd'
                dwa_measured.symbol_size = 10
                dwa_measured.color = 'b'
                mock = DataRaw('Predict', data=[self._mock_dwa.data[0].copy(),
                                                dwa_prediction.data[0].copy()],
                               labels=['Target', 'Prediction'],
                               errors=[np.zeros((len(axis_array))),
                                       dwa_prediction.errors[0]],
                               axes=[axis_grid[0].copy()])
                self.viewer_mock.show_data(mock,
                                           scatter_dwa=dwa_measured)
            best_indiv_array = self.optimization_controller.algorithm.best_individual
            if isinstance(self.viewer_mock, Viewer2D):
                best_indiv_array = self.viewer_mock.view.unscale_axis(*best_indiv_array)
            self.viewer_mock.set_crosshair_position(*best_indiv_array)

        except Exception as e:
            pass