from neuropack.devices import BrainFlowDevice
from neuropack.feature_extraction import BandpowerModel
from neuropack.keywave import KeyWave, TemplateDatabase
from neuropack.preprocessing import PreprocessingPipeline
from neuropack.similarity_metrics import bounded_cosine_similarity
from neuropack.tasks import PersistentColorTask

USE_CONT_AUTH = True

# Setup device
device = BrainFlowDevice.CreateMuse2Device()
device.connect()

# Setup task
task = PersistentColorTask(3, 5, "green", "blue", 200, inter_stim_time=300)

# Preprocessing
preprocessing = PreprocessingPipeline()

# Feature extraction model
model = BandpowerModel()

# Database
database = TemplateDatabase()

# Similarity measure
sim = bounded_cosine_similarity

# Default threshold
t = .725

# Create KeyWave instance
k = KeyWave(device, task, preprocessing, model, database, sim, t)

operation_modes = ["enroll", "authenticate", "identify", "stop"]

while True:
    mode = input(
        "Please chose a mode of operation (" +
        ",".join(operation_modes) +
        "): ")
    mode = mode.lower()

    if mode not in operation_modes:
        print("Not a valid mode!\n")

    if mode == "stop":
        print("Stopping demo..")
        break

    if mode == "enroll":
        enroll_id = input("Please enter ID for enrollment: ")
        result = k.enroll(enroll_id)

        if result:
            print("Enrollment successful!\n")
        else:
            print("Enrollment failed!\n")

    if mode == "authenticate":
        auth_id = input("Please enter ID for authentication: ")
        result = k.authenticate(auth_id, USE_CONT_AUTH)

        if result:
            print("Authentication successful!\n")
        else:
            print("Authentication failed!\n")

    if mode == "identify":
        result = k.identify()

        if result[0]:
            print("Identification successful!")
            print("ID: " + result[1])
        else:
            print("Identification failed!\n")

device.disconnect()
del device
