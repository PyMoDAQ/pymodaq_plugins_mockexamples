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

The instruments above grouped by what they simulate. Instruments of a setup that share a controller must have the
same *controller ID* in the Dashboard. The experiment files (``resources/*.xml``) are to be copied in the
``.pymodaq/experiments`` folder, they load in the Dashboard of PyMoDAQ 5.3.

.. _beam steering:

Beam steering with a piezo mirror
+++++++++++++++++++++++++++++++++

One controller shared by five modules, moves that take time, a 2D and a 0D detector reading the same beam.

Experiment file: ``beam_steering_piezo.xml``.

- *BSPiezoMirror* (actuator): simulates the X and Y tilt axes of a piezo mirror steering a laser beam, with a response time set by the *Tau* setting; shows a multi-axis actuator sharing one controller with the power meter, camera and photodiode of the same name family (same controller ID), and a move that takes time.
- *BSPowerMeter* (actuator): simulates the power (W) of the steered beam, set through an actuator axis; shows an actuator on the *Power* axis of the shared beam steering controller.
- *BSPhotodiode* (0D detector): simulates a photodiode measuring the total power sent on the beam steering camera; shows a 0D detector derived from the 2D one, sharing the beam steering controller, with its own averaging.
- *BSCamera* (2D detector): simulates a camera imaging a laser spot whose position is set by the *BSPiezoMirror* actuator, with beam size, angle, Gaussian-ness and power noise settings; shows a live acquisition with hardware averaging, and a controller shared with the beam steering actuators.

.. _mock camera:

Beam steering on a camera image
+++++++++++++++++++++++++++++++

Axes moving the image of a camera, live acquisition and ROI selection. The PID model *PIDModelBeamSteering* uses the axes Xpiezo and Ypiezo and the detector Camera of the experiment.

Experiment file: ``beam_steering.xml``.

- *MockCamera* (actuator): simulates the X, Y and Theta axes moving the image of the *MockCamera* 2D detector; shows a multi-axis actuator sharing its controller with a detector.
- *MockCamera* (2D detector): simulates a camera generating various images, with settings for the number of colours and panels, a threshold and a read-only property; shows pixel axes, a live acquisition, hardware averaging, several data in one acquisition, and the X, Y and Theta actuators of the same name moving the image.
- *RoiStuff* (2D detector): simulates the *MockCamera* camera whose image can be cropped to the ROI drawn on the viewer; shows the ``roi_select`` method receiving a ``RoiInfo`` from the viewer, and data cropped inside the plugin.

.. _heater:

Heater and PID
++++++++++++++

A closed loop for the PID extension.

Experiment file: ``Heater.xml``.

- *MockHeater* (actuator): simulates the heating power (W) applied to something measured by the *MockHeater* 0D detector; shows a closed loop to test the PID extension.
- *MockHeater* (0D detector): simulates the temperature of something heated by the *MockHeater* actuator, with noise and ambient temperature settings; shows a detector in a closed loop with an actuator, for the PID extension.

.. _temperature controller:

Temperature controller with a PID loop
++++++++++++++++++++++++++++++++++++++

A master actuator and a slave detector on one controller, with an inner PID loop.

Experiment file: ``TempController.xml``.

- *MockTempController* (actuator): simulates a temperature controller with an inner PID loop, or a manual power control when the loop is disabled (axes *Temperature* and *Power*); shows a master actuator whose controller is shared with the *MockTempController* 0D detector.
- *MockTempController* (0D detector): simulates the temperature and the applied power of the temperature controller; shows a detector that is the slave of the *MockTempController* actuator (it receives its controller).

.. _gaussian scan:

Scanning a known signal
+++++++++++++++++++++++

Scans of a noisy Gaussian, and the sort button of the 1D viewer.

No experiment file: add the instruments in the Dashboard and give them the same controller ID.

- *MockRandom* (actuator): simulates a stage setting the position (0 to 20) of a noisy Gaussian read by the *MockRandom* detectors; shows a single axis actuator sharing its controller with 0D and 1D detectors of the same controller ID, to scan a known signal.
- *MockRandom* (0D detector): simulates a noisy Gaussian read at the value of the *MockRandom* actuator; shows a detector coupled to an actuator through a shared controller ID.
- *MockRandom* (1D detector): simulates a shuffled Gaussian on a non-sorted axis; shows the sort button of the 1D data viewer.

.. _harmonics:

Harmonics source
++++++++++++++++

Physical units carried by ``pint`` quantities from the controller to the data.

No experiment file: add the instruments in the Dashboard and give them the same controller ID.

- *Harmonics* (actuator): simulates the power (W) of a source read by the *Harmonics* detectors, with a slow response; shows physical units carried by ``pint`` quantities from the controller to the actuator, and a per-axis epsilon.
- *Harmonics* (0D detector): simulates the power (W) of the source driven by the *Harmonics* actuator; shows a 0D detector emitting data with units from ``pint`` quantities.
- *Harmonics* (1D detector): simulates a spectrum of the harmonics of the source driven by the *Harmonics* actuator, with settings for the number of harmonics and the noise on the energy axis; shows an axis with units from ``pint`` quantities, and the ``roi_select`` method receiving the ROI drawn on the viewer.

.. _complex signal:

Complex signal and adaptive scan
++++++++++++++++++++++++++++++++

Scans in one or two dimensions, and the ``positions`` argument of an adaptive scan.

No experiment file: add the instruments in the Dashboard and give them the same controller ID.

- *MockComplexSignal* (actuator): simulates the X and Y axes of a sample scanned by the *MockComplexSignal* 0D detector, with a response time set by the *Tau* setting; shows axes given as a dictionary of name and integer identifier, and a signal to scan in one or two dimensions.
- *MockComplexSignal* (0D detector): simulates a signal made of Gaussians, Lorentzians or a CNRS image, read at the position of the *MockComplexSignal* actuators; shows a 0D detector to scan in one or two dimensions, with structures that can be regenerated.
- *MockAdaptive* (0D detector): simulates a signal (Gaussians, Lorentzians or a CNRS image) evaluated at the positions requested by the caller; shows ``grab_data`` receiving the ``positions`` keyword argument, as sent by an adaptive scan.

.. _spectrometer:

Spectrometer with a calibrated axis
+++++++++++++++++++++++++++++++++++

A wavelength axis that follows a setting, and data with errors.

No experiment file: add the instrument in the Dashboard.

- *Mock_spectro* (1D detector): simulates a spectrometer with a laser line, an exposure time and a calibrated wavelength axis, producing one curve with two peaks or two curves; shows an axis (nm) recomputed when a setting changes, and the specific methods used by the ``pymodaq_spectrometer`` package.

.. _actuator interfaces:

Multi-axis and user interface examples
++++++++++++++++++++++++++++++++++++++

Named axes on one controller, and the binary and relative user interfaces of an actuator.

No experiment file: add the instruments in the Dashboard.

- *MockNamedAxes* (actuator): simulates a controller with several axes (X, Y and Z); shows axes having both a name and an integer identifier, the first axis creating the controller and the others receiving it.
- *MockBinary* (actuator): simulates a device with two states, 0 or 1; shows the binary user interface of an actuator (``ui_type = UiType.BINARY``).
- *MockRelative* (actuator): simulates a stage that can only be moved relatively, with no absolute reference; shows the relative user interface of an actuator (``ui_type = UiType.RELATIVE``), with only ``move_rel`` implemented.

.. _photon events:

Photon counting camera
++++++++++++++++++++++

N-dimensional data, an acquisition thread with Qt callbacks, temporary data emitted during the acquisition.

No experiment file: add the instrument in the Dashboard.

- *MockEvents* (ND detector): simulates a photon counting camera: the position and arrival time of photons replayed from a recorded file; shows N-dimensional data, an acquisition thread with Qt callbacks, temporary data emitted during the acquisition, histograms in time of flight and in position, and saving the events.

.. _error tests:

Error handling
++++++++++++++

Errors on reading and on initialization, and data carrying errors.

No experiment file: add the instruments in the Dashboard.

- *BSPiezoMirrorRunTimeError* (actuator): simulates the piezo mirror, but reading its position raises a ``RuntimeError``; shows how PyMoDAQ reacts to an error raised by ``get_actuator_value``.
- *BSPiezoMirrorTimeout* (actuator): simulates the piezo mirror, but the initialization lasts twice the initialization polling time and then fails with an ``IOError``; shows how PyMoDAQ reacts to an initialization timeout.
- *BSPiezoMirrorUninitializing* (actuator): simulates the piezo mirror, but the initialization fails at once with an ``IOError``; shows how PyMoDAQ reacts to a failed initialization.
- *MockErrors* (0D detector): simulates a 0D measurement with its standard deviation; shows data carrying errors, computed from the hardware averaging (``hardware_averaging = True``), to test saving and loading them.
- *MockSpectroErrors* (1D detector): simulates the *Mock_spectro* spectrometer, each data being the average and the standard deviation of 10 acquisitions; shows data with errors from hardware averaging, to test saving and loading them.

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
