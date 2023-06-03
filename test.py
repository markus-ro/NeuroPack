from neuropack import EEGContainer

# Load the data
file_path = 'C:/Users/MarkusR/Desktop/studie002_2019.05.08_14.08.51.edf'
channel_names = [x.strip(
) for x in "AF3, F7, F3, FC5, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4".split(',')]
time_channel = ("TIME_STAMP_s", "TIME_STAMP_ms")

container = EEGContainer.from_edf(file_path, 256, channel_names, time_channel)

container.plot_ps()
container.plot_ch()

print(channel_names)
