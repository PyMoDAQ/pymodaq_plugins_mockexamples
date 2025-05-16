# -*- coding: utf-8 -*-
"""
Created the 24/10/2022

@author: Sebastien Weber
"""
import numpy as np
import pymodaq_utils.math_utils as mutils

from pymodaq_plugins_mockexamples.hardware.camera_wrapper import Camera
from pymodaq_plugins_mock.hardware.wrapper import ActuatorWrapperWithTauMultiAxes


class BeamSteeringActuators(ActuatorWrapperWithTauMultiAxes):
    axes = ['X', 'Y', 'Power']
    _units = ['mm', 'mm', 'W']
    _epsilon = 0.01
    _tau = 0.01  # s

    def __init__(self):
        super().__init__()

        self._current_values = [0, 0, 1]


class Camera:
    Nx = 256
    Ny = 256
    amp = 20
    x0 = 128
    y0 = 128
    _dx = 20
    _dy = 10
    _n = 1
    _angle = 0
    amp_noise = 4
    fringes = False

    def __init__(self):
        super().__init__()
        self._image: np.ndarray = None
        self.base_Mock_data()

    @property
    def dx(self):
        return self._dx

    @dx.setter
    def dx(self, new_dx: float):
        self._dx = new_dx
        self.base_Mock_data()

    @property
    def dy(self):
        return self._dy

    @dy.setter
    def dy(self, new_dy: float):
        self._dy = new_dy
        self.base_Mock_data()

    @property
    def n(self):
        return self._n

    @n.setter
    def n(self, new_n: int):
        self._n = new_n
        self.base_Mock_data()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, new_angle: float):
        self._angle = new_angle
        self.base_Mock_data()

    def base_Mock_data(self):
        self.x_axis = np.linspace(0, self.Nx, self.Nx, endpoint=False)
        self.y_axis = np.linspace(0, self.Ny, self.Ny, endpoint=False)
        data_mock = self.amp * (
            mutils.gauss2D(self.x_axis, self.x0, self.dx,
                           self.y_axis, self.y0, self.dy,
                           self.n,
                           self.angle))

        for indy in range(data_mock.shape[0]):
            if self.fringes:
                data_mock[indy, :] = data_mock[indy, :] * np.sin(self.x_axis / 4) ** 2

        self._image = data_mock
        return self._image

    def get_data(self, xpos, ypos) -> np.ndarray:
        return np.roll(np.roll(self._image + self.amp_noise * np.random.rand(len(self.y_axis),
                                                                             len(self.x_axis)),
                               int(xpos), axis=1),
                       int(ypos), axis=0)


class BeamSteering:
    _tau = BeamSteeringActuators._tau

    def __init__(self):

        self.actuators = BeamSteeringActuators()
        self.camera = Camera()
        self.camera.fringes = False

    @property
    def tau(self):
        """
        fetch the characteristic decay time in s
        Returns
        -------
        float: the current characteristic decay time value

        """
        return self.actuators.tau

    @tau.setter
    def tau(self, value: float):
        """
        Set the characteristic decay time value in s
        Parameters
        ----------
        value: (float) a strictly positive characteristic decay time
        """
        self.actuators.tau = value

    def move_at(self, value: float, axis: str):
        """
        """
        if axis in BeamSteeringActuators.axes:
            self.actuators.move_at(value, axis)

    def stop(self, axis: str):
        self.actuators.stop(axis)

    def get_value(self, axis: str):
        """
        Get the current actuator value
        Returns
        -------
        float: The current value
        """
        return self.actuators.get_value(axis)

    def get_camera_data(self) -> np.ndarray:
        return self.camera.get_data(self.actuators.get_value('X'),
                                    self.actuators.get_value('Y')) * self.actuators.get_value('Power')

    def get_photodiode_data(self) -> float:
        
        idx = int(Camera.Nx / 2)
        idy = int(Camera.Ny / 2)
        width = 20
        
        return np.mean(
            self.camera.get_data(self.actuators.get_value('X'),
                                    self.actuators.get_value('Y'))[
               int(idy-width/2): int(idy+width/2),
               int(idx-width/2): int(idx+width/2)]) * self.actuators.get_value('Power')
