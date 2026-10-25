"""The DLL / SDK recipe: loading a native library, the ctypes driver on the simulated library, the plugins on it

The first tests call the real C library of the system (``libc``, ``libm``, ``ucrtbase``). To test your own driver copy
the last part and replace the plugin classes.
"""
import ctypes
import threading
import time

import pytest

from pymodaq.utils.data import DataActuator
from pymodaq.utils.plugin_testing import (make_actuator, make_detector, move_abs_and_wait, move_rel_and_wait,
                                          move_home_and_wait, grab_and_wait)

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_CookbookDll import DAQ_Move_CookbookDll
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_0D.daq_0Dviewer_CookbookDll import \
    DAQ_0DViewer_CookbookDll
from pymodaq_plugins_mockexamples.hardware import mock_dll_controller as mock
from pymodaq_plugins_mockexamples.hardware import system_library_demo
from pymodaq_plugins_mockexamples.hardware.dll_controller import (MotionController, MotionControllerError,
                                                                  open_controller)
from pymodaq_plugins_mockexamples.hardware.native_library import (load_library, LibraryNotFoundError,
                                                                  candidate_names)


class TestLoadLibrary:
    def test_candidate_names(self):
        assert candidate_names('a') == ['a']
        assert candidate_names(['a', 'b']) == ['a', 'b']
        assert candidate_names({'Linux': ['x'], 'Windows': ['y']}, 'Windows') == ['y']
        assert candidate_names({'Linux': ['x']}, 'Darwin') == []

    def test_loads_the_system_library(self):
        assert load_library(system_library_demo.C_LIBRARY) is not None

    def test_a_wrong_path_falls_back_to_the_names(self, tmp_path):
        assert load_library(system_library_demo.C_LIBRARY, path=tmp_path / 'nothing.dll') is not None

    def test_environment_variable(self, monkeypatch, tmp_path):
        missing = str(tmp_path / 'does_not_exist.dll')  # paths are written in the native form of the system
        monkeypatch.setenv('MY_LIBRARY', missing)
        with pytest.raises(LibraryNotFoundError) as e:
            load_library('no_such_library_for_the_tests', env_var='MY_LIBRARY')
        assert missing in str(e.value) and 'MY_LIBRARY' in str(e.value)

    def test_missing_library_says_what_was_tried(self, tmp_path):
        folder = str(tmp_path / 'somewhere')
        with pytest.raises(LibraryNotFoundError) as e:
            load_library({'Linux': ['libmissing.so'], 'Darwin': ['libmissing.dylib'], 'Windows': ['missing.dll']},
                         path=folder)
        message = str(e.value)
        assert 'Tried' in message and 'missing' in message and folder in message
        assert isinstance(e.value, OSError)

    def test_unknown_convention(self):
        with pytest.raises(ValueError):
            load_library('c', convention='pascal')


class TestSystemLibrary:
    """Real calls into native code: the techniques of any ctypes driver"""

    def test_argtypes_and_restype(self):
        assert system_library_demo.string_length('PyMoDAQ') == 7

    def test_output_parameter(self):
        mantissa, exponent = system_library_demo.split_mantissa_exponent(48.)
        assert (mantissa, exponent) == (0.75, 6)

    def test_callback_called_by_the_library(self):
        calls = []

        def compare(a, b):
            calls.append((a, b))
            return (a > b) - (a < b)

        assert system_library_demo.sort_with_callback([3., -1., 2., 0.], compare) == [-1., 0., 2., 3.]
        assert calls


class TestMockLibrary:
    @pytest.fixture
    def library(self):
        return mock.MockMotionLibrary(speed=1000.)

    def test_behaves_like_a_cdll(self, library):
        handle = ctypes.c_void_p()
        library.mm_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        assert library.mm_open(b'MOCK', ctypes.byref(handle)) == mock.MM_OK
        assert handle.value
        with pytest.raises(AttributeError):
            library.not_a_function

    def test_wrong_number_of_arguments(self, library):
        library.mm_close.argtypes = [ctypes.c_void_p]
        with pytest.raises(TypeError):
            library.mm_close()

    def test_unknown_port(self):
        with pytest.raises(MotionControllerError, match='no controller on this port'):
            MotionController(mock.MockMotionLibrary(), 'COM99')


@pytest.fixture
def controller():
    controller = MotionController.mock(speed=1000.)
    yield controller
    controller.close()


