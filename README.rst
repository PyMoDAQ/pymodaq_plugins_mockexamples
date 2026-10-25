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

Below is the list of the instruments included in this plugin. Each one is described the same way: what it
*simulates*, then what it *highlights* of PyMoDAQ. The tag in brackets names the simulated setup it belongs to (see
"Simulated setups" below, which groups the instruments to use together).

.. Keep every instrument on one line starting with an asterisk and a bold name: the plugin manager of PyMoDAQ
   lists only that first line, and looks for the five titles below.

Actuators
+++++++++

* **BSPiezoMirror** [beam steering]: *simulates* the X and Y tilt axes of a piezo mirror steering a laser beam, with a response time set by the *Tau* setting; *highlights* a multi-axis actuator sharing one controller with the power meter, camera and photodiode of the same name family (same controller ID), and a move that takes time.
* **BSPowerMeter** [beam steering]: *simulates* the power (W) of the steered beam, set through an actuator axis; *highlights* an actuator on the *Power* axis of the shared beam steering controller.
* **MockCamera** [mock camera]: *simulates* the X, Y and Theta axes moving the image of the *MockCamera* 2D detector; *highlights* a multi-axis actuator sharing its controller with a detector.
* **MockHeater** [heater]: *simulates* the heating power (W) applied to something measured by the *MockHeater* 0D detector; *highlights* a closed loop to test the PID extension.
* **MockTempController** [temperature controller]: *simulates* a temperature controller with an inner PID loop, or a manual power control when the loop is disabled (axes *Temperature* and *Power*); *highlights* a master actuator whose controller is shared with the *MockTempController* 0D detector.
* **MockRandom** [gaussian scan]: *simulates* a stage setting the position (0 to 20) of a noisy Gaussian read by the *MockRandom* detectors; *highlights* a single axis actuator sharing its controller with 0D and 1D detectors of the same controller ID, to scan a known signal.
* **Harmonics** [harmonics]: *simulates* the power (W) of a source read by the *Harmonics* detectors, with a slow response; *highlights* physical units carried by ``pint`` quantities from the controller to the actuator, and a per-axis epsilon.
* **MockComplexSignal** [complex signal]: *simulates* the X and Y axes of a sample scanned by the *MockComplexSignal* 0D detector, with a response time set by the *Tau* setting; *highlights* axes given as a dictionary of name and integer identifier, and a signal to scan in one or two dimensions.
* **MockNamedAxes** [multi-axis]: *simulates* a controller with several axes (X, Y and Z); *highlights* axes having both a name and an integer identifier, the first axis creating the controller and the others receiving it.
* **MockBinary** [user interfaces]: *simulates* a device with two states, 0 or 1; *highlights* the binary user interface of an actuator (``ui_type = UiType.BINARY``).
* **MockRelative** [user interfaces]: *simulates* a stage that can only be moved relatively, with no absolute reference; *highlights* the relative user interface of an actuator (``ui_type = UiType.RELATIVE``), with only ``move_rel`` implemented.
* **BSPiezoMirrorRunTimeError** [error tests]: *simulates* the piezo mirror, but reading its position raises a ``RuntimeError``; *highlights* how PyMoDAQ reacts to an error raised by ``get_actuator_value``.
* **BSPiezoMirrorTimeout** [error tests]: *simulates* the piezo mirror, but the initialization lasts twice the initialization polling time and then fails with an ``IOError``; *highlights* how PyMoDAQ reacts to an initialization timeout.
* **BSPiezoMirrorUninitializing** [error tests]: *simulates* the piezo mirror, but the initialization fails at once with an ``IOError``; *highlights* how PyMoDAQ reacts to a failed initialization.

Viewer0D
++++++++

* **BSPhotodiode** [beam steering]: *simulates* a photodiode measuring the total power sent on the beam steering camera; *highlights* a 0D detector derived from the 2D one, sharing the beam steering controller, with its own averaging.
* **MockHeater** [heater]: *simulates* the temperature of something heated by the *MockHeater* actuator, with noise and ambient temperature settings; *highlights* a detector in a closed loop with an actuator, for the PID extension.
* **MockTempController** [temperature controller]: *simulates* the temperature and the applied power of the temperature controller; *highlights* a detector that is the slave of the *MockTempController* actuator (it receives its controller).
* **MockRandom** [gaussian scan]: *simulates* a noisy Gaussian read at the value of the *MockRandom* actuator; *highlights* a detector coupled to an actuator through a shared controller ID.
* **Harmonics** [harmonics]: *simulates* the power (W) of the source driven by the *Harmonics* actuator; *highlights* a 0D detector emitting data with units from ``pint`` quantities.
* **MockComplexSignal** [complex signal]: *simulates* a signal made of Gaussians, Lorentzians or a CNRS image, read at the position of the *MockComplexSignal* actuators; *highlights* a 0D detector to scan in one or two dimensions, with structures that can be regenerated.
* **MockAdaptive** [complex signal]: *simulates* a signal (Gaussians, Lorentzians or a CNRS image) evaluated at the positions requested by the caller; *highlights* ``grab_data`` receiving the ``positions`` keyword argument, as sent by an adaptive scan.
* **MockErrors** [error tests]: *simulates* a 0D measurement with its standard deviation; *highlights* data carrying errors, computed from the hardware averaging (``hardware_averaging = True``), to test saving and loading them.

