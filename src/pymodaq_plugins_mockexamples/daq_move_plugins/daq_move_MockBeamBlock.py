"""Ontology demo: the beam block of a simulated absorption bench (1 blocks the beam, 0 lets it through)

The beam block, the cuvette holder (``MockSampleChanger``) and the spectrometer (``MockSpectro``) share one simulated
bench (see ``hardware/spectro_bench.py``): all are masters, nothing to link in the experiment.
"""
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType
from pymodaq.utils.data import DataActuator

from pymodaq_plugins_mockexamples.hardware.spectro_bench import SpectroBench


class DAQ_Move_MockBeamBlock(DAQ_Move_base):
    """Sets ``beam_block`` of the bench"""
    _controller_units = ''
    is_multiaxes = True
    _axis_names = ['Block']
    _epsilons = 0.01
    attribute = 'beam_block'  # of the bench, set by this plugin

    params = [] + comon_parameters_fun(axis_names=_axis_names, epsilon=_epsilons)
    data_actuator_type = DataActuatorType.DataActuator

    def ini_attributes(self):
        self.controller: SpectroBench = None

    def get_actuator_value(self) -> DataActuator:
        pos = DataActuator(self._title, data=float(getattr(self.controller, self.attribute)), units=self.axis_unit)
        return self.get_position_with_scaling(pos)

    def close(self):
        pass

    def commit_settings(self, param):
        pass

    def ini_stage(self, controller: SpectroBench = None):
        self.controller = SpectroBench.shared()
        return 'Simulated absorption bench initialized', True

    def move_abs(self, position: DataActuator):
        position = self.check_bound(position)
        self.target_value = position
        setattr(self.controller, self.attribute, float(self.target_value.value(self.axis_unit)))

    def move_rel(self, position: DataActuator):
        position = self.check_bound(self.current_value + position) - self.current_value
        self.target_value = position + self.current_value
        setattr(self.controller, self.attribute, float(self.target_value.value(self.axis_unit)))

    def stop_motion(self):
        self.move_done()


if __name__ == '__main__':
    main(__file__)
