from typing import List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

from ..utils import osum
from .abstract_container import AbstractContainer


class EventContainer(AbstractContainer):
    def __init__(
            self,
            channel_names: List[str],
            sample_rate: int,
            signals: Union[List[List[float]], List[NDArray]],
            timestamps: Union[List[float], NDArray]) -> None:
        """Container for event data.

        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param sample_rate: Sample rate of the data.
        :type sample_rate: int
        :param signals: List of signals. Each signal is a list of floats.
        :type signals: Union[List[List[float]], List[NDArray]]
        :param timestamps: List of timestamps. Each timestamp is a float.
        :type timestamps: Union[List[float], NDArray]
        """
        if isinstance(signals[0], list):
            signals = [np.array(x) for x in signals]
        if isinstance(timestamps, list):
            timestamps = np.array(timestamps)
        super().__init__(channel_names, sample_rate, signals, timestamps)

    def average_ch(self, *channel_selection: Optional[List[str]]):
        """Create EventContainer with an averaged channel.

        :param channel_selection: Specify channels to average. If None, returns EventContainer with a signal channel, which is the average of all channels. Defaults to None
        :type channel_selection: Optional[List[str]], optional
        """
        if not channel_selection:
            new_channel_name = ["".join(self.channel_names)]
            new_signal = [osum(self.signals) / len(self.signals)]
        else:
            new_channel_name = ["".join(channel_selection)]
            selected_signals = [self[ch] for ch in channel_selection]
            new_signal = [osum(selected_signals) / len(selected_signals)]

        return EventContainer(
            new_channel_name,
            self.sample_rate,
            new_signal,
            np.copy(
                self.timestamps))

    def average_sub_ch(
            self, *channel_selection: Optional[List[Union[Tuple[str], str]]]):
        """Create EventContainer containing several averaged channels. Channels in the new EventContainer are
        made up of specified channels. Each tuple results in one new averaged channel.
        E.g., the input ("TP9", "TP10"), ("AF9", "AF10") results in EventContainer with two new channels. The first
        channel is the average of "TP9" and "TP10". If no channels are selected, averages all channels into one.

        :param channel_selection: Specify channels to average.
        :type channel_selection: Optional[List[Union[Tuple[str], str]]], optional.
        """
        if not len(channel_selection):
            return self.average_ch()

        new_channel_names = []
        new_signals = []

        for t in channel_selection:
            selection = t
            if not isinstance(t, tuple):
                selection = [t]
            selected_signals = [self[ch] for ch in selection]

            new_channel_names.append("".join(selection))
            new_signals.append(osum(selected_signals) / len(selected_signals))

        return EventContainer(
            new_channel_names,
            self.sample_rate,
            new_signals,
            np.copy(
                self.timestamps))

    def contains_blink(self, *channel_names) -> bool:
        """Checks if EventContainer contains a blink. This is done by
        checking if a threshold of 100 is reached. If True, signals
        in EventContainer include a blink.

        :param channel_names: Name of the channel for which the snr should be calculated.
        :type channel_names: *list, optional
        :return: True if blink is contained, False otherwise.
        :rtype: bool
        """
        if not channel_names:
            channel_names = self.channel_names

        for ch in self.channel_names:
            if np.abs(self[ch]).max() > 100:
                return True
        return False

    def snr(self, signal_range: Tuple[int, int] = (
            250, 400), use_absolutes: bool = False) -> dict:
        """Estimates the signal-to-noise ratio for a given channel by dividing the peak amplitude in the signal range by the standard deviation
        of the full eeg epoch. If the amplitude is expected to be negative, e.g., for a negative ERP amplitude, use_absolutes should be true.
        Returns the ratio.

        :param signal_range: Time range in which signal should appear. E.g. for for P300 250-400ms -> (250, 400)
        :type signal_range: Tuple[int, int]
        :param use_absolutes: If true, the absolute value of the signal is used to calculate the peak amplitude, defaults to False
        :type use_absolutes: bool, optional
        :return: Dictionary with channel names as keys and snr as values.
        :rtype: dict
        """
        def find_nearest(array, value):
            return int((np.abs(array - value)).argmin())

        def peak_amplitude(signal, start, stop):
            return np.max(np.abs(signal[start:stop])
                          if use_absolutes else signal[start:stop])

        start = find_nearest(self.timestamps, signal_range[0] / 1000)
        stop = find_nearest(self.timestamps, signal_range[1] / 1000)
        return {
            ch: peak_amplitude(
                self[ch],
                start,
                stop) /
            np.std(
                self[ch]) for ch in self.channel_names}

    def avg_snr(self, channel_names: list = None, signal_range: Tuple[int, int] = (
            250, 400), use_absolutes: bool = False) -> float:
        """Calculates the average snr over all channels in EventContainer. Returns the average snr.

        :param channel_names: List of channel names for which the snr should be calculated. If None, all channels are used.
        :type channel_names: list, defaults to None
        :param signal_range: Time range in which signal should appear. E.g. for P300 250-400ms -> (250, 400)
        :type signal_range: Tuple[int, int]
        :param use_absolutes: If true, the absolute value of the signal is used to calculate the peak amplitude, defaults to False, defaults to False
        :type use_absolutes: bool, optional
        :return: Average snr over all channels.
        :rtype: float
        """
        snr = self.snr(signal_range, use_absolutes)
        if not channel_names:
            channel_names = self.channel_names

        return np.mean([snr[ch] for ch in channel_names])

    def __add__(self, other):
        assert set(self.channel_names) == set(other.channel_names)
        assert len(self.signals[0]) == len(other.signals[0])
        assert self.sample_rate == other.sample_rate

        new_signals = [self[c] + other[c] for c in self.channel_names]

        return EventContainer(
            self.channel_names,
            self.sample_rate,
            new_signals,
            self.timestamps)

    def __truediv__(self, scalar: float):
        if scalar == 0:
            raise Exception("Can't divide by zero.")

        new_signals = [self[c] / scalar for c in self.channel_names]
        return EventContainer(
            self.channel_names,
            self.sample_rate,
            new_signals,
            self.timestamps)

    def __floordiv__(self, scalar: float):
        if scalar == 0:
            raise Exception("Can't divide by zero.")

        new_signals = [self[c] // scalar for c in self.channel_names]
        return EventContainer(
            self.channel_names,
            self.sample_rate,
            new_signals,
            self.timestamps)

    def __eq__(self, other):
        if self.channel_names != other.channel_names:
            return False

        if self.sample_rate != other.sample_rate:
            return False

        if not np.array_equal(self.timestamps, other.timestamps):
            return False

        if len(self.signals) != len(other.signals):
            return False

        for i in range(len(self.signals)):
            if not np.array_equal(self.signals[i], other.signals[i]):
                return False

        return True