class TestDriver:
    def test_info_structure(self, controller):
        info = controller.info()
        assert (info.name, info.n_axes, info.firmware) == ('MockMotion 3000', 3, (2, 7))

    def test_move_and_callback_from_another_thread(self, controller):
        events = []
        controller.subscribe(lambda axis, event: events.append((axis, event, threading.get_ident())))
        controller.move_abs(2, 10.)
        deadline = time.monotonic() + 2
        while not events and time.monotonic() < deadline:
            time.sleep(0.005)
        assert events[0][:2] == (2, mock.EVENT_MOVE_DONE)
        assert events[0][2] != threading.get_ident()  # the callback comes from a thread of the library
        assert controller.position(2) == pytest.approx(10.)
        assert not controller.is_moving(2)

    def test_error_codes_become_exceptions(self, controller):
        with pytest.raises(MotionControllerError, match='position out of range'):
            controller.move_abs(0, 500.)
        with pytest.raises(MotionControllerError, match='invalid axis'):
            controller.move_abs(5, 1.)

    def test_stop_reports_a_stopped_event(self):
        controller = MotionController.mock(speed=1.)
        events = []
        controller.subscribe(lambda axis, event: events.append(event))
        try:
            controller.move_abs(0, 40.)
            time.sleep(0.05)
            controller.stop(0)
            assert events == [mock.EVENT_STOPPED]
            assert 0. < controller.position(0) < 40.
        finally:
            controller.close()

    def test_closed_handle_is_refused(self):
        controller = MotionController.mock()
        library, handle = controller._lib, controller._handle
        controller.close()
        library.mm_get_position.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        assert library.mm_get_position(handle, 0, ctypes.byref(ctypes.c_double())) == mock.MM_ERR_HANDLE

    def test_open_controller_without_the_library(self):
        with pytest.raises(LibraryNotFoundError):
            open_controller('COM3', library_path='')


@pytest.fixture
def actuator(qapp):
    plugin = make_actuator(DAQ_Move_CookbookDll)
    assert plugin.initialized
    yield plugin
    plugin.close()


class TestPlugins:
    def test_ini_returns_the_identity(self, actuator):
        assert 'MockMotion 3000' in actuator.init_info

    def test_move_abs_waits_for_the_callback(self, actuator):
        position = move_abs_and_wait(actuator, 5.)
        assert position.value('mm') == pytest.approx(5., abs=0.01)
        assert actuator._move_finished

    def test_move_rel(self, actuator):
        move_abs_and_wait(actuator, 1.)
        assert move_rel_and_wait(actuator, 0.5).value('mm') == pytest.approx(1.5, abs=0.01)

    def test_move_home_ends_with_the_callback(self, actuator):
        move_abs_and_wait(actuator, 3.)
        assert move_home_and_wait(actuator).value('mm') == pytest.approx(0., abs=0.01)

    def test_out_of_range_is_an_error_of_the_driver(self, actuator):
        with pytest.raises(MotionControllerError):
            actuator.move_abs(DataActuator(data=500., units='mm'))

    def test_axes_share_the_controller(self, actuator):
        slave = make_actuator(DAQ_Move_CookbookDll, controller=actuator.controller)
        try:
            slave.settings.child('controller', 'axis').setValue(1)  # the axis Y, number 1 for the library
            assert slave.controller is actuator.controller
            move_abs_and_wait(actuator, 4.)
            move_abs_and_wait(slave, -2.)
            assert actuator.get_actuator_value().value('mm') == pytest.approx(4., abs=0.01)
            assert slave.get_actuator_value().value('mm') == pytest.approx(-2., abs=0.01)
        finally:
            slave.close()  # a slave never closes the shared controller
        assert actuator.get_actuator_value().value('mm') == pytest.approx(4., abs=0.01)

    def test_events_of_the_other_axes_are_ignored(self, actuator):
        slave = make_actuator(DAQ_Move_CookbookDll, controller=actuator.controller)
        try:
            slave.settings.child('controller', 'axis').setValue(1)
            actuator._move_finished = False  # waiting for its own end of move
            move_abs_and_wait(slave, 1.)
            assert not actuator._move_finished
        finally:
            slave.close()

    def test_detector_shares_the_controller(self, actuator):
        detector = make_detector(DAQ_0DViewer_CookbookDll, controller=actuator.controller)
        try:
            move_abs_and_wait(actuator, 2.)
            dte = grab_and_wait(detector)
            assert [float(array[0]) for array in dte[0].data] == pytest.approx([2., 0., 0.], abs=0.01)
            assert dte[0].labels == ['X', 'Y', 'Z']
        finally:
            detector.close()
        assert actuator.get_actuator_value().value('mm') == pytest.approx(2., abs=0.01)

    def test_detector_alone_is_a_master(self, qapp):
        detector = make_detector(DAQ_0DViewer_CookbookDll)
        try:
            assert grab_and_wait(detector)[0].shape == (1,)
        finally:
            detector.close()
