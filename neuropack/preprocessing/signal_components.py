from abc import ABC, abstractclassmethod

import numpy as np

from ..containers import EventContainer


class SignalComponentBase(ABC):
    @abstractclassmethod
    def find(self, data: EventContainer) -> bool:
        """Try to find specified feature in data.

        :param data: Container to check for feature.
        :type data: EventContainer
        :return: Is feature present in EventContainer.
        :rtype: bool
        """
        pass


class Blink(SignalComponentBase):
    def __init__(self, *channel_names) -> None:
        """Check if specified channels in given EventContainer contain a blink.
        If no channels were specified in constructor, checks all channels.
        """
        super().__init__()
        self.channel_names = channel_names

    def find(self, data: EventContainer) -> bool:
        """Check if specified channels in given EventContainer contain a blink.
        If no channels were specified in constructor, checks all channels.

        :param data: _description_
        :type data: EventContainer
        :return: _description_
        :rtype: bool
        """
        channel_names = self.channel_names
        if not channel_names:
            channel_names = data.channel_names

        for ch in channel_names:
            if np.abs(data[ch]).max() > 100:
                return True

        return False
