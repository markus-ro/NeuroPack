from typing import Union

import numpy as np
from scipy.ndimage import shift


class FastQueue():
    __slots__ = ["size", "data", "head", "__raw"]

    def __init__(self, size: int = 256) -> None:
        """Optimized implementation of a queue for fast access and insertion.
        Uses a numpy array of fixed size to store the data. This allows for fast
        access and insertion at the end of the queue. If the queue is full, the
        first element is removed.

        :param size: Size of the queue, defaults to 256
        :type size: int, optional
        """
        self.size = size
        self.data = np.zeros(size, dtype=np.float32)
        self.head = -1
        self.__raw = None

    def push(self, value: float) -> None:
        """Inserts an element at the end of the queue.
        If the queue is full, the first element is removed.

        :param value: Element to be added.
        :type value: Float
        """
        self.__raw = None
        if self.head == self.size - 1:
            self.pop()
            self.push(value)
            return

        if self.head < self.size:
            self.head += 1
            self.data[self.head] = value

    def overflow_push(self, value: float) -> Union[float, None]:
        """Inserts an element at the end of the queue. If the queue
        is full, the first element is removed. The removed item is
        returned.
        """
        v = None
        if len(self) == self.size:
            v = self.pop()
        self.push(value)
        return v

    def pop(self) -> float:
        self.__raw = None
        if self.head == -1:
            raise IndexError("pop from empty queue")

        value = self.data[0]
        self.__roll()
        return value

    def is_full(self) -> bool:
        """Returns True if the queue is full.

        :return: True if the queue is full.
        :rtype: bool
        """
        return self.head == self.size - 1

    def raw(self) -> np.ndarray:
        """Returns the raw numpy array.

        :return: Raw numpy array.
        :rtype: np.ndarray
        """
        if self.head == self.size:
            return self.data

        if self.__raw is not None:
            return self.__raw

        self.__raw = self.data[:self.head + 1]
        return self.__raw

    def __roll(self):
        """Rolls the queue by one element. The first element is removed and the
        rest of the elements are shifted by one position. The last element is
        set to zero.
        """
        cval = 0.0
        shift(self.data, -1, cval=cval, output=self.data)
        self.head -= 1

    def __len__(self) -> int:
        """Returns the number of elements in the queue.

        :return: Number of elements in the queue.
        :rtype: int
        """
        return self.head + 1

    def __getitem__(self, index: int) -> float:
        """Returns the element at the given index.

        :param index: Index of the element to be returned.
        :type index: int
        :return: Element at the given index.
        :rtype: float
        """
        return self.raw()[index]
