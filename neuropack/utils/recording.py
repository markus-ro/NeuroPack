from time import time
from typing import Union

from ..containers import EEGContainer, LiveEEGContainer
from ..devices.base import DeviceBase
from ..tasks.base import PersistentTaskBase, TaskBase


def __wait_for_wear(device: DeviceBase, verbose: bool = True):
    """Waits for device to be worn.

    :param device: Device to check
    :type device: DeviceBase
    :param verbose: Print progress to console, defaults to True
    :type verbose: bool, optional
    """
    if verbose:
        print("Waiting for device to be worn...")
    while not device.is_worn():
        pass
    if verbose:
        print("Device is worn.")


def record(device: DeviceBase,
           duration_s: int,
           verbose: bool = True,
           start_on_wear: bool = True,
           check_worn: bool = True) -> EEGContainer:
    """Records data from device for a given duration. The data is returned as EEGContainer object.
    If visualize is set to True, the data is also plotted. If verbose is set to True, the progress
    is printed to the console. If check_worn is set to True, the recording will stop if the device
    is not worn anymore.

    :param device: Device to record from (must be connected)
    :type device: DeviceBase
    :param duration_s: Duration of recording in seconds
    :type duration_s: int
    :param visualize: Visualize data while recording, defaults to False
    :type visualize: bool, optional
    :param verbose: Print progress to console, defaults to True
    :type verbose: bool, optional
    :param start_on_wear: Start recording when device is worn, defaults to True
    :type start_on_wear: bool, optional
    :param check_worn: Check if device is worn, defaults to True
    :type check_worn: bool, optional
    :return: Recorded data
    :rtype: Union[EEGContainer,LiveEEGContainer]
    """

    def vprint(t):
        """Verbose print function. Prints t if verbose is set to True."""
        if verbose:
            print(t)

    assert device.is_connected(), "Device must be connected to record data."
    assert duration_s > 0, "Duration must be greater than 0."

    # Wait for device to be worn
    if start_on_wear:
        __wait_for_wear(device, verbose)

    # Create container
    params = [device.channel_names, device.sample_rate]
    container = EEGContainer(*params)

    # Start stream
    vprint("Starting stream...")
    device.start_stream()

    # Start recording
    vprint("Starting recording...")

    start_time = time()
    while time() - start_time < duration_s:
        if check_worn and not device.is_worn():
            vprint("Device is not worn anymore. Stopping recording.")
            break
        if device.has_data():
            container.add_data(device.fetch_data())
    vprint("Recording finished.")
    samp = len(container)
    vprint(f"Recorded {samp} samples.")

    # Stop stream
    device.stop_stream()
    vprint("Stopped stream.")

    return container


def record_erp(device: DeviceBase,
               acquisition_task: Union[TaskBase, PersistentTaskBase],
               duration_s: int,
               verbose: bool = True,
               start_on_wear: bool = True,
               check_worn: bool = True) -> EEGContainer:
    """Records data from device for a given duration. The data is returned as EEGContainer object.
    Returned container also contains marked events for ERP analysis.

    :param device: Device to record from (must be connected)
    :type device: DeviceBase
    :param acquisition_task: Acquisition task to use
    :type acquisition_task: Union[TaskBase, PersistentTaskBase]
    :param duration_s: Duration of recording in seconds
    :type duration_s: int
    :param verbose: Print progress to console, defaults to True
    :type verbose: bool, optional
    :param start_on_wear: Start recording when device is worn, defaults to True
    :type start_on_wear: bool, optional
    :param check_worn: Check if device is worn, defaults to True
    :type check_worn: bool, optional
    :return: Recorded data
    :rtype: EEGContainer
    """
    def vprint(t):
        """Verbose print function. Prints t if verbose is set to True."""
        if verbose:
            print(t)

    assert device.is_connected(), "Device must be connected to record data."

    # Wait for device to be worn
    if start_on_wear:
        __wait_for_wear(device, verbose)

    # Start acquisition task
    vprint("Acquisition task started.")
    acquisition_task.start()

    # Start recording
    recording = record(device, duration_s, verbose, False, check_worn)

    # Get event times
    vprint("Getting event times...")
    event_times = []
    while acquisition_task.has_data():
        event_times.append(acquisition_task.fetch_data().timestamp)

    while event_times[0] < recording.timestamps[0]:
        event_times.pop(0)

    while event_times[-1] > recording.timestamps[-1]:
        event_times.pop()

    vprint(f"Found {len(event_times)} events.")

    # Stop acquisition task
    acquisition_task.stop()
    vprint("Acquisition task stopped.")

    for t in event_times:
        recording.mark_event(1, t)

    return recording
