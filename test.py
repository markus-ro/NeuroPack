from neuropack import EEGContainer
from neuropack.preprocessing import BandpassFilter
from neuropack.utils import oavg

# Load the data
file_path = '/home/markus/Desktop/dat.csv'
new_file_path = '/home/markus/Desktop/new_dat.csv'
channel_names = ["TP9", "AF7", "AF8", "TP10"]
sample_rate = 256

raw = EEGContainer.from_csv(file_path, sample_rate, channel_names)
# BandpassFilter(1,30,)(raw)

events = raw.get_events(2, 100, 800)
average_ev = oavg(events)

# Plot the data
average_ev.plot_ch("TP9", "TP10")

# Save the data
raw.save_signals(new_file_path)
