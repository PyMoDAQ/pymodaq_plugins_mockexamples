import numpy as np

from pymodaq.extensions.data_mixer.model import DataMixerModel, np  # np will be used in method eval of the formula

from pymodaq_utils.math_utils import gauss1D, my_moment

from pymodaq_data.data import DataToExport, DataWithAxes
from pymodaq_gui.parameter import Parameter

from pymodaq.extensions.data_mixer.parser import (
    extract_data_names, split_formulae, replace_names_in_formula)


from scipy.signal import find_peaks



class DataMixerModelFit(DataMixerModel):
    params = [
        {'title': 'Find Peaks', 'name': 'find_peaks', 'type': 'group', 'children': [
            {'title': 'Highest Peak', 'name': 'highest_peak', 'type': 'float', 'value': 0, 'readonly': True},
            {'title': 'Options', 'name': 'options', 'type': 'bool', 'value': False, 'children': [
                {'title': 'Height', 'name': 'height', 'type': 'float', 'value': 0},
                {'title': 'Distance', 'name': 'distance', 'type': 'int', 'value': 1, 'max': 1},
            ]},
            ]},
        {'title': 'Cropping', 'name': 'cropping', 'type': 'group', 'children': [
            {'title': 'Index min from peak', 'name': 'ind_min', 'type': 'int', 'value': 0},
            {'title': 'Index max from peak', 'name': 'ind_max', 'type': 'int', 'value': 100},

        ]},
    ]

    def ini_model(self):
        pass

    def update_settings(self, param: Parameter):
        pass

    def process_dte(self, dte: DataToExport):
        dte_processed = DataToExport('computed')
        dwa = dte[0].deepcopy()

        options = {}
        if self.settings['find_peaks', 'options']:
            for param in self.settings.child('find_peaks', 'options'):
                options[param.name()] = param.value()

        peaks_indices, _ = find_peaks(dwa[0], **options)

        heights = [float(dwa.isig[index][0][0]) for index in peaks_indices]
        ind_max = peaks_indices[np.argmax(heights)]
        self.settings.child('find_peaks', 'highest_peak').setValue(dwa.axes[0].get_data()[ind_max])

        dwa_indexed = dwa.isig[ind_max + self.settings['cropping', 'ind_min']:
                               ind_max + self.settings['cropping', 'ind_max']]
        dwa_indexed.axes = []
        dwa_indexed.create_missing_axes()

        dte_processed.append(dwa_indexed)

        return dte_processed


def main():
    from pymodaq_gui.utils.utils import mkQApp
    from pymodaq.utils.gui_utils.loader_utils import load_dashboard_with_preset

    app = mkQApp('DataMixer')

    preset_file_name = 'harmonics'
    dashboard, extension, win = load_dashboard_with_preset(preset_file_name, 'Data Mixer')
    app.exec()

    return dashboard, extension, win


if __name__ == '__main__':
    main()
