import random
from math import copysign
from time import sleep, time
from typing import Literal, Optional, TypedDict, Union

type Dimension = Literal[0,1,2]

type RawDetectorData = Union[
    float,
    list[float],
    list[list[float]],
    list[list[list[float]]]
]

class Bounds(TypedDict):
    '''  A simple min max dictionnary  '''
    min : float
    max : float

class ActuatorDriver:
    ''' 
        Class to simulate an actuator driver.

        It can be instanciated with units (or not) and with min/max bounds
        It provides a `move_at` methods that moves the actuator
        to the provided value, and a `get_value` method that
        returns the current position
    '''

    def __init__(self, bounds : Bounds, home : float = 10., units : Optional[str] = None):
        self.__time : float
        
        if units:
            self.units = units

        self._min, self._max = sorted([bounds['min'], bounds['max']])
        
        self._channels = 1
        self._home = self._bounded(home) 
        self._position = self._bounded(home)
        self.__target = self._bounded(home)

        # time to go from one bound to the other
        # is (arbitrarly) 10s, so here is the speed
        # in units/s
        self.__speed = (self._max - self._min)/10


    def has_units(self) -> bool:
        return hasattr(self, 'units')


    @property
    def home(self) -> float:
        return self._home
    
    @property
    def position(self) -> float:
        '''
            Get the position 
        '''
        if self.is_moving():
            '''
                Actually update the value to simulate movement
                if the position has not yet reached the target
                according to the defined speed
            '''
            new_time = time() 
            delta_time = new_time - self.__time

            max_step_towards_target = self.__speed*delta_time
            remaining_step_towards_target = self.__target - self._position

            #get the direction of the step by getting the sign 
            sign = copysign(1, remaining_step_towards_target)
            
            step = sign*min(abs(remaining_step_towards_target), max_step_towards_target)
            self._position += step
            self.__time = new_time
        return self._position

    def is_moving(self) -> bool:
        return self._position != self.__target

    def stop_move(self):
        self.__target = self._position
    
    def _bounded(self, value : float) -> float:
        return max(self._min, min(value, self._max))


    def move_at(self, value : float, rel : bool = False):
        '''
           simulate a move to a postion
        '''
        if rel:
            value += self.position
        self.__target = self._bounded(value)
        self.__time = time()


class SLMDriver:
    ''' 
        Class to simulate a SLM.
    '''
    def __init__(self, width : int = 32, height : int = 16):
        self.units = ''

        self.__time : float
        self._min = 0.
        self._max = 255.

        self._channels = 1

        def generate_random_array(height, width):
            import random
            return [[float(random.randint(0, 255)) for _ in range(width)] for _ in range(height)]

        home = [[0.]*width]*height

        home = generate_random_array(height, width)

        self._home = self._bounded(home) 
        self._position = self._bounded(home)
        self.__target = self._bounded(home)

    def __str__(self):
        lines = []
        for row in self._position:
            for value in row:
                gray = int(value)
                lines.append(f"\033[48;2;{gray};{gray};{gray}m  \033[0m")
            lines.append("\n")

        return ''.join(lines)

    def has_units(self) -> bool:
        return False


    @property
    def home(self) -> list[list[float]]:
        return self._home
    
    @property
    def position(self) -> list[list[float]]:
        '''
            Get the position 
        '''
        if self.is_moving():
            self._position = self.__target

        return self._position

    def is_moving(self) -> bool:
        return self._position != self.__target

    def stop_move(self):
        self.__target = self._position
    
    def _bounded(self, values : list[list[float]]) -> list[list[float]]:
        return [[ max(self._min, min(v, self._max)) for v in row] for row in values]


    def move_at(self, value : list[list[float]], rel : bool = False):
        '''
           simulate a move to a postion
        '''
        if rel:
            value = [[v + p for v, p in zip(row_value, row_position)] for row_value, row_position in zip(value, self.position)]

        self.__target = self._bounded(value)
        self.__time = time()

        
class DetectorDriver:
    '''

        Class to simulate the driver of a detector.

        It can be build using its constructor with the following arguments:
            * dimension: the dimension of the data (0, 1, or 2)
            * data_type: the type of data produced (int or float) 
            * x_axis_len: mandatory and useful for dimensions >= 1, gives the number
                          of points of an acquisition 
            * y_axis_len: like x_axis_len but for dimensions >= 2
            * a list of labels corresponding to the acquired channels 
                (in this implementation, only one channel can exists)
            
        It provides a method `acquire` that returns the randomly generated data 
        according to the dimensions:
            - 0D: a scalar
            - 1D: a list of x_axis_len scalars
            - 2D: a list of y_axis_len lists of x_axis_len scalars   

    '''
    def __init__(self, dimension : Dimension = 0, x_axis_len : int = 0,
        y_axis_len : int = 0, acq_time_ms : int = 200, labels : list[str] = [],
        channels : int = 1
    ):
        self._acq_time_ms = acq_time_ms
        self._dimension = dimension

        if dimension >= 1 and x_axis_len == 0:
            raise TypeError(f"Dimension is {dimension} but no x_axis_len provided!")
        if dimension >= 2 and y_axis_len == 0:
            raise TypeError(f"Dimension is {dimension} but no y_axis_len provided!")

        self._x_axis_len = x_axis_len
        self._y_axis_len = y_axis_len
        self._labels = labels
        self._channels = channels

    def _acquire_0d(self) -> float:
        return random.uniform(-255,255)
        

    def _acquire_1d(self) -> list[float]:
        return [self._acquire_0d() for _ in range(self._x_axis_len)]


    def _acquire_2d(self) -> list[list[float]]:
        return [self._acquire_1d() for _ in range(self._y_axis_len)]

    @property
    def labels(self):
        return self._labels
    
    def is_multichannel(self) -> bool:
        return self._channels > 1

    def acquire(self) -> RawDetectorData:
        ''' 
            Simulate acquisition from the detector
        '''
        sleep(self._acq_time_ms/1000)
        
        acquisition_function = getattr(self, f'_acquire_{self._dimension}d', self._acquire_0d)
        if self.is_multichannel():
            return [acquisition_function() for _ in range(self._channels)]
        return acquisition_function()


