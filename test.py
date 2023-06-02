from neuropack.devices import BrainFlowDevice
from neuropack.utils.recording import record, record_erp
from neuropack.tasks import PersistentColorTask

if __name__ == "__main__":
    task = PersistentColorTask(3,5,"blue", "red", 200)

    with BrainFlowDevice.CreateMuse2BLEDDevice() as device:
        a = record_erp(device, task, 10, verbose=True, start_on_wear=True)
        a.plot_ch("Fp1")
