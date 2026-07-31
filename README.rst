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

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **MockCamera**: set of X, Y or theta actuators moving a light image on the corresponding camera instrument. To
  be used with the 2D detector **MockCamera**.  An experiment file called **beam_steering.xml** is available in the
  resources folder to be copied in the .pymodaq/experiments folder to orchestrate such a simulated beam steering
  experiment.
* **MockNamedAxes**: Show examples of multi axis actuator controller specifying both a name and an integer ID
* **MockRandom** actuator to be used with the corresponding 0D detector. If they share the same ID in the preset then
  this actuator can be moved in the [0-20] range (even randomly) to retrieve a noisy gaussian
* **MockTauMulti**: controller with multiple axes and showing how to add a characteristic time (to mimic real
  instruments)
* **MockHeater**: actuator simulating the heating of something (in Watt). To be used with the mockHeater 0D detector.
  An experiment file called **Heater.xml** is available in the resources folder to
  be copied in the .pymodaq/experiments folder to orchestrate such a simulated experiment. Can be used to test the
  PID extension.
* **MockTempController** simulation of a temperature controller with inner PID stabilization loop possibilities or
  manual power control. Has two axes: *Temperature* for the PID setpoint (if PID enabled) and *Power* for manual power
  controller if PID disabled. An experiment file called **TempController.xml** is available in the resources folder to
  be copied in the .pymodaq/experiments folder to orchestrate such a simulated experiment.

Viewer0D
++++++++

* **MockAdaptive**: to be used to show how a detector can be used for adaptive samplking (not working yet with PyMoDAQ4)
* **MockRandom**: generate a value of a noisy gaussian given the current value of the underlying mock controller.
  To be used with the MockRandom actuator. If they share the same ID in the preset then this actuator can be moved in
  the [0-20] range (even randomly) to retrieve a noisy gaussian
* **MockHeater**: detector simulating the temperature measurement of something. To be used with the mockHeater actuator
* **MockTempController** simulation of a temperature controller (should be slave of the MockTempController master
  actuator). Probe both the instantaneous temperature and the current applied power

Viewer1D
++++++++

* **MockSpectro**: mimic data one coulf obtain from a spectrometer. Specific methods are also added to seemlessly use
  this detector with the Spectrometer extension (not yet working with PyMoDAQ4)
* **MockRandom**: Generate a noisy Gaussian with a spread axis (to illustrate the sorting button action of the Viewer1D
  data viewer
* **Pinem**: Generate Photon-Induced Near-field Electron Microscopy spectra. It is Electron energy loss spectroscopy
  from the interaction of a near-field (could be induced by a laser on a sample) and probed by the electronic beam.
  The coupling between the near-field and the electronic beam can be tuned using various parameters (g1, g2, theta)...


Viewer2D
++++++++

* **MockCamera**: if connected with a preset with the MockCamera actuator (or a few of them, X, Y and thera), then the
  image displayed on screen is moved or rotated accordingly to the actuators value. Perfect for a beamsteering example
* **RoiStuff**: example of ROI exporting into the instrument plugin. Not yet working, planned to be ok for the future
  >= 4.2.* releases.


ViewerND
++++++++

* **MockEvents**: Simulate the acquisition of photons received on a timepix camera (position and time of arrival of each photon)


PID Models
==========


Extensions
==========


Installation instructions
=========================

* PyMoDAQ >= 5 (except for some of them, specified in this README)
* nothing in particular to be installed, they are all virtual instruments
