# -*- coding: utf-8 -*-
"""
Created the 04/11/2023

@author: Sebastien Weber
"""


from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_MockNamedAxes import DAQ_Move_MockNamedAxes

import pytest
from pytest import fixture, approx


@fixture
def init_qt(qtbot):
    return qtbot


def test_stage_names(init_qt):
    qtbot = init_qt
    axis_names = DAQ_Move_MockNamedAxes._axis_names.copy()
    prog = DAQ_Move_MockNamedAxes()

    prog.ini_stage()
    assert axis_names == prog.axis_names
    name_axis = 'anotheraxis'
    index_axis = 45
    axis_names.update({name_axis: index_axis})

    prog.axis_names = axis_names
    assert prog.axis_names == axis_names
    # units and epsilons are defined per axis: they must follow the new axis names
    prog.axis_units = ''
    prog.epsilons = prog.epsilon
    # the (mock) controller must know the new axis, the position is read when the axis changes
    prog.controller.axes_indexes = [*prog.controller.axes_indexes, index_axis]
    prog.controller._current_value = [*prog.controller._current_value, 0.]

    assert name_axis in prog.axis_names
    prog.axis_name = name_axis
    assert name_axis == prog.axis_name
    assert prog.settings.child('controller', 'axis').value() == index_axis
    assert prog.axis_value == index_axis
