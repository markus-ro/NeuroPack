from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from scipy.fft import fft, fftfreq


class AbstractContainer(ABC):
    __slots__ = "channel_names", "signals", "sample_rate", "timestamps"

    def __init__(
            self,
            channel_names: List[str],
            sample_rate: int,
            signals: Union[List[List[float]], List[NDArray]],
            timestamps: Union[List[float], NDArray]) -> None:
        """Base class for all containers.

        :param channel_names: List of channel names.
        :type channel_names: List[str]
        :param sample_rate: Sample rate of the data.
        :type sample_rate: int
        :param signals: List of signals. Each signal is a list of floats.
        :type signals: Union[List[List[float]], List[NDArray]]
        :param timestamps: List of timestamps. Each timestamp is a float.
        :type timestamps: Union[List[float], NDArray]
        """
        self.channel_names = channel_names
        self.sample_rate = sample_rate
        self.signals = signals
        self.timestamps = timestamps

    @abstractmethod
    def average_ch(self, *channel_selection: Optional[List[str]]):
        """Create Container with an averaged channel. Operation is not performed in place.

        :param channel_selection: Specify channels to average. If None, returns Container with a signal channel, which is the average of all channels. Defaults to None
        :type channel_selection: Optional[List[str]], optional
        """
        pass

    @abstractmethod
    def average_sub_ch(
            self, *channel_selection: Optional[List[Union[Tuple[str], str]]]):
        """Create Container containing several averaged channels. Channels in the new Container are
        made up of specified channels. Each tuple results in one new averaged channel.
        E.g., the input ("TP9", "TP10"), ("AF9", "AF10") results in Container with two new channels. The first
        channel is the average of "TP9" and "TP10". If no channels are selected, averages all channels into one.

        :param channel_selection: Specify channels to average.
        :type channel_selection: Optional[List[Union[Tuple[str], str]]], optional.
        """
        pass

    def power_spectrum(self) -> List[NDArray]:
        """Calculates the power spectrum over all channels using
        Fast Fourier Transformation.

        :return: List containing real parts of frequency domain for each signal. The last entry in the returned list is a list containing the frequencies.
        :rtype: List[NDArray]
        """
        fin = []
        N = len(self)
        xf = fftfreq(N, 1 / self.sample_rate)[:N // 2]
        for ch in self.channel_names:
            yf = fft(self[ch])
            fin.append(2.0 / N * np.abs(yf[0:N // 2]))
        fin.append(xf)
        return fin

    def plot_ch(self, *channel_names: List[str]):
        """Plot stored channel data using matplotlib.

        :param channel_names: List of channel names to plot. If None, plots all channels. Defaults to None.
        :type channel_names: List[str]
        """
        max_val = 0
        if channel_names:
            for ch in channel_names:
                if ch not in self.channel_names:
                    raise Exception("Unknown channel can not be plotted.")
        else:
            channel_names = self.channel_names

        for ch in channel_names:
            plt.plot(self.timestamps, self[ch], label=ch)
            max_val = max(max_val, np.max(np.abs(self[ch])))
        plt.grid()
        plt.xlim([self.timestamps[0], self.timestamps[-1]])
        plt.ylim([-(max_val + 1), max_val + 1])
        plt.legend()
        plt.show()
        plt.close()

    def save_plot_ch(
            self,
            title: str,
            filename: str,
            *channel_names: List[str]):
        """Plot stored channel data using matplotlib and save to file.

        :param title: Title of the plot.
        :type title: str
        :param filename: Filename of the plot.
        :type filename: str
        :param channel_names: List of channel names to plot. If None, plots all channels. Defaults to None.
        :type channel_names: List[str], optional
        """
        max_val = 0
        if channel_names:
            for ch in channel_names:
                if ch not in self.channel_names:
                    raise Exception("Unknown channel can not be plotted.")
        else:
            channel_names = self.channel_names

        for ch in channel_names:
            plt.plot(self.timestamps, self[ch], label=ch)
            max_val = max(max_val, np.max(np.abs(self[ch])))
        plt.grid()
        plt.xlim([self.timestamps[0], self.timestamps[-1]])
        plt.ylim([-(max_val + 1), max_val + 1])
        plt.legend()
        plt.title(title)
        plt.savefig(filename, dpi=300)
        plt.close()

    def plot_ps(self):
        """Plot power spectrum using matplotlib.
        """
        ps = self.power_spectrum()
        for i in range(len(self.channel_names)):
            plt.plot(ps[-1], ps[i], label=self.channel_names[i])
        plt.title("Power Spectrum")
        plt.grid()
        plt.legend()
        plt.show()
        plt.close()

    def __getitem__(self, key):
        if type(key) not in [str, int]:
            raise Exception("Unsupported index type")

        if isinstance(key, int):
            if key >= len(self.channel_names) or key < 0:
                raise Exception("Index out of bound")
            key = self.channel_names[key]

        if key not in self.channel_names:
            raise Exception("No channel with that name")

        i = self.channel_names.index(key)
        return self.signals[i]

    def __setitem__(self, key, value):
        if type(key) not in [str, int]:
            raise Exception("Unsupported index type")

        if isinstance(key, int):
            if key >= len(self.channel_names) or key < 0:
                raise Exception("Index out of bound")
            key = self.channel_names[key]

        if key not in self.channel_names:
            raise Exception("No channel with that name")

        i = self.channel_names.index(key)
        self.signals[i] = value

    def __len__(self):
        if self.signals and len(self.signals) > 0:
            return len(self.signals[0])
        return 0
