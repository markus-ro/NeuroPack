import copy
import csv
from collections import defaultdict
from typing import List, Optional, Tuple, Union

import numpy as np
from pyedflib import highlevel

from neuropack.devices.base import BCISignal

from ..devices.base import BCISignal
from ..utils.marker_vault import MarkerVault
from .abstract_container import AbstractContainer
from .event_container import EventContainer


class EEGContainer(AbstractContainer):
    __slots__ = "events", "event_markers"

    @classmethod
    def from_csv(
            cls,
            file: str,
            sample_rate: int,
            channel_names: List[str],
            contains_markers: bool = True):
        """Create EEGContainer from data. Data is expected to be in the following format: <timestamp>, <channels>*n, <target marker>

        :param file: File containing data.
        :type file: str
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param contains_markers: If True, last column is treated as target marker, defaults to False
        :type contains_markers: bool, optional
        """
        t = cls(channel_names, sample_rate)
        t.load_csv(file, contains_markers=contains_markers)
        return t

    @classmethod
    def from_edf(
            cls,
            file: str,
            sample_rate: int,
            channel_names: List[str],
            time_channel: Union[str, Tuple[str, str]] = None,
            marker_channel: str = None):
        """Create EEGContainer from EDF file.

        :param file: File containing data.
        :type file: str
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param time_channel: Channel name or list of channel names containing time stamps. If a tuple is provided, the first channel is used as seconds and the second as milliseconds. If None, timestamps are generated from sample rate. Defaults to None.
        :type time_channel: Union[str, Tuple[str, str]]
        :param marker_channel: Channel name containing event markers. Defaults to None.
        :type marker_channel: str, optional"""
        t = cls(channel_names, sample_rate)
        t.load_edf(file, time_channel, marker_channel)
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
        self.event_markers = MarkerVault()
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

    def add_marker(self, marker: str, timestamp_s: int) -> None:
        """Marks specific event in time with marker. Markers are stored in a MarkerVault.
        Provided timestamp is altered to match timestamp of the closest data point.

        :param marker: Marker to add.
        :type marker: str
        :param timestamp_s: Timestamp in seconds.
        :type timestamp_s: int
        """
        clostest_time_idx = self.__find_closest_timestamp(timestamp_s)
        new_time = self.timestamps[clostest_time_idx]
        self.event_markers.add_marker(new_time, marker)

    def get_marker(self, marker: str) -> List[float]:
        """Returns list of timestamps for specific marker.

        :param marker: Marker to get timestamps for.
        :type marker: str
        :return: List of timestamps.
        :rtype: List[int]
        """
        return self.event_markers.get_marker(marker)

    def get_events(self, marker: str, before: int = 50, after: int = 100) -> List[EventContainer]:
        """Returns list of EventContainers for specific marker. EventContainers contain all channels centered around the event.
        
        :param marker: Marker to get events for.
        :type marker: str
        :param before: Duration in milliseconds before the event to include in EventContainer, defaults to 50
        :type before: int
        :param after: Duration in milliseconds after the event to include in EventContainer, defaults to 100
        :type after: int
        """
        def create_event(t, b_idx, a_idx):
            _timestamps = np.array(self.timestamps[b_idx:a_idx])
            _timestamps -= t
            _signals = [np.array(s[b_idx:a_idx]) for s in self.signals]
            return EventContainer(self.channel_names, self.sample_rate, _signals, _timestamps)

        events = []
        for t in self.event_markers.get_marker(marker):
            before_idx, after_idx = self.__calc_samples_idx(t, before, after)
            events.append(create_event(t, before_idx, after_idx))
        
        return events

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

    def load_csv(self, file_name: str, contains_markers: bool = True):
        """Load data from a csv file.
        The first col has to be the column with timestamps. Following this,
        the different channels must follow. The last column must contain either a 0, no
        target, or a 1, target.

        Channels are read in the same order as configured for the container. The additional channels are ignored if more channels
        are present than in the container.
        <timestamp>, <channels>*n, <target marker?>

        :param file_name: File name to read from.
        :type file_name: str
        :param contains_markers: If True, the last column is interpreted as target marker. Defaults to True
        :type contains_markers: bool, optional
        """

        # Reset object before loading new signals
        self.timestamps = []
        self.signals = [list() for _ in range(len(self.channel_names))]

        with open(file_name) as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for line in reader:
                # Skip empty lines
                if len(line) == 0: continue
                
                # Get timestamp and signals
                t = float(line[0])
                signals = [float(x)
                           for x in line[1: len(self.channel_names) + 1]]

                # Add data
                self.add_data(BCISignal(t, signals))

                # Check if a marker is present
                # Has to be done after adding data, because the marker is added to the last timestamp
                if contains_markers and int(line[-1]) != 0:
                    self.event_markers.add_marker(int(line[-1]), t)
                

    def load_edf(
            self,
            file: str,
            time_channel: Union[str, Tuple[str, str]] = None,
            marker_channel: str = None):
        """Load data from an EDF file. If time_channel is None, timestamps are generated from sample rate.

        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param sample_rate: Sample rate in Hz.
        :type sample_rate: int
        :param file: File containing data.
        :type file: str
        :param time_channel: Channel name or list of channel names containing time stamps. If a tuple is provided, the first channel is used as seconds and the second as milliseconds. If None, timestamps are generated from sample rate. Defaults to None.
        :type time_channel: Union[str, Tuple[str, str]]
        :param marker_channel: Channel name containing event markers. Defaults to None.
        :type marker_channel: str, optional"""
        all_channels = self.channel_names.copy()

        # Include time channel(s) if provided
        if time_channel is not None:
            if isinstance(time_channel, str):
                all_channels.append(time_channel)
            else:
                all_channels.extend(time_channel)

        # Include event channel if provided
        if marker_channel is not None:
            all_channels.append(marker_channel)

        # Load data from EDF file
        signals, _, _ = highlevel.read_edf(file, ch_names=all_channels)

        # Create time stamps from time channel(s)
        if time_channel is None:
            self.timestamps = [(1 / self.sample_rate) *
                               i for i in range(len(signals[0]))]

        if isinstance(time_channel, str):
            self.timestamps = signals[all_channels.index(time_channel)]

        if isinstance(time_channel, tuple):
            self.timestamps = []
            fidx = all_channels.index(time_channel[0])
            sidx = all_channels.index(time_channel[1])
            self.timestamps = [signals[fidx][i] + signals[sidx]
                               [i] / 1000 for i in range(len(signals[0]))]

        # Add signal data
        for i in range(len(self.channel_names)):
            self.signals[i] = signals[all_channels.index(
                self.channel_names[i])].tolist()

        if marker_channel:
            markers = signals[all_channels.index(marker_channel)]
            for i in range(len(markers)):
                if markers[i] != 0:
                    self.event_markers.add_marker(markers[i], self.timestamps[i])

    def save_signals(self, file_name: str):
        """Store data in csv format.

        :param file_name: File name to write to.
        :type file_name: str
        :param event_marker: Character to signify an event in saved data. Non-events always get marked with a 0.
        :type file_name: str
        """
        timeline = self.event_markers.get_timeline()

        with open(file_name, "w", newline='') as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["timestamps"] + self.channel_names + ["Marker"])

            for i in range(len(self.timestamps)):
                t = self.timestamps[i]

                # Check if marker is present
                marker = 0
                if len(timeline) and t == timeline[0][0]:
                    marker = timeline.pop(0)[1]
                    
                # Write data
                writer.writerow([t] + [ch[i]
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

    def __calc_samples_idx(self, timestamp_s: float, before_ms: int, after_ms: int) -> Tuple[int, int]:
        """Calculates the start and end index of the samples to be returned. Ensures the event is always always in bound of the recorded data. If the event is too close to the start or end of the recording, the returned ideices are shifted accordingly. Calculates index by converting the provided time in 
        milliseconds to samples. This is done by first converting the time in milliseconds to seconds and then multiplying by the sample rate.

        :param timestamp_s: Time stamp in seconds.
        :type timestamp_s: float
        :param before_ms: Time in milliseconds before the event to include in the returned data.
        :type before_ms: int
        :param after_ms: Time in milliseconds after the event to include in the returned data.
        :type after_ms: int
        :return: Start and end index of the samples to be returned.
        :rtype: Tuple[int, int]
        """
        event_time_idx = self.__find_closest_timestamp(timestamp_s)

        # Calculate number of samples before and after event
        # Add 1 to after_ms to ensure the event is always included
        before_samples = (before_ms * self.sample_rate) // 1000
        before_idx = max(event_time_idx - before_samples, 0)

        after_samples = (after_ms * self.sample_rate) // 1000 + 1
        after_idx = min(event_time_idx + after_samples, len(self.timestamps))

        return (before_idx, after_idx)

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
