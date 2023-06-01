from time import time
from typing import Union

from ..containers import EEGContainer, LiveEEGContainer
from ..devices.base import DeviceBase


def record(device: DeviceBase,
           duration_s: int,
           visualize: bool = False,
           verbose: bool = True,
           start_on_wear: bool = True,
           check_worn: bool = True) -> Union[EEGContainer,
                                             LiveEEGContainer]:
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

    def vprint(self, t):
        """Verbose print function. Prints t if verbose is set to True."""
        if verbose:
            print(t)

    assert device.is_connected(), "Device must be connected to record data."
    assert duration_s > 0, "Duration must be greater than 0."

    # Start stream
    vprint("Starting stream...")
    device.start_stream()

    # Wait for device to be worn
    if start_on_wear:
        vprint("Waiting for device to be worn...")
        while not device.is_worn():
            pass
        vprint("Device is worn.")

    # Create container
    container = LiveEEGContainer(
        device.channel_names,
        device.sampling_rate) if visualize else EEGContainer(
        device.channel_names,
        device.sampling_rate)
    if visualize:
        vprint("Starting visualization...")
        container.start_vis()

    # Start recording
    vprint("Starting recording...")
    start_time = time()
    while time() - start_time < duration_s:
        if check_worn and not device.is_worn():
            vprint("Device is not worn anymore. Stopping recording.")
            break
        if device.has_data():
            container.append(device.fetch_data())

    # Stop stream
    vprint("Stopping stream...")
    device.stop_stream()
    if visualize:
        vprint("Stopping visualization...")
        container.stop_vis()

    return container
