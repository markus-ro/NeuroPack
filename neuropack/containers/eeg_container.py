import copy
import csv
from collections import defaultdict
from typing import List, Optional, Tuple, Union

import numpy as np
from pyedflib import highlevel

from neuropack.devices.base import BCISignal

from ..devices.base import BCISignal
from .abstract_container import AbstractContainer
from .event_container import EventContainer


class EEGContainer(AbstractContainer):
    __slots__ = "events"

    @classmethod
    def from_csv(
            cls,
            file: str,
            sample_rate: int,
            channel_names: List[str],
            event_marker: str = "1"):
        """Create EEGContainer from data. Data is expected to be in the following format: <timestamp>, <channels>*n, <target marker>

        :param file: File containing data.
        :type file: str
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param event_marker: Marker indicating the start of a new event. Defaults to "1".
        :type event_marker: str, optional
        """
        t = cls(channel_names, sample_rate)
        t.load_csv(file, event_marker=event_marker)
        return t

    @classmethod
    def from_edf(
        cls,
        file: str,
        sample_rate: int,
        channel_names: List[str],
        time_channel: Union[str, Tuple[str, str]] = None,
        event_channel: str = None):
        """Create EEGContainer from EDF file.

        :param file: File containing data.
        :type file: str
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param time_channel: Channel name or list of channel names containing time stamps. If a tuple is provided, the first channel is used as seconds and the second as milliseconds. If None, timestamps are generated from sample rate. Defaults to None.
        :type time_channel: Union[str, Tuple[str, str]]
        :param event_channel: Channel name containing event markers. Defaults to None.
        :type event_channel: str, optional"""
        t = cls(channel_names, sample_rate)
        t.load_edf(file, time_channel, event_channel)
        return t

    def __init__(self, channel_names: List[str], sample_rate: int) -> None:
        """Create EEGContainer containing several channels. Channels are expected to be in the same order as signals added to the container.

        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        """
        super().__init__(
            channel_names, sample_rate, [
                list() for _ in range(
                    len(channel_names))], [])
        self.events = []

    def add_data(self, rec: BCISignal):
        """Add new measured data point to the container. Data points consist of combinations of
        a time stamp and measured signals, and signals are expected to be in the same order as channels
        initially configured for the container.

        :param rec: Data point to add to the container.
        :type rec: BCISignal
        """
        if len(rec.signals) != len(self.channel_names):
            raise Exception(
                "Number of signals does not match number of channels provided")

        self.timestamps.append(rec.timestamp)
        for i in range(len(rec.signals)):
            self.signals[i].append(rec.signals[i])

    def add_event(
            self,
            event_time: int,
            before: int = 50,
            after: int = 100) -> EventContainer:
        """Adds an event to the recording. Returns EventContainer containing all data for added event.

        :param event_time: Time of event data in the container will be centered around.
        :type event_time: int
        :param before: Duration in milliseconds before the event to include in EventContainer, defaults to 50
        :type before: int
        :param after: Duration in milliseconds after the event to include in EventContainer, defaults to 100
        :type after: int
        :return: EventContainer containing all channels centered around event_time.
        :rtype: EventContainer
        """
        event = self.__find_closest_timestamp(event_time)
        event_time = self.timestamps[event]
        if event_time not in self.events:
            self.events.append(event_time)

        # Calculate number of samples before and after event
        before_samples = (before * self.sample_rate) // 1000
        before_samples = max(event - before_samples, 0)
        after_samples = (after * self.sample_rate) // 1000 + 1
        after_samples = min(event + after_samples, len(self.timestamps))

        # Create new timestamps and signals
        new_timestamps = np.array(
            self.timestamps[before_samples: after_samples])
        new_timestamps -= event_time
        new_signals = [np.array(x[before_samples: after_samples])
                       for x in self.signals]

        # Create new EventContainer
        return EventContainer(
            self.channel_names,
            self.sample_rate,
            new_signals,
            new_timestamps)

    def average_ch(self, *channel_selection: Optional[List[str]]):
        """Create EEGContainer with an averaged channel.

        :param channel_selection: Specify channels to average. If None, returns EEGContainer with a signal channel, which is the average of all channels. Defaults to None
        :type channel_selection: Optional[List[str]], optional
        """
        def s_osum(x):
            if len(x) == 0:
                return None
            if len(x) == 1:
                if isinstance(x[0], list):
                    return np.array(x[0])
                return x
            s = copy.deepcopy(x[0])
            for o in x[1:]:
                s = np.add(s, o)
            return s

        # If no channels are specified, average all channels
        if not channel_selection:
            # Average all channels
            new_channel_name = ["".join(self.channel_names)]
            new_signal = [s_osum(self.signals) / len(self.signals)]
        else:
            # Average specified channels
            new_channel_name = ["".join(channel_selection)]
            selected_signals = [self[ch] for ch in channel_selection]
            # Average signals
            new_signal = [s_osum(selected_signals) / len(selected_signals)]

        # Convert to list
        new_signal = [x.tolist() for x in new_signal]

        # Create new EEGContainer
        _t = EEGContainer(new_channel_name, self.sample_rate)
        _t.timestamps = copy.deepcopy(self.timestamps)
        _t.signals = new_signal

        return _t

    def average_sub_ch(
            self, *channel_selection: Optional[List[Union[Tuple[str], str]]]):
        """Create EEGContainer containing several averaged channels. Channels in the new EEGContainer are
        made up of specified channels. Each tuple results in one new averaged channel.
        E.g., the input ("TP9", "TP10"), ("AF9", "AF10") results in EEGContainer with two new channels. The first
        channel is the average of "TP9" and "TP10". If no channels are selected, averages all channels into one.

        :param channel_selection: Specify channels to average.
        :type channel_selection: Optional[List[Union[Tuple[str], str]]], optional.
        """
        def s_osum(x):
            if len(x) == 0:
                return None
            if len(x) == 1:
                if isinstance(x[0], list):
                    return np.array(x[0])
                return x
            s = copy.deepcopy(x[0])
            for o in x[1:]:
                s = np.add(s, o)
            return s

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
            new_signals.append(
                s_osum(selected_signals) /
                len(selected_signals))

        # Convert to list
        new_signals = [x.tolist() for x in new_signals]

        # Create new EEGContainer
        _t = EEGContainer(new_channel_names, self.sample_rate)
        _t.timestamps = copy.deepcopy(self.timestamps)
        _t.signals = new_signals

        return _t

    def get_events(self, event_code: str, before: int,
                   after: int) -> List[EventContainer]:
        """Get EventContainer representation for all events with event_code stored in container.

        :param event_code: Event code for which to get all events.
        :type event_code: str
        :param before: Before duration.
        :type before: int
        :param after: After duration.
        :type after: int
        :return: List containing EventContainers for all stored events.
        :rtype: List[EventContainer]
        """
        return [self.add_event(x, before, after) for x in self.events]

    def load_csv(self, file_name: str, event_marker: str = "1"):
        """Load data from a csv file.
        The first col has to be the column with timestamps. Following this,
        the different channels must follow. The last column must contain either a 0, no
        target, or a 1, target.

        Channels are read in the same order as configured for the container. The additional channels are ignored if more channels
        are present than in the container.
        <timestamp>, <channels>*n, <target marker?>

        :param file_name: File name to read from.
        :type file_name: str
        """

        # Reset object before loading new signals
        self.timestamps = []
        self.signals = [list() for _ in range(len(self.channel_names))]

        with open(file_name) as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for line in reader:
                timestamp = float(line[0])
                signals = [float(x)
                           for x in line[1: len(self.channel_names) + 1]]

                if line[-1] == event_marker:
                    self.events.append(timestamp)
                self.add_data(BCISignal(timestamp, signals))

    def load_edf(
        self,
        file: str,
        time_channel: Union[str, Tuple[str, str]] = None,
        event_channel: str = None):
        """Load data from an EDF file. If time_channel is None, timestamps are generated from sample rate.

        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        :param file: File containing data.
        :type file: str
        :param time_channel: Channel name or list of channel names containing time stamps. If a tuple is provided, the first channel is used as seconds and the second as milliseconds. If None, timestamps are generated from sample rate. Defaults to None.
        :type time_channel: Union[str, Tuple[str, str]]
        :param event_channel: Channel name containing event markers. Defaults to None.
        :type event_channel: str, optional"""
        all_channels = self.channel_names.copy()

        # Include time channel(s) if provided
        if time_channel is not None:
            if isinstance(time_channel, str):
                all_channels.append(time_channel)
            else:
                all_channels.extend(time_channel)
        
        # Include event channel if provided
        if event_channel is not None:
            all_channels.append(event_channel)

        # Load data from EDF file
        signals, _, _ = highlevel.read_edf(file, ch_names=all_channels)

        # Create time stamps from time channel(s)
        if time_channel is None:
            self.timestamps = [(1/self.sample_rate) * i for i in range(len(signals[0]))]

        if isinstance(time_channel, str):
            self.timestamps = signals[all_channels.index(time_channel)]
        
        if isinstance(time_channel, tuple):
            self.timestamps = []
            fidx = all_channels.index(time_channel[0])
            sidx = all_channels.index(time_channel[1])
            self.timestamps = [signals[fidx][i] + signals[sidx][i] / 1000 for i in range(len(signals[0]))]
        
        # Add signal data
        for i in range(len(self.channel_names)):
            self.signals[i] = signals[all_channels.index(self.channel_names[i])]

        # TODO: Create events from event channel

    def save_signals(self, file_name: str, event_marker: str = "1"):
        """Store data in csv format.

        :param file_name: File name to write to.
        :type file_name: str
        :param event_marker: Character to signify an event in saved data. Non-events always get marked with a 0.
        :type file_name: str
        """
        assert event_marker != "0"

        with open(file_name, "w", newline='') as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["timestamps"] + self.channel_names + ["Marker"])

            for i in range(len(self.timestamps)):
                timestamp = self.timestamps[i]
                marker = 1 if timestamp in self.events else 0
                writer.writerow([timestamp] + [ch[i]
                                for ch in self.signals] + [marker])

    def shift_timestamps(self):
        """Shifts all timestamps to start at 0. This is useful if the EEGContainer is created
        from a file with a start time stamp != 0. Can also be used to anonymize data,i.e., by removing
        any information about the time of the recording. All events are shifted accordingly.
        """
        if len(self.timestamps) == 0:
            return

        first_timestamp = self.timestamps[0]
        self.timestamps = [x - first_timestamp for x in self.timestamps]
        self.events = [x - first_timestamp for x in self.events]

    def __find_closest_timestamp(self, timestamp: float) -> float:
        """Finds the index of the closest stored timestamp to provided time stamp.
        Ensures the event is always centered at 0.

        :param timestamp: External time stamp to search for in milliseconds.
        :type timestamp: float
        :return: Index of closest stored time stamp.
        :rtype: float
        """
        timestamp_arr = np.array(self.timestamps)
        return (np.abs(timestamp_arr - timestamp)).argmin()

    def __eq__(self, other):
        if self.channel_names != other.channel_names:
            return False

        if self.sample_rate != other.sample_rate:
            return False

        if self.timestamps != other.timestamps:
            return False

        if self.events != other.events:
            return False

        if len(self.signals) != len(other.signals):
            return False

        for i in range(len(self.signals)):
            if self.signals[i] != other.signals[i]:
                return False

        return True

    def __len__(self):
        return len(self.timestamps)
