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

Below is the list of the instruments included in this plugin. Every entry follows the same pattern: what the
instrument *simulates*, then what it *highlights* of PyMoDAQ. Example experiment files (``resources/*.xml``) are to be
copied in the ``.pymodaq/experiments`` folder to set up the matching instruments together in the Dashboard:
``beam_steering.xml`` (the *MockCamera* actuators and detector), ``beam_steering_mock.xml`` (the beam steering
instruments, *MockNamedAxes* and *MockEvents*), ``Heater.xml`` and ``TempController.xml``.

Actuators
+++++++++

* **BSPiezoMirror**

  * *Simulates*: the X and Y tilt axes of a piezo mirror steering a laser beam, with a response time set by the *Tau* setting.
  * *Highlights*: a multi-axis actuator sharing its controller with the beam steering detectors and the power meter (same controller ID), and a move that takes time to complete.

* **BSPowerMeter**

  * *Simulates*: the power (W) of the beam steered by the piezo mirror, set through an actuator axis.
  * *Highlights*: an actuator on the *Power* axis of the same shared beam steering controller.

* **BSPiezoMirrorRunTimeError**

  * *Simulates*: the piezo mirror, but reading its position raises a ``RuntimeError``.
  * *Highlights*: how PyMoDAQ reacts to an error raised by ``get_actuator_value`` (for tests).

* **BSPiezoMirrorTimeout**

  * *Simulates*: the piezo mirror, but the initialization lasts twice the initialization polling time and then fails with an ``IOError``.
  * *Highlights*: how PyMoDAQ reacts to an initialization timeout (for tests).

* **BSPiezoMirrorUninitializing**

  * *Simulates*: the piezo mirror, but the initialization fails at once with an ``IOError``.
  * *Highlights*: how PyMoDAQ reacts to a failed initialization (for tests).

* **Harmonics**

  * *Simulates*: the power (W) of a source whose output is read by the *Harmonics* detectors, with a slow response.
  * *Highlights*: physical units carried by ``pint`` quantities from the controller to the actuator, and a per-axis epsilon.

* **MockBinary**

  * *Simulates*: a device with two states, 0 or 1.
  * *Highlights*: the binary user interface of an actuator (``ui_type = UiType.BINARY``), here a very simple actuator returning the value set into it.

* **MockCamera**

  * *Simulates*: the X, Y and rotation (Theta) axes moving the image of the *MockCamera* 2D detector.
  * *Highlights*: a multi-axis actuator sharing its controller with a detector, and the example experiment file ``resources/beam_steering.xml``.

* **MockComplexSignal**

  * *Simulates*: the X and Y axes of a sample scanned by the *MockComplexSignal* 0D detector, with a response time set by the *Tau* setting.
  * *Highlights*: axes given as a dictionary of name and integer identifier, and a signal to scan in one or two dimensions.

* **MockHeater**

  * *Simulates*: the heating power (W) applied to something that is measured by the *MockHeater* 0D detector.
  * *Highlights*: a closed loop to test the PID extension, with the example experiment file ``resources/Heater.xml``.

* **MockNamedAxes**

  * *Simulates*: a controller with several axes (X, Y and Z).
  * *Highlights*: multi-axis actuators whose axes have both a name and an integer identifier, the first axis creating the controller and the others receiving it.

* **MockRandom**

  * *Simulates*: a stage that sets the position (0 to 20) of a noisy Gaussian read by the *MockRandom* detectors.
  * *Highlights*: a single axis actuator sharing its controller with 0D and 1D detectors when they have the same controller ID, to scan a known signal.

* **MockRelative**

  * *Simulates*: a stage that can only be moved relatively, with no absolute reference.
  * *Highlights*: the relative user interface of an actuator (``ui_type = UiType.RELATIVE``) with only ``move_rel`` implemented.

* **MockTempController**

  * *Simulates*: a temperature controller with an inner PID loop, or a manual power control when the loop is disabled; it has the axes *Temperature* (the PID setpoint) and *Power*.
  * *Highlights*: a master actuator whose controller is shared with the *MockTempController* 0D detector, and the example experiment file ``resources/TempController.xml``.


Viewer0D
++++++++

* **BSPhotodiode**

  * *Simulates*: a photodiode measuring the total power sent on the beam steering camera.
  * *Highlights*: a 0D detector derived from the 2D one, sharing the beam steering controller, with its own averaging.

* **Harmonics**

  * *Simulates*: the power (W) of the source driven by the *Harmonics* actuator.
  * *Highlights*: a 0D detector emitting data with units from ``pint`` quantities.

* **MockAdaptive**

  * *Simulates*: a signal (Gaussians, Lorentzians or a CNRS image) evaluated at the positions requested by the caller.
  * *Highlights*: ``grab_data`` receiving the ``positions`` keyword argument, as sent by an adaptive scan.

* **MockComplexSignal**

  * *Simulates*: a signal made of Gaussians, Lorentzians or a CNRS image, read at the position of the *MockComplexSignal* actuators.
  * *Highlights*: a 0D detector to scan in one or two dimensions, with structures that can be regenerated.

* **MockErrors**

  * *Simulates*: a 0D measurement with its standard deviation.
  * *Highlights*: data carrying errors, computed from the hardware averaging (``hardware_averaging = True``), to test saving and loading them.

* **MockHeater**

  * *Simulates*: the temperature of something heated by the *MockHeater* actuator, with noise and ambient temperature settings.
  * *Highlights*: a detector in a closed loop with an actuator, for the PID extension.

* **MockRandom**

  * *Simulates*: a noisy Gaussian read at the value of the *MockRandom* actuator.
  * *Highlights*: a detector coupled to an actuator through a shared controller ID.

* **MockTempController**

  * *Simulates*: the temperature and the applied power of the temperature controller.
  * *Highlights*: a detector that is the slave of the *MockTempController* actuator (it receives its controller).


Viewer1D
++++++++

* **Harmonics**

  * *Simulates*: a spectrum of the harmonics of the source driven by the *Harmonics* actuator, with settings for the number of harmonics and the noise on the energy axis.
  * *Highlights*: an axis with units from ``pint`` quantities, and the ``roi_select`` method receiving the ROI drawn on the viewer.

* **MockRandom**

  * *Simulates*: a shuffled Gaussian on a non-sorted axis.
  * *Highlights*: the sort button of the 1D data viewer.

* **Mock_spectro**

  * *Simulates*: a spectrometer with a laser line, an exposure time and a calibrated wavelength axis, producing one curve with two peaks or two curves.
  * *Highlights*: an axis (nm) recomputed when a setting changes, and the specific methods used by the ``pymodaq_spectrometer`` package.

* **MockSpectroErrors**

  * *Simulates*: the *Mock_spectro* spectrometer, each data being the average and the standard deviation of 10 acquisitions.
  * *Highlights*: data with errors from hardware averaging, to test saving and loading them.


Viewer2D
++++++++

* **BSCamera**

  * *Simulates*: a camera imaging a laser spot whose position is set by the *BSPiezoMirror* actuator, with beam size, angle, Gaussian-ness and power noise settings.
  * *Highlights*: a live acquisition with hardware averaging, and a controller shared with the beam steering actuators.

* **MockCamera**

  * *Simulates*: a camera generating various images, with settings for the number of colours and panels, a threshold and a read-only property.
  * *Highlights*: pixel axes, a live acquisition, hardware averaging, several data in one acquisition, and the X, Y and Theta actuators of the same name moving the image.

* **RoiStuff**

  * *Simulates*: the *MockCamera* camera whose image can be cropped to the ROI drawn on the viewer.
  * *Highlights*: the ``roi_select`` method receiving a ``RoiInfo`` from the viewer, and data cropped inside the plugin.


ViewerND
++++++++

* **MockEvents**

  * *Simulates*: a photon counting camera: the position and arrival time of photons replayed from a recorded file.
  * *Highlights*: N-dimensional data, an acquisition thread with Qt callbacks, temporary data emitted during the acquisition, histograms in time of flight and in position, and saving the events.



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
