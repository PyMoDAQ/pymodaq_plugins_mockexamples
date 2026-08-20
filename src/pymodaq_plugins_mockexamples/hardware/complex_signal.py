from pymodaq_utils import math_utils as mutils
from pymodaq_data.data import DataToExport, DataRaw, Axis


import numpy as np
from PIL import Image
from pathlib import Path
from pymodaq_plugins_mock.hardware.wrapper import ActuatorWrapperWithTauMultiAxes

here = Path(__file__).parent
# %%
with Image.open(str(here.parent.joinpath('hardware', 'CNRS_degrade.png'))) as im:
    im = im.convert("L")
    data_CNRS = np.array(im)


class DataSignal(ActuatorWrapperWithTauMultiAxes):

    signal_types = ['Lorentzian', 'Gaussian', 'CNRS']
    axes = ['X', 'Y',]
    Nstruct = 1
    _tau = 0.2

    def __init__(self):
        super().__init__()

        self._data = None
        self.signal_type = self.signal_types[0]

    def ini_random_structures(self):
        xlim = [-5, 5]
        ylim = [-5, 5]
        dxmax = np.abs((np.max(xlim) - np.min(xlim)))
        dymax = np.abs((np.max(ylim) - np.min(ylim)))

        Npts = 1000
        self.x0s = np.random.rand(self.Nstruct) * dxmax - np.max(xlim)
        self.y0s = np.random.rand(self.Nstruct) * dymax - np.max(ylim)
        self.dx = np.random.rand(self.Nstruct)
        self.dy = np.random.rand(self.Nstruct)
        self.amp = np.random.rand(self.Nstruct) * 100
        self.slope = np.random.rand(self.Nstruct) / 10

    def random_hypergaussians2D(self, xy, coeff=1):
        x, y = xy
        if not hasattr(x, '__len__'):
            x = [x]
        if not hasattr(y, '__len__'):
            y = [y]
        signal = np.zeros((len(x), len(y)))
        for ind in range(self.Nstruct):
            signal += self.amp[ind] * mutils.gauss2D(x, self.x0s[ind], coeff * self.dx[ind],
                                                    y, self.y0s[ind], coeff * self.dy[ind], 1)
        signal += 0.025 * np.random.rand(len(x), len(y))
        return signal

    def get_random_hypergaussian_datagrid(self) -> DataRaw:
        x = np.linspace(-5, 5, 251)
        y = np.linspace(-5, 5, 251)
        return DataRaw('Random Gaussians', data=[
            self.random_hypergaussians2D((x, y))],
                       axes=[
                           Axis('xaxis', data=x, index=1),
                           Axis('Yaxis', data=y, index=0)]
                       )

    def get_cnrs_datagrid(self) -> DataRaw:
        x = np.linspace(-5, 5, data_CNRS.shape[1])
        y = np.linspace(-5, 5, data_CNRS.shape[0])
        return DataRaw('Random Gaussians', data=[data_CNRS],
                       axes=[
                           Axis('xaxis', data=x, index=1),
                           Axis('Yaxis', data=y, index=0)]
                       )

    def get_data_grid(self):
        if self.signal_type == 'Gaussian':
            return self.get_random_hypergaussian_datagrid()
        elif self.signal_type == 'Lorentzian':
            return self.get_random_lorentzian_1D()
        else:
            return DataRaw('CNRS', data=[data_CNRS])

    def random_hypergaussians2D_signal(self, xy, coeff=1.0):
        return self.random_hypergaussians2D(xy, coeff)[0, 0]

    def diverging1D(self, x, coeff=1.0):
        signal = 0
        for ind in range(self.Nstruct):
            signal += self.amp[ind] * (coeff * self.slope[ind]) ** 2 / ((coeff * self.slope[ind]) ** 2 +
                                                                        (x - self.x0s[ind]) ** 2)
        return signal

    def get_random_lorentzian_1D(self) -> DataRaw:
        x = np.linspace(-5, 5, 401)
        return DataRaw('Random Lorentian', data=[
            self.diverging1D(x)],
                       axes=[
                           Axis('xaxis', data=x, index=0),
                       ]
                       )

    def generate_data(self, x, y=0):
        if self.signal_type == 'Gaussian':
            return self.random_hypergaussians2D_signal((x, y))
        elif self.signal_type == 'Lorentzian':
            return self.diverging1D(x)
        elif self.signal_type == 'CNRS':
            ind_x = max((0, int(min([x, data_CNRS.shape[1] - 1]))))
            ind_y = max((0, int(min([y, data_CNRS.shape[0] - 1]))))
            ind_y = data_CNRS.shape[0] - 1 - ind_y
            return data_CNRS[ind_y, ind_x]

    def get_data_0D(self):
        return self.generate_data(*self._current_values)

