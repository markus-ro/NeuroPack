import sys
import pyglet
from tkinter import Tk
from screeninfo import get_monitors
from typing import Callable, List, Optional, Tuple, Union

from . import TaskBase


class GraphicTaskBase(TaskBase):
    __slots__ = "_window", "_early_stop", "_key_pressed", "screen_width", "screen_height", "key_handler"

    def __init__(
            self,
            min_non_target: int,
            max_non_target: int,
            exposure_time: Union[int, Tuple[int, int]],
            stimuli_record: Optional[List[bool]] = None,
            inter_stim_time: Union[int, Tuple[int, int]] = 200,
            early_stop: Optional[Callable] = None) -> None:
        """Base class for tasks with graphic display. It is based on tkinter. It is not recommended to use it directly.

        :param min_non_target: Minimum number of non-target stimuli.
        :param type: int
        :param max_non_target: Maximum number of non-target stimuli.
        :param type: int
        :param exposure_time: Exposure time of stimuli in ms.
        :param type: Union[int, Tuple[int, int]]
        :param stimuli_record: List of bools. True means target stimulus, False means non-target stimulus.
        :param type: list
        :param inter_stim_time: Time between stimuli in ms.
        :param type: Union[int, Tuple[int, int]]
        :param early_stop: Function to be called when task is stopped early.
        :param type: function"""
        super().__init__(min_non_target, max_non_target,
                         exposure_time, stimuli_record, inter_stim_time)
        self._early_stop = early_stop
        self._key_pressed = False
        self.screen_width = get_monitors()[0].width
        self.screen_height = get_monitors()[0].height

    def set_up(self) -> None:
        """Setup window for further graphic displays.
        """
        self._window = pyglet.window.Window(self.screen_width, self.screen_height, fullscreen=True)
        self._window.set_mouse_visible(False)
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self._window.push_handlers(self.key_handler)

    def main(self) -> None:
        """Async main loop for tk windows. Otherwise it would keep whole process
        busy.
        """
        self._window.dispatch_events()
        if self.key_handler[pyglet.window.key.ESCAPE]:
            self.__early_stop_call()
            return
        self._window.flip()

    def __early_stop_call(self):
        """Stop task early due to user intervention.
        Task will be stopped at next update or through external intervention.
        """
        if self._running and not self._key_pressed:
            self._aborted.value = 1
            self._key_pressed = True
            if self._early_stop:
                self._early_stop()
