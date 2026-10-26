"""A simulated camera that behaves like the cameras of pylablib: images arrive in a buffer filled by its own thread.

It is the driver of the cookbook camera recipe (``DAQ_2DViewer_CookbookCamera``). The methods are those listed in
``pymodaq_plugins_utils.hardware.camera_driver.CameraDriverBase``, and the semantics those of a real driver:

- ``set_roi`` and ``set_exposure`` act on the next images, ``setup_acquisition`` makes the buffer, ``start_acquisition``
  starts the thread that "exposes" the sensor and fills the buffer, ``clear_acquisition`` stops it;
- ``wait_for_frame`` blocks (with a timeout) until new frames are in the buffer, ``read_multiple_images`` and
  ``read_newest_image`` read them. The plugin calls them from its own thread, never from the thread of the camera.

COPY this file as the starting point of the driver of a camera that pylablib does not drive: inherit from
``CameraDriverBase``, replace ``_expose`` and the thread by the calls of the vendor library (or its callback that tells
a frame is ready) and keep the buffer, the counters and ``wait_for_frame``.
"""
import threading
import time
from collections import deque
from typing import Optional, Tuple

import numpy as np

from pymodaq_plugins_utils.hardware.camera_driver import CameraDriverBase

from pymodaq_plugins_mockexamples.hardware.beam_steering import Camera as Sensor


class MockCamera(CameraDriverBase):
    """A 256 x 256 camera with 5.5 um pixels, 16 bits images, looking at a Gaussian spot"""
    gain = 100.  # counts per unit of the signal of the sensor
    buffer_size = 20
    min_frame_period = 0.01  # s, the readout time

    def __init__(self):
        super().__init__()
        self._sensor = Sensor()
        self._width, self._height = Sensor.Nx, Sensor.Ny
        self._roi = (0, self._width, 0, self._height, 1, 1)
        self._exposure = 0.1  # s
        self._rng = np.random.default_rng()

        self._buffer: deque = deque(maxlen=self.buffer_size)
        self._condition = threading.Condition()
        self._n_acquired = 0  # frames made since the start
        self._last_read = 0  # index of the first frame not read yet
        self._last_wait = 0  # value of ``_n_acquired`` at the end of the last wait
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    # --- sensor ----------------------------------------------------------------------------------------------------

    def get_detector_size(self) -> Tuple[int, int]:
        return self._width, self._height

    def get_data_dimensions(self) -> Tuple[int, int]:
        hstart, hend, vstart, vend, hbin, vbin = self._roi
        return (vend - vstart) // vbin, (hend - hstart) // hbin

    def get_roi(self) -> Tuple[int, int, int, int, int, int]:
        return self._roi

    def set_roi(self, hstart=0, hend=None, vstart=0, vend=None, hbin=1, vbin=1):
        hend = self._width if hend is None else hend
        vend = self._height if vend is None else vend
        if not (0 <= hstart < hend <= self._width and 0 <= vstart < vend <= self._height):
            raise ValueError(f'The ROI {(hstart, hend, vstart, vend)} is not inside the {self._width}x{self._height} '
                             f'sensor')
        if hbin < 1 or vbin < 1 or hend - hstart < hbin or vend - vstart < vbin:
            raise ValueError(f'The binning {(hbin, vbin)} does not fit in the ROI')
        if self.acquisition_in_progress():
            raise RuntimeError('Stop the acquisition before changing the ROI')  # as most real cameras
        self._roi = (hstart, hend, vstart, vend, hbin, vbin)

    def set_exposure(self, exposure: float):
        self._exposure = max(float(exposure), 0.)

    def get_pixel_size(self) -> Tuple[float, float]:
        return self._sensor.pixel_size, self._sensor.pixel_size

    def get_device_info(self):
        from types import SimpleNamespace
        return SimpleNamespace(name='Mock camera (cookbook)')

    # --- acquisition -----------------------------------------------------------------------------------------------

    def setup_acquisition(self):
        """Make the buffer; the ROI cannot change while it exists, as for most cameras"""
        with self._condition:
            self._buffer = deque(maxlen=self.buffer_size)
            self._n_acquired = self._last_read = self._last_wait = 0

    def clear_acquisition(self):
        """Stop the thread of the camera and empty the buffer"""
        self._running.clear()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join()
        self._thread = None
        self.setup_acquisition()

    def start_acquisition(self, nframes: int = 1):
        if self.acquisition_in_progress():
            return
        self.setup_acquisition()
        self._running.set()
        self._thread = threading.Thread(target=self._acquire, name='mock camera', daemon=True)
        self._thread.start()

    def acquisition_in_progress(self) -> bool:
        return self._running.is_set()

    def _acquire(self):
        """Thread of the camera: one frame every exposure time, put in the buffer"""
        while self._running.is_set():
            time.sleep(max(self._exposure, self.min_frame_period))
            frame = self._expose()
            with self._condition:
                if not self._running.is_set():
                    break
                self._buffer.append(frame)
                self._n_acquired += 1
                self._condition.notify_all()

    def _expose(self) -> np.ndarray:
        """What the sensor gives for one exposure: the ROI, binned, in counts with shot noise"""
        hstart, hend, vstart, vend, hbin, vbin = self._roi
        height, width = self.get_data_dimensions()
        image = self._sensor.get_sensor_image(0, 0) * self._exposure * 1000 / self._sensor.reference_exposure_ms
        image = image[vstart:vstart + height * vbin, hstart:hstart + width * hbin]
        image = image.reshape(height, vbin, width, hbin).sum(axis=(1, 3))
        return np.clip(self._rng.poisson(image * self.gain), 0, 2 ** 16 - 1).astype(np.uint16)

    def wait_for_frame(self, since: str = 'lastread', nframes: int = 1, timeout: float = 20.0):
        with self._condition:
            if since == 'now':
                target = self._n_acquired + nframes
            elif since == 'lastwait':
                target = self._last_wait + nframes
            elif since == 'start':
                target = nframes
            else:  # 'lastread'
                target = self._last_read + nframes
            if not self._condition.wait_for(lambda: self._n_acquired >= target or not self._running.is_set(),
                                            timeout=timeout):
                raise TimeoutError('Timeout while waiting for a frame')
            self._last_wait = self._n_acquired  # also returns, without a new frame, if the acquisition is stopped

    def read_multiple_images(self, rng=None, peek: bool = False, missing_frame: str = 'skip',
                             return_rng: bool = False):
        """The frames not read yet, as an array (nframes, height, width); older ones may have left the buffer"""
        with self._condition:
            first = max(self._last_read, self._n_acquired - len(self._buffer))
            frames = list(self._buffer)[first - (self._n_acquired - len(self._buffer)):]
            if not peek:
                self._last_read = self._n_acquired
            last = self._n_acquired
        height, width = self.get_data_dimensions()
        array = np.array(frames) if frames else np.zeros((0, height, width), dtype=np.uint16)
        return (array, (first, last)) if return_rng else array

    def read_newest_image(self, peek: bool = False) -> Optional[np.ndarray]:
        with self._condition:
            if not self._buffer:
                return None
            if not peek:
                self._last_read = self._n_acquired
            return self._buffer[-1]

    def close(self):
        self.clear_acquisition()
