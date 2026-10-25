"""The .NET assembly recipe: starting the runtime, the ``pythonnet`` driver on the simulated assembly, the plugins on it

The first tests call the real .NET libraries of the runtime (.NET Framework on Windows, .NET 6+ elsewhere) and are
skipped if ``pythonnet`` or a runtime is missing. The others need neither. To test your own driver copy the last part
and replace the plugin classes.
"""
import threading
import time

import pytest

from pymodaq.utils.data import DataActuator
from pymodaq.utils.plugin_testing import (make_actuator, make_detector, move_abs_and_wait, move_rel_and_wait,
                                          move_home_and_wait, grab_and_wait)

from pymodaq_plugins_mockexamples.daq_move_plugins.daq_move_CookbookDotNet import DAQ_Move_CookbookDotNet
from pymodaq_plugins_mockexamples.daq_viewer_plugins.plugins_0D.daq_0Dviewer_CookbookDotNet import \
    DAQ_0DViewer_CookbookDotNet
from pymodaq_plugins_mockexamples.hardware import mock_dll_controller as mock
from pymodaq_plugins_mockexamples.hardware import system_dotnet_demo
from pymodaq_plugins_mockexamples.hardware.dll_controller import MotionControllerError
from pymodaq_plugins_mockexamples.hardware.dotnet_controller import MotionController, open_controller
from pymodaq_plugins_mockexamples.hardware.dotnet_runtime import (load_dotnet, load_assembly, DotNetNotAvailableError,
                                                                   AssemblyNotFoundError)
from pymodaq_plugins_mockexamples.hardware.mock_dotnet_controller import MockMmNamespace


@pytest.fixture(scope='module')
def runtime():
    """The .NET runtime, or skip the tests of the real .NET libraries if there is none on this machine"""
    try:
        return load_dotnet()
    except DotNetNotAvailableError as e:
        pytest.skip(str(e))


class TestSystemLibraries:
    """Real calls to the libraries of the runtime"""

    def test_out_parameter(self, runtime):
        assert system_dotnet_demo.parse_integer('42') == 42
        assert system_dotnet_demo.parse_integer('forty-two') is None

    def test_dotnet_exception(self, runtime):
        assert system_dotnet_demo.parse_integer_or_raise('7') == 7
        with pytest.raises(ValueError, match='not in a correct format'):
            system_dotnet_demo.parse_integer_or_raise('x')

    def test_generic_collection(self, runtime):
        assert system_dotnet_demo.sum_of_list([1., 2.5, 3.]) == pytest.approx(6.5)

    def test_typed_array_and_dispose(self, runtime):
        assert system_dotnet_demo.bytes_through_a_stream(b'\x00\x01\xffabc') == b'\x00\x01\xffabc'

    def test_event_raised_by_another_thread(self, runtime):
        thread = system_dotnet_demo.thread_of_the_event()
        assert thread is not threading.main_thread()

    def test_missing_assembly_says_what_was_tried(self, runtime, tmp_path):
        missing = tmp_path / 'Nowhere.dll'
        with pytest.raises(AssemblyNotFoundError) as exc:
            load_assembly(['Not.An.Assembly'], path=missing)
        assert str(missing) in str(exc.value)
        assert 'Not.An.Assembly' in str(exc.value)

    def test_second_candidate_is_used(self, runtime):
        assert load_assembly(['Not.An.Assembly', 'System.Collections']) is not None


def test_no_runtime_is_a_clear_error(monkeypatch):
    monkeypatch.setitem(__import__('sys').modules, 'pythonnet', None)  # import pythonnet fails
    with pytest.raises(DotNetNotAvailableError, match='pip install pythonnet'):
        load_dotnet()


class TestMockAssembly:
    def test_behaves_like_a_namespace_of_pythonnet(self):
        api = MockMmNamespace()
        controller = api.Controller.Open('MOCK')
        try:
            ok, position = controller.TryGetPosition(0)  # an out parameter comes back in a tuple
            assert ok and position == 0.
            with pytest.raises(api.MmException) as exc:
                api.Controller.Open('COM1')
            assert 'COM1' in exc.value.Message
        finally:
            controller.Dispose()

    def test_unknown_member(self):
        with pytest.raises(AttributeError):
            MockMmNamespace().Controller.Open('MOCK').DoesNotExist()


@pytest.fixture
def controller():
    ctl = MotionController.mock()
    yield ctl
    ctl.close()


