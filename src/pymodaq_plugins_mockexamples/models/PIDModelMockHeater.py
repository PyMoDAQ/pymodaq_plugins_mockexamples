import numpy as np

from pymodaq.extensions.pid.utils import PIDModelGeneric
from pymodaq.utils.data import DataToActuators, DataActuator
from pymodaq_data import DataToExport



class PIDModelMockHeater(PIDModelGeneric):

    limits = dict(max=dict(state=False, value=10),
                  min=dict(state=False, value=0), )
    konstants = dict(kp=0.001, ki=0, kd=0.0000)

    actuators_name = ["Heater"]
    detectors_name = ['Temperature']

    Nsetpoints = 1
    setpoint_ini = [20]
    setpoints_names = ['Temperature']



    def __init__(self, pid_controller):
        super().__init__(pid_controller)

    def update_settings(self, param):
        """
        Get a parameter instance whose value has been modified by a user on the UI
        Parameters
        ----------
        param: (Parameter) instance of Parameter object
        """
        if param.name() == '':
            pass

    def ini_model(self):
        super().ini_model()

    def convert_input(self, measurements: DataToExport) -> DataToExport:
        """
        Convert the measurements in the units to be fed to the PID (same dimensionality as the setpoint)
        Parameters
        ----------
        measurements: DataToExport
         DataToExport object from which the model extract a value of the same units as the setpoint

        Returns
        -------
        DataToExport: the converted input as 0D DataCalculated stored in a DataToExport
        """

        return DataToExport('output', data=[measurements.get_data_from_name(self.detectors_name[0])])

    def convert_output(self, outputs: list[float], dt: float, stab=True) -> DataToActuators:
        """
        Convert the output of the PID in units to be fed into the actuator
        Parameters
        ----------
        outputs: (list of float) output value from the PID from which the model extract a value of the same units as the actuator
        dt: (float) elapsed time in seconds since last call

        Returns
        -------
        DataToActuatorPID: the converted output as a DataToActuatorPID object (derived from DataToExport)
        """
        out_put_to_actuator = DataToActuators('Boiler',
                                              mode='abs',
                                              data=[DataActuator(name=self.actuators_name[0],
                                                                 data = [np.atleast_1d(outputs[0] / dt)])],)


        return out_put_to_actuator



