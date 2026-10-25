pymodaq_plugins_mockexamples
############################

.. the following must be adapted to your developed package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_mockexamples.svg
   :target: https://pypi.org/project/pymodaq_plugins_mockexamples/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_mockexamples/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_mockexamples
   :alt: Publication Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_mockexamples/actions/workflows/Test.yml/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_mockexamples/actions/workflows/Test.yml


This PyMoDAQ plugin adds various Mock instruments to test PyMoDAQ functionalities

Authors
=======

* Sebastien J. Weber  (sebastien.weber@cnrs.fr)


Instruments
===========

Below is the list of the instruments included in this plugin: what each one *simulates*, then what it shows of
PyMoDAQ. The link in brackets leads to the simulated setup it belongs to, described in "Simulated setups"
with the instruments to use together and the experiment files to load.

.. Keep every instrument on one short line starting with an asterisk and a bold name: the plugin manager of
   PyMoDAQ lists only that first line, and looks for the five titles below.

Actuators
+++++++++

* **BSPiezoMirror** (`beam steering`_): simulates a piezo mirror (X and Y tilt); shows a controller shared with four other modules.
* **BSPowerMeter** (`beam steering`_): simulates the power (W) of the steered beam; shows an axis of the shared beam steering controller.
* **MockCamera** (`mock camera`_): simulates X, Y and Theta axes moving a camera image; shows axes sharing a controller with a detector.
* **MockHeater** (`heater`_): simulates a heating power (W); shows a closed loop for the PID extension.
* **MockTempController** (`temperature controller`_): simulates a temperature controller (Temperature and Power axes); shows a master actuator with a slave detector.
* **MockRandom** (`gaussian scan`_): simulates the position of a noisy Gaussian; shows an actuator and detectors sharing a controller ID.
* **Harmonics** (`harmonics`_): simulates the power (W) of a harmonics source; shows units from pint quantities.
* **MockComplexSignal** (`complex signal`_): simulates X and Y axes over a 2D signal; shows axes given as a name to ID dictionary.
* **MockNamedAxes** (`actuator interfaces`_): simulates a three-axis controller; shows axes with a name and an integer ID.
* **MockBinary** (`actuator interfaces`_): simulates a two-state device (0 or 1); shows the binary actuator interface.
* **MockRelative** (`actuator interfaces`_): simulates a stage moved relatively only; shows the relative actuator interface.
* **BSPiezoMirrorRunTimeError** (`error tests`_): simulates the piezo mirror failing when read; shows how an error in get_actuator_value is handled.
* **BSPiezoMirrorTimeout** (`error tests`_): simulates the piezo mirror timing out at initialization; shows how an initialization timeout is handled.
* **BSPiezoMirrorUninitializing** (`error tests`_): simulates the piezo mirror failing at initialization; shows how a failed initialization is handled.

Viewer0D
++++++++

* **BSPhotodiode** (`beam steering`_): simulates a photodiode on the steered beam; shows a 0D detector on a shared controller.
* **MockHeater** (`heater`_): simulates the temperature of a heated object; shows a detector in a closed loop.
* **MockTempController** (`temperature controller`_): simulates the temperature and power of the controller; shows a slave detector receiving its controller.
* **MockRandom** (`gaussian scan`_): simulates a noisy Gaussian read at the actuator position; shows a detector coupled to an actuator by ID.
* **Harmonics** (`harmonics`_): simulates the power of the harmonics source; shows data with pint units.
* **MockComplexSignal** (`complex signal`_): simulates a signal read at the actuators position; shows scans in one or two dimensions.
* **MockAdaptive** (`complex signal`_): simulates a signal at requested positions; shows the positions argument of an adaptive scan.
* **MockErrors** (`error tests`_): simulates a 0D value with its standard deviation; shows data with errors from hardware averaging.

Viewer1D
++++++++

