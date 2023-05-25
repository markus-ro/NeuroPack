from multiprocessing import Process, Queue
from typing import List

import matplotlib.pyplot as plt

from neuropack.devices.base import BCISignal
from neuropack.utils import FastQueue

from ..devices.base import BCISignal
from .eeg_container import EEGContainer


class LiveEEGContainer(EEGContainer):
    def __init__(self, channel_names: List[str], sample_rate: int) -> None:
        """Container capable of displaying live data. Most useful for debugging.

        :param channel_names: Name of channels.
        :type channel_names: List[str]
        :param sample_rate: Sample rate of the data.
        :type sample_rate: int
        """
        super().__init__(channel_names, sample_rate)
        self.queue = None
        self.p = None

    def add_data(self, rec: BCISignal):
        if self.queue:
            self.queue.put(rec)
        super().add_data(rec)

    def start_vis(self):
        """Starts the visualization of the data. This method blocks the main thread.
        """
        if self.p:
            return

        self.queue = Queue()
        self.p = Process(target=self.vis)
        print("Starting visualization. Press Ctrl+C to stop.")
        self.p.start()

    def stop_vis(self):
        """Stops the visualization of the data.
        """
        if self.p:
            self.queue.put(None)
            self.p.join()
            self.p = None

        if self.queue:
            self.queue.close()
            self.queue = None

    def vis(self):
        """Visualization process. This method is called in a separate process.
        Absolutly unoptimized, but works for debugging.
        """
        refresh_rate = self.sample_rate // 2
        x = FastQueue(self.sample_rate)
        y = [FastQueue(self.sample_rate)
             for _ in range(len(self.channel_names))]
        start = 0

        count = 0
        while True:
            count += 1
            rec = self.queue.get()

            # Stop the process if we get a None
            if rec is None:
                break

            # Add new data
            if not len(x):
                start = rec.timestamp
            x.push(rec.timestamp - start)

            for i in range(len(self.channel_names)):
                y[i].push(rec.signals[i])

            # Only update every 500ms, enough for human perception
            if count != refresh_rate:
                continue
            count = 0

            # Plot
            plt.clf()
            plt.ylim(-1000, 1000)
            for i in range(len(self.channel_names)):
                plt.plot(x.raw(), y[i].raw(), label=self.channel_names[i])
            plt.grid()
            plt.legend()
            plt.pause(0.001)
        plt.close()
