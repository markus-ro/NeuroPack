import math
import sys
import tempfile
import unittest
from os import path, remove
from random import randint

import numpy as np
from pyedflib import highlevel

from neuropack.containers import EEGContainer
from neuropack.devices.base import BCISignal

sys.path.append("../")

# TODO: tests for shifting
# TODO: tests for preprocessing


class EEGContainerTests(unittest.TestCase):
    def assertListAlmostEqual(self, list1, list2, msg, delta=0.01):
        self.assertEqual(len(list1), len(list2))
        for i in range(len(list1)):
            self.assertAlmostEqual(list1[i], list2[i], delta=delta, msg=msg)

    def test_add_values(self):
        """Check, that new EEG signals are correctly added to EEGContainer.
        """
        container = EEGContainer(["Ch1", "Ch2"], 256)
        container.add_data(BCISignal(0, [0.1, 0.2]))

        self.assertEqual(container["Ch1"][0], 0.1,
                         "Value was not added as expected")
        self.assertEqual(container["Ch2"][0], 0.2,
                         "Value was not added as expected")

        container.add_data(BCISignal(0, [0.2, 0.1]))

        self.assertEqual(container["Ch1"][1], 0.2,
                         "Value was not added as expected")
        self.assertEqual(container["Ch2"][1], 0.1,
                         "Value was not added as expected")

    def test_wrong_channels(self):
        # arrange
        container = EEGContainer(["Ch1", "Ch2"], 256)
        exception_raised = False

        # action
        try:
            container.add_data(BCISignal(0, [0.1, 0.2, 0.3]))
        except BaseException:
            exception_raised = True

        # check
        self.assertTrue(exception_raised,
                        "No exception was raised despite wrong data.")

    def test_event_data(self):
        """Check, that creating events works as intended.
        """
        # arrange
        container = EEGContainer(["Ch1"], 250)
        signal = [math.sin(x) for x in range(250)]
        timestamps = [x * 4 for x in range(250)]
        event_time_stamp = 500
        signal[125] = 100
        for i in range(250):
            container.add_data(BCISignal(timestamps[i], [signal[i]]))

        # action
        container.mark_event(1, event_time_stamp)
        event = container.get_events(1, 250, 250)[0]

        # check
        self.assertEqual(
            len(event.signals[0]), 125, "Expected exactly 125 signal data points.")
        self.assertEqual(len(event.timestamps), 125,
                         "Expected exactly 125 signal time stamps.")
        i = np.where(event.timestamps == 0)
        self.assertEqual(event.signals[0][i], 100,
                         "Did not find event value at 0 time stamp.")

    def test_save_signals_csv(self):
        """Check, that signals can be saved and loaded in csv format.
        """
        # arrange
        file_name = path.join(tempfile.gettempdir(), "test.csv")
        container = EEGContainer(["Ch1", "Ch2"], 250)
        signal = [math.sin(x) for x in range(250)]
        timestamps = [x * 4 for x in range(250)]
        event_time_stamp = 500
        signal[125] = 100
        for i in range(250):
            container.add_data(BCISignal(timestamps[i], [signal[i], 5]))
        container.mark_event(1, event_time_stamp)

        # action
        container.save_signals(file_name)
        container2 = EEGContainer(["Ch1", "Ch2"], 250)
        container2.load_csv(file_name)

        # check
        self.assertEqual(container, container2,
                         "Loaded container differ from stored ones.")

    def test_save_signals_multiple_markers(self):
        """Check, that signals can be saved and loaded in csv format.
        """
        # arrange
        file_name = path.join(tempfile.gettempdir(), "test.csv")
        container = EEGContainer(["Ch1", "Ch2"], 250)
        signal = [math.sin(x) for x in range(250)]
        timestamps = [x * 4 for x in range(250)]
        event_time_stamp = 500
        signal[125] = 100
        for i in range(250):
            container.add_data(BCISignal(timestamps[i], [signal[i], 5]))
        container.mark_event(1, event_time_stamp)
        container.mark_event(2, event_time_stamp + 100)

        # action
        container.save_signals(file_name)
        container2 = EEGContainer(["Ch1", "Ch2"], 250)
        container2.load_csv(file_name)

        # check
        self.assertEqual(container, container2,
                         "Loaded container differ from stored ones.")

    def test_out_of_bound_markers(self):
        """Check, that markers are not added outside of signal range.
        """
        # arrange
        container = EEGContainer(["Ch1", "Ch2"], 250)
        signal = [math.sin(x) for x in range(250)]
        timestamps = [x * 4 for x in range(250)]
        event_time_stamp = 500
        signal[125] = 100
        for i in range(250):
            container.add_data(BCISignal(timestamps[i], [signal[i], 5]))

        # action
        container.mark_event(1, event_time_stamp)
        container.mark_event(1, event_time_stamp + 1000)

        # check
        self.assertEqual(len(container.get_events(1, 250, 250)), 2,
                         "Expected two events.")

        self.assertEqual(
            container.get_marker(1)[0],
            event_time_stamp,
            "Expected marker at 500.")
        self.assertEqual(container.get_marker(
            1)[1], container.timestamps[-1], "Expected marker at last possible timestamp.")

    def test_load_edf(self):
        """Check, that signals can be loaded from edf file.
        """
        # arrange
        file_name = path.join(tempfile.gettempdir(), "test.edf")

        timestamps = [math.pi * (1 / 32) * x for x in range(32)]
        sin = [math.sin(x) for x in timestamps]
        cos = [math.cos(x) for x in timestamps]
        signals = [
            np.array(
                sin, dtype=np.float64), np.array(
                cos, dtype=np.float64), np.array(
                timestamps, dtype=np.float64)]

        channel_names = ["SIN", "COS", "TIME"]

        signal_headers = highlevel.make_signal_headers(
            channel_names, sample_rate=32)
        header = highlevel.make_header(patientname="test")
        highlevel.write_edf(file_name, signals, signal_headers, header)

        # action
        container = EEGContainer(["SIN", "COS"], 32)
        container.load_edf(file_name, "TIME")

        # check
        self.assertListAlmostEqual(
            container["SIN"],
            signals[0].tolist(),
            "Loaded signals differ from stored ones.")
        self.assertListAlmostEqual(
            container["COS"],
            signals[1].tolist(),
            "Loaded signals differ from stored ones.")
        self.assertListAlmostEqual(
            container.timestamps,
            signals[2].tolist(),
            "Loaded timestamps differ from stored ones.")

        # cleanup
        remove(file_name)

    def test_create_edf(self):
        """Check, that signals can be loaded from edf file.
        """
        # arrange
        file_name = path.join(tempfile.gettempdir(), "test.edf")

        timestamps = [math.pi * (1 / 32) * x for x in range(32)]
        sin = [math.sin(x) for x in timestamps]
        cos = [math.cos(x) for x in timestamps]
        signals = np.array([sin, cos, timestamps])

        channel_names = ["SIN", "COS", "TIME"]

        signal_headers = highlevel.make_signal_headers(
            channel_names, sample_rate=32)
        header = highlevel.make_header(patientname="test")
        highlevel.write_edf(file_name, signals, signal_headers, header)

        # action
        container = EEGContainer.from_edf(
            file_name, 32, ["SIN", "COS"], "TIME")

        # check
        self.assertListAlmostEqual(
            container["SIN"],
            signals[0].tolist(),
            "Loaded signals differ from stored ones.")
        self.assertListAlmostEqual(
            container["COS"],
            signals[1].tolist(),
            "Loaded signals differ from stored ones.")
        self.assertListAlmostEqual(
            container.timestamps,
            signals[2].tolist(),
            "Loaded timestamps differ from stored ones.")

        # cleanup
        remove(file_name)

    def test_numerical_index_access_test(self):
        """Check, that numerical index can be used to access signals.
        """
        # arrange
        container = EEGContainer(["Ch1", "Ch2"], 256)
        for i in range(200):
            container.add_data(
                BCISignal(i, [randint(0, 100), randint(0, 100)]))

        # action and check
        self.assertEqual(
            container["Ch1"],
            container[0],
            "Signal with index 0 differed from first signal in named list.")
        self.assertEqual(
            container["Ch2"],
            container[1],
            "Signal with index 1 differed from second signal in named list.")

    def test_numerical_index_out_of_bound_test(self):
        # arrange
        container = EEGContainer(["Ch1", "Ch2"], 256)
        exception_raised = False

        for i in range(200):
            container.add_data(
                BCISignal(i, [randint(0, 100), randint(0, 100)]))

        # action
        try:
            print(container[-1])
        except BaseException:
            exception_raised = True

        # check
        self.assertTrue(
            exception_raised,
            "No exception was raised despite numerical index out of bound.")

    def test_average_channels(self):
        # arrange
        sample_rate = 256
        length = 20
        channel_names = ["C1", "C2", "C3"]
        signal_data = [[1] * length, [5] * length, [0] * length]
        timestamps = [x for x in range(length)]

        # action
        recording = EEGContainer(
            channel_names,
            sample_rate)
        recording.signals = signal_data
        recording.timestamps = timestamps
        avg_recording = recording.average_ch()

        # check
        self.assertEqual(len(avg_recording.signals), 1,
                         "Found more than one signal. Expected exactly 1.")
        self.assertEqual(len(avg_recording.channel_names), 1,
                         "Found more than one channel name. Expected exactly 1.")
        self.assertEqual(
            avg_recording.channel_names[0],
            "".join(channel_names),
            "Name of new channel is not as expected.")
        self.assertEqual(
            len(
                avg_recording.signals[0]),
            length,
            "Number of recorded data points is not equal to original.")

        self.assertListEqual(
            avg_recording.signals[0],
            [2.0] * length,
            "Average signal is not as expected.")

    def test_average_channels_identity(self):
        # arrange
        sample_rate = 256
        length = 20
        channel_names = ["C1"]
        signal_data = [[1] * length]
        timestamps = [x for x in range(length)]

        # action
        recording = EEGContainer(
            channel_names,
            sample_rate)
        recording.signals = signal_data
        recording.timestamps = timestamps
        avg_recording = recording.average_ch()

        # check
        self.assertEqual(
            recording,
            avg_recording,
            "Average of one channel is not the same as the original.")

    def test_average_channels_selection(self):
        # arrange
        sample_rate = 256
        length = 20
        channel_names = ["C1", "C2", "C3"]
        signal_data = [[1] * length, [5] * length, [0] * length]
        timestamps = [x for x in range(length)]
        selected_channels = ["C1", "C2"]

        # action
        recording = EEGContainer(
            channel_names,
            sample_rate)
        recording.signals = signal_data
        recording.timestamps = timestamps
        avg_recording = recording.average_ch(*selected_channels)

        # check
        self.assertEqual(len(avg_recording.signals), 1,
                         "Found more than one signal. Expected exactly 1.")
        self.assertEqual(len(avg_recording.channel_names), 1,
                         "Found more than one channel name. Expected exactly 1.")
        self.assertEqual(
            avg_recording.channel_names[0],
            "".join(selected_channels),
            "Name of new channel is not as expected.")
        self.assertEqual(
            len(
                avg_recording.signals[0]),
            length,
            "Number of recorded data points is not equal to original.")
        self.assertListEqual(
            avg_recording.signals[0],
            [3.0] * length,
            "Average signal is not as expected.")

        self.assertListEqual(avg_recording["".join(selected_channels)], [
                             3.0] * length, "New channel could not be accessed.")

    def test_average_sub_channel(self):
        # arrange
        sample_rate = 256
        length = 20
        channel_names = ["C1", "C2", "C3"]
        signal_data = [[1] * length, [5] * length, [0] * length]
        timestamps = [x for x in range(length)]
        selected_channels = [("C1", "C2"), ("C1"), ("C2"), ("C1", "C2", "C3")]

        # action
        recording = EEGContainer(
            channel_names,
            sample_rate)
        recording.signals = signal_data
        recording.timestamps = timestamps
        avg_recording = recording.average_sub_ch(*selected_channels)

        # check
        self.assertEqual(len(avg_recording.signals), 4,
                         "Did not find exactly four signals.")

        self.assertEqual(len(avg_recording.channel_names), 4,
                         "Did not find exactly four channel names")

        self.assertEqual(
            len(
                avg_recording.signals[0]),
            length,
            "Number of recorded data points is not equal to original.")

        self.assertEqual(
            "C1C2",
            avg_recording.channel_names[0],
            "First channel was not named \"C1C2\".")
        self.assertEqual(
            "C1",
            avg_recording.channel_names[1],
            "Second channel was not named \"C1\".")
        self.assertEqual(
            "C2",
            avg_recording.channel_names[2],
            "Third channel was not named \"C2\".")
        self.assertEqual(
            "C1C2C3",
            avg_recording.channel_names[3],
            "Fourth channel was not named \"C1C2C3\".")

        self.assertListEqual(
            avg_recording["C1C2"],
            [3.] * length,
            "Channel \"C1C2\" was not as expected.")

        self.assertListEqual(
            avg_recording["C1"],
            [1.] * length,
            "Channel \"C1\" was not as expected.")

        self.assertListEqual(
            avg_recording["C2"],
            [5.] * length,
            "Channel \"C5\" was not as expected.")

        self.assertListEqual(
            avg_recording["C1C2C3"],
            [2.] * length,
            "Channel \"C1C2C3\" was not as expected.")

    def test_average_sub_channel_identity(self):
        # arrange
        sample_rate = 256
        length = 20
        channel_names = ["C1"]
        signal_data = [[1] * length]
        timestamps = [x for x in range(length)]
        selected_channels = [("C1")]

        # action
        recording = EEGContainer(
            channel_names,
            sample_rate)
        recording.signals = signal_data
        recording.timestamps = timestamps
        avg_recording = recording.average_sub_ch(*selected_channels)

        # check
        self.assertEqual(
            recording,
            avg_recording,
            "Average of one channel is not the same as the original.")