* **MockRandom** (`gaussian scan`_): simulates a shuffled Gaussian; shows the sort button of the 1D viewer.
* **Harmonics** (`harmonics`_): simulates the harmonics spectrum of the source; shows pint units and roi_select.
* **Mock_spectro** (`spectrometer`_): simulates a spectrometer with laser line and exposure; shows a calibrated wavelength axis (nm).
* **MockSpectroErrors** (`error tests`_): simulates the spectrometer averaged over 10 acquisitions; shows data with errors from averaging.

Viewer2D
++++++++

* **BSCamera** (`beam steering`_): simulates a camera imaging a laser spot; shows a live acquisition on a shared controller.
* **MockCamera** (`mock camera`_): simulates a camera generating various images; shows live mode, several data, X, Y and Theta actuators.
* **RoiStuff** (`mock camera`_): simulates the mock camera cropped to a ROI; shows roi_select receiving the ROI from the viewer.

ViewerND
++++++++

* **MockEvents** (`photon events`_): simulates a photon counting camera replaying a recording; shows N-dimensional data from an acquisition thread.

Simulated setups
================

The instruments above grouped by what they simulate (the links of the lists lead to the rows of this table).
Instruments of a setup that share a controller must have the same *controller ID* in the Dashboard. The
experiment files (``resources/*.xml``) are to be copied in the ``.pymodaq/experiments`` folder, they load in the
Dashboard of PyMoDAQ 5.3.

.. list-table::
   :header-rows: 1
   :widths: 22 33 17 28

   * - Setup
     - Instruments
     - Experiment file
     - What it shows
   * - .. _beam steering:

       **Beam steering with a piezo mirror**

     - actuators *BSPiezoMirror*, *BSPowerMeter*; 0D *BSPhotodiode*; 2D *BSCamera*
     - ``beam_steering_piezo.xml``
     - One controller shared by five modules, moves that take time, a 2D and a 0D detector on the same beam
   * - .. _mock camera:

       **Beam steering on a camera image**

     - actuators *MockCamera*; 2D *MockCamera*, *RoiStuff*
     - ``beam_steering.xml``
     - Axes moving a camera image, live acquisition, ROI selection; the PID model *PIDModelBeamSteering* uses its Xpiezo, Ypiezo and Camera
   * - .. _heater:

       **Heater and PID**

     - actuators *MockHeater*; 0D *MockHeater*
     - ``Heater.xml``
     - A closed loop for the PID extension
   * - .. _temperature controller:

       **Temperature controller with a PID loop**

     - actuators *MockTempController*; 0D *MockTempController*
     - ``TempController.xml``
     - A master actuator and a slave detector on one controller
   * - .. _gaussian scan:

       **Scanning a known signal**

     - actuators *MockRandom*; 0D *MockRandom*; 1D *MockRandom*
     - none
     - Scans of a noisy Gaussian, the sort button of the 1D viewer
   * - .. _harmonics:

       **Harmonics source**

     - actuators *Harmonics*; 0D *Harmonics*; 1D *Harmonics*
     - none
     - Physical units from ``pint`` quantities
   * - .. _complex signal:

       **Complex signal and adaptive scan**

     - actuators *MockComplexSignal*; 0D *MockComplexSignal*, *MockAdaptive*
     - none
     - Scans in one or two dimensions, the ``positions`` argument of an adaptive scan
   * - .. _spectrometer:

       **Spectrometer with a calibrated axis**

     - 1D *Mock_spectro*
     - none
     - A wavelength axis that follows a setting, data with errors
   * - .. _actuator interfaces:

       **Multi-axis and user interface examples**

     - actuators *MockNamedAxes*, *MockBinary*, *MockRelative*
     - none
     - Named axes on one controller, binary and relative user interfaces
   * - .. _photon events:

       **Photon counting camera**

     - ND *MockEvents*
     - none
     - N-dimensional data, an acquisition thread with Qt callbacks, temporary data
   * - .. _error tests:

       **Error handling**

     - actuators *BSPiezoMirrorRunTimeError*, *BSPiezoMirrorTimeout*, *BSPiezoMirrorUninitializing*; 0D *MockErrors*; 1D *MockSpectroErrors*
     - none
     - Errors on reading and on initialization, data carrying errors

Cookbook of device patterns
===========================

Short, runnable and tested plugins to copy from when writing a plugin for a real instrument. Each recipe is a pair
(actuator and 0D detector) that runs without hardware: leave the port or the address to ``MOCK`` and the plugin talks
to a simulated stage with a voltmeter (``hardware/fake_instrument.py``). Each file starts with a header telling what to
copy, what to adapt and what to keep. The tests (``tests/test_cookbook_drivers.py``, ``tests/test_cookbook_plugins.py``)
show how to test a plugin against a simulated device with the harness of ``pymodaq.utils.plugin_testing``.

Giving the same *controller ID* to an actuator and a detector of a recipe makes them share one driver: the first
initialized is the master and creates it, the other is the slave and receives it.

======================================  ==============================================  ================================================================
Pattern                                 Files                                           What it shows
======================================  ==============================================  ================================================================
Text protocol, ``pymeasure`` driver     ``daq_move_CookbookPymeasure``,                 The recommended way: a few declarative lines (``control``,
(recommended)                           ``daq_0Dviewer_CookbookPymeasure``,             ``measurement``, validators, error checking) in
                                        ``hardware/pymeasure_source.py``                ``hardware/pymeasure_source.py``, tested with ``ProtocolAdapter``
                                                                                        (exact commands) and with a simulated device
Serial line (RS-232, USB-serial),       ``daq_move_CookbookSerial``,                    A driver written on ``pyserial``: terminations, timeouts treated
driver written directly                 ``daq_0Dviewer_CookbookSerial``,                as errors, one lock for the shared driver, the error queue of the
                                        ``hardware/serial_stage.py``                    device, a blocking homing ended by ``move_done``
VISA / SCPI, driver written directly    ``daq_move_CookbookVisa``,                      The same on a ``pyvisa`` resource: explicit terminations and
                                        ``daq_0Dviewer_CookbookVisa``,                  timeout, ``query`` versus ``write``
                                        ``hardware/visa_meter.py``
======================================  ==============================================  ================================================================

Patterns already shown by the mock instruments of this package
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

======================================  ==============================================  ================================================================
Pattern                                 Plugins                                         What they show
======================================  ==============================================  ================================================================
Several axes on one controller          ``MockNamedAxes`` (actuator)                    The master axis creates the controller, the others receive it.
                                                                                        Axes have a name and an integer identifier
Actuator and detector on the same       ``MockTempController`` (actuator and 0D         A temperature controller with a PID loop: the actuator is
controller                              detector)                                       the master, the detector is its slave
2D camera                               ``MockCamera``, ``BSCamera`` (2D                Pixel axes, live acquisition, ROI selection done on the
                                        detectors), ``RoiStuff``                        viewer (``roi_select`` with ``RoiInfo``). Not shown: binning
                                                                                        and exposure time of a camera
1D spectrometer with a calibrated axis  ``Mock_spectro`` (1D detector)                  A wavelength axis in nm that follows the laser line setting,
                                                                                        and an exposure time that scales the signal
Simulated device, no hardware           every plugin of this package                    A pure python controller behind a small wrapper class in
                                                                                        ``hardware/``: the plugins run on it, no hardware needed
======================================  ==============================================  ================================================================

Patterns not yet covered: an instrument driven by a vendor DLL or SDK (``ctypes`` or a Python binding).


PID Models
==========


Extensions
==========

* **Move and Grab** (*extensions/move_and_grab.py*): the smallest useful Dashboard extension, to start from when
  writing yours. It moves an actuator of the Dashboard's experiment to a target, grabs a detector, shows the data and can
  save them. It shows how to use the ``modules_manager``, how to wait for the instruments with callbacks instead of
  blocking the GUI, units on the positions and a clean shutdown. It works with the mock instruments of PyMoDAQ. See
  "How a Dashboard extension works" in the PyMoDAQ documentation.


Installation instructions
=========================

* PyMoDAQ >= 5 (except for some of them, specified in this README)
* nothing in particular to be installed, they are all virtual instruments