Viewer1D
++++++++

* **MockRandom** [gaussian scan]: *simulates* a shuffled Gaussian on a non-sorted axis; *highlights* the sort button of the 1D data viewer.
* **Harmonics** [harmonics]: *simulates* a spectrum of the harmonics of the source driven by the *Harmonics* actuator, with settings for the number of harmonics and the noise on the energy axis; *highlights* an axis with units from ``pint`` quantities, and the ``roi_select`` method receiving the ROI drawn on the viewer.
* **Mock_spectro** [spectrometer]: *simulates* a spectrometer with a laser line, an exposure time and a calibrated wavelength axis, producing one curve with two peaks or two curves; *highlights* an axis (nm) recomputed when a setting changes, and the specific methods used by the ``pymodaq_spectrometer`` package.
* **MockSpectroErrors** [error tests]: *simulates* the *Mock_spectro* spectrometer, each data being the average and the standard deviation of 10 acquisitions; *highlights* data with errors from hardware averaging, to test saving and loading them.

Viewer2D
++++++++

* **BSCamera** [beam steering]: *simulates* a camera imaging a laser spot whose position is set by the *BSPiezoMirror* actuator, with beam size, angle, Gaussian-ness and power noise settings; *highlights* a live acquisition with hardware averaging, and a controller shared with the beam steering actuators.
* **MockCamera** [mock camera]: *simulates* a camera generating various images, with settings for the number of colours and panels, a threshold and a read-only property; *highlights* pixel axes, a live acquisition, hardware averaging, several data in one acquisition, and the X, Y and Theta actuators of the same name moving the image.
* **RoiStuff** [mock camera]: *simulates* the *MockCamera* camera whose image can be cropped to the ROI drawn on the viewer; *highlights* the ``roi_select`` method receiving a ``RoiInfo`` from the viewer, and data cropped inside the plugin.

ViewerND
++++++++

* **MockEvents** [photon events]: *simulates* a photon counting camera: the position and arrival time of photons replayed from a recorded file; *highlights* N-dimensional data, an acquisition thread with Qt callbacks, temporary data emitted during the acquisition, histograms in time of flight and in position, and saving the events.

Simulated setups
================

The instruments above that are meant to be used together. Give the same *controller ID* to the instruments of a
setup that share a controller. The experiment files (``resources/*.xml``) are to be copied in the
``.pymodaq/experiments`` folder, they load in the Dashboard of PyMoDAQ 5.3.

.. list-table::
   :header-rows: 1
   :widths: 18 32 20 30

   * - Setup
     - Instruments
     - Experiment file
     - What it shows
   * - Beam steering with a piezo mirror
     - *BSPiezoMirror* (X and Y), *BSPowerMeter*, *BSCamera*, *BSPhotodiode*
     - ``beam_steering_piezo.xml``
     - One controller shared by five modules, moves that take time, and a 2D and a 0D detector reading the same beam
   * - Beam steering on a camera image
     - *MockCamera* actuators (X, Y, Theta), *MockCamera* detector, optionally *RoiStuff*
     - ``beam_steering.xml``
     - Axes moving the image of a camera, live acquisition, ROI selection, and the PID model *PIDModelBeamSteering* (axes Xpiezo and Ypiezo, detector Camera)
   * - Heater and PID
     - *MockHeater* actuator and detector
     - ``Heater.xml``
     - A closed loop for the PID extension
   * - Temperature controller
     - *MockTempController* actuator (Temperature, Power) and detector
     - ``TempController.xml``
     - A master actuator and a slave detector on one controller, with an inner PID loop
   * - Scanning a known signal
     - *MockRandom* actuator, 0D and 1D detectors
     - none
     - Scans of a noisy Gaussian, the sort button of the 1D viewer
   * - Harmonics
     - *Harmonics* actuator, 0D and 1D detectors
     - none
     - Physical units from ``pint`` quantities
   * - Complex signal and adaptive scan
     - *MockComplexSignal* actuator and 0D detector, *MockAdaptive*
     - none
     - Scans in one or two dimensions, the ``positions`` of an adaptive scan
   * - Spectrometer
     - *Mock_spectro*, *MockSpectroErrors*
     - none
     - A calibrated wavelength axis that follows a setting
   * - Actuator interfaces
     - *MockNamedAxes*, *MockBinary*, *MockRelative*
     - none
     - Named axes, binary and relative user interfaces
   * - Photon events
     - *MockEvents*
     - none
     - N-dimensional data, acquisition in a thread, temporary data
   * - Error handling
     - *BSPiezoMirrorRunTimeError*, *BSPiezoMirrorTimeout*, *BSPiezoMirrorUninitializing*, *MockErrors*, *MockSpectroErrors*
     - none
     - Errors on reading and on initialization, data with errors


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
