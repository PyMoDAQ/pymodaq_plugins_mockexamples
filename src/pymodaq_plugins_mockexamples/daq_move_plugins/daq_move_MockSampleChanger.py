"""Ontology demo: the cuvette holder of a simulated absorption bench (0 the blank cuvette, 1 the sample), see
``MockBeamBlock``"""
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun, main, DataActuatorType

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_MockBeamBlock import DAQ_Move_MockBeamBlock


class DAQ_Move_MockSampleChanger(DAQ_Move_MockBeamBlock):
    """Sets ``sample_position`` of the bench"""
    _axis_names = ['Holder']
    attribute = 'sample_position'

    params = [] + comon_parameters_fun(axis_names=_axis_names, epsilon=DAQ_Move_MockBeamBlock._epsilons)
    data_actuator_type = DataActuatorType.DataActuator


if __name__ == '__main__':
    main(__file__)