class TestDriver:
    def test_info(self, controller):
        info = controller.info()
        assert info.name == 'MockMotion .NET'
        assert info.n_axes == 3
        assert info.firmware == (3, 1)

    def test_move_and_event_from_another_thread(self, controller):
        events = []
        controller.subscribe(lambda axis, event: events.append((axis, event, threading.current_thread())))
        controller.move_abs(1, 5.)
        deadline = time.monotonic() + 5
        while not events and time.monotonic() < deadline:
            time.sleep(0.01)
        assert events[0][:2] == (1, mock.EVENT_MOVE_DONE)
        assert events[0][2] is not threading.main_thread()
        assert controller.position(1) == pytest.approx(5.)

    def test_dotnet_exceptions_become_driver_errors(self, controller):
        with pytest.raises(MotionControllerError, match='out of range'):
            controller.move_abs(0, 500.)
        with pytest.raises(MotionControllerError, match='Invalid axis'):
            controller.move_abs(7, 1.)

    def test_stop_reports_a_stopped_event(self):
        ctl = MotionController(MockMmNamespace())
        events = []
        ctl.subscribe(lambda axis, event: events.append(event))
        try:
            ctl.move_abs(0, 40.)
            ctl.stop(0)
            assert events == [mock.EVENT_STOPPED]
            assert not ctl.is_moving(0)
        finally:
            ctl.close()

    def test_closed_controller_is_refused(self):
        ctl = MotionController.mock()
        ctl.close()
        ctl.close()  # closing twice is harmless
        with pytest.raises(MotionControllerError, match='closed'):
            ctl.position(0)

    def test_close_removes_the_handler(self):
        ctl = MotionController.mock()
        event = ctl._controller.MoveFinished
        assert len(event._handlers) == 1
        ctl.close()
        assert event._handlers == []

    def test_open_controller_without_the_assembly(self, runtime, tmp_path):
        with pytest.raises(AssemblyNotFoundError):
            open_controller('COM1', str(tmp_path / 'Mm.Net.dll'))


@pytest.fixture
def actuator(qapp):
    plugin = make_actuator(DAQ_Move_CookbookDotNet)
    assert plugin.initialized
    yield plugin
    plugin.close()


class TestPlugins:
    def test_ini_returns_the_identity(self, actuator):
        assert 'MockMotion .NET' in actuator.init_info

    def test_move_abs_waits_for_the_event(self, actuator):
        position = move_abs_and_wait(actuator, 5.)
        assert position.value('mm') == pytest.approx(5., abs=0.01)
        assert actuator._move_finished

    def test_move_rel(self, actuator):
        move_abs_and_wait(actuator, 1.)
        assert move_rel_and_wait(actuator, 0.5).value('mm') == pytest.approx(1.5, abs=0.01)

    def test_move_home_ends_with_the_event(self, actuator):
        move_abs_and_wait(actuator, 3.)
        assert move_home_and_wait(actuator).value('mm') == pytest.approx(0., abs=0.01)

    def test_out_of_range_is_an_error_of_the_driver(self, actuator):
        with pytest.raises(MotionControllerError):
            actuator.move_abs(DataActuator(data=500., units='mm'))

    def test_axes_share_the_controller(self, actuator):
        slave = make_actuator(DAQ_Move_CookbookDotNet, controller=actuator.controller)
        try:
            slave.settings.child('controller', 'axis').setValue(1)
            assert slave.controller is actuator.controller
            move_abs_and_wait(actuator, 4.)
            move_abs_and_wait(slave, -2.)
            assert actuator.get_actuator_value().value('mm') == pytest.approx(4., abs=0.01)
            assert slave.get_actuator_value().value('mm') == pytest.approx(-2., abs=0.01)
        finally:
            slave.close()  # a slave never closes the shared controller
        assert actuator.get_actuator_value().value('mm') == pytest.approx(4., abs=0.01)

    def test_detector_shares_the_controller(self, actuator):
        detector = make_detector(DAQ_0DViewer_CookbookDotNet, controller=actuator.controller)
        try:
            move_abs_and_wait(actuator, 2.)
            dte = grab_and_wait(detector)
            assert [float(array[0]) for array in dte[0].data] == pytest.approx([2., 0., 0.], abs=0.01)
            assert dte[0].labels == ['X', 'Y', 'Z']
        finally:
            detector.close()

    def test_detector_alone_is_a_master(self, qapp):
        detector = make_detector(DAQ_0DViewer_CookbookDotNet)
        try:
            assert grab_and_wait(detector)[0].shape == (1,)
        finally:
            detector.close()
