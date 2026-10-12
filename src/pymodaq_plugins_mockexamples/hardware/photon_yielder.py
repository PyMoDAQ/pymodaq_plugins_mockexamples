# -*- coding: utf-8 -*-
"""
Created the 30/10/2023

@author: Sebastien Weber
"""
from pathlib import Path

import numpy as np


here = Path(__file__).parent.parent
data_memory_map = np.load(here.joinpath('resources/KXe_000203_raw.npy'), mmap_mode='r')


class Photons:

    def __init__(self, photon_array: np.ndarray):
        self.index = photon_array[:, 0]
        self.time_stamp = photon_array[:, 4]
        self.x_pos = photon_array[:, 2]
        self.y_pos = photon_array[:, 3]
        self.intensity = photon_array[:, 5]

    def __len__(self):
        return self.index.shape[0]

    def __iter__(self):
        self._iter_index = -1
        return self

    def __next__(self):
        if self._iter_index < len(self) - 1:
            self._iter_index += 1
            return (self.index[self._iter_index],
                    self.time_stamp[self._iter_index],
                    self.x_pos[self._iter_index],
                    self.y_pos[self._iter_index],
                    self.intensity[self._iter_index],)
        else:
            raise StopIteration

    def to_positions_intensity(self):
        return np.array([self.x_pos, self.y_pos, self.intensity])

    def __repr__(self):
        return f'Photon events {self.index}: x:{self.x_pos}, y: {self.y_pos},' \
               f' time: {self.time_stamp}, intensity: {self.intensity}'


class PhotonYielder:
    ind_grabbed = 0

    def __init__(self):
        self._photon_grabber = self._grabber()

    def _grabber(self):
        while self.ind_grabbed < data_memory_map.shape[0]:
            next_grab = np.random.randint(10, 200)
            ind_grabbed = self.ind_grabbed
            self.ind_grabbed += next_grab
            print(self.ind_grabbed)
            yield data_memory_map[ind_grabbed:ind_grabbed+next_grab, ...]

    def grab(self) -> Photons:
        return Photons(next(self._photon_grabber))


if __name__ == '__main__':
    from pathlib import Path
    from qtpy import QtCore
    from pymodaq_data.h5modules.saving import H5SaverLowLevel
    from pymodaq.utils.daq_utils import ThreadCommand
    from pymodaq_data.data import  Axis, DataToExport, DataRaw, DataCalculated, DataWithAxes
    from pymodaq_data.h5modules.data_saving import DataSaverLoader

    here = Path(__file__).parent.joinpath('resources')

    addhoc_file_path = here.joinpath('photons.h5')
    h5temp = H5SaverLowLevel()
    h5temp.init_file(file_name=addhoc_file_path, new_file=True)
    h5temp.get_set_group('/RawData', 'myphotons')

    saver = DataSaverLoader(h5temp)

    data = DataWithAxes('timepix', source='raw', distribution='spread', nav_indexes=(0,),
                        data=[data_memory_map[:, 5], data_memory_map[:, 2], data_memory_map[:, 3]],
                        axes=[Axis('tof', 's', data=data_memory_map[:, 4])])
    saver.add_data('/RawData/myphotons', data, save_axes=True)
    h5temp.close_file()
    photon = PhotonYielder()
    ind = 0
    for ind in range(100):
        print(photon.grab())


    pass
