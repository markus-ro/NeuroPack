from time import time

class RunFor:
    def __init__(self):
        """StopWatch class for measuring time in seconds.
        Works by calling the object as a function, which returns False if the time has passed.
        """
        self.start_t = 0

    def start(self):
        """Starts the timer."""
        self.start_t = time()

    def reset(self):
        """Resets the timer."""
        self.start_t = 0

    def __call__(self, for_s):
        """Returns False if the time has passed.
        
        :param for_s: Time in seconds.
        :type for_s: int
        """
        if self.start_t == 0:
            self.start_t = time()

        done = self.start_t + for_s < time()

        if done:
            self.start_t = 0

        return not done

run_for = RunFor()