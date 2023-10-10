# <b>Neuro</b>logics<b>Pack</b>age

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)]() [![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/) [![status: experimental](https://github.com/GIScience/badges/raw/master/status/experimental.svg)](https://github.com/GIScience/badges#experimental) [![License](https://img.shields.io/badge/License-BSD_3--Clause-green.svg)](https://opensource.org/licenses/BSD-3-Clause) 


Simple library to implement prototypes of brainwave-based authentication in Python. Further, it allows for the general usage of brainwave data in Python. I wrote this library as part of my master thesis. If you come across this library and find it useful, feel free to use it and contribute if you like. Currently all graphic components of the library are based on tkinter, which apparently is slow on windows.

## Installation
You can install NeuroPack directly from source:
```bash
git clone https://github.com/markus-ro/neuropack/
cd neuropack
python -m pip install .
``` 

Alternatively, you can install NeuroPack via pip:
```bash
pip install neuropack
```

## Usage
The library itself is seperated into several modules containing different components used for brainwave-based authentication.
These modules are:
- **devices**: Contains implementations and wrappers for EEG recording devices. Currently only a wrapper for the [Brainflow](https://brainflow.org/) library is implemented.
- **tasks**: Contains implementations of different tasks used to acquire event related potentials (ERPs) from EEG data.
- **preprocessing**: Contains implementations of different preprocessing steps used to prepare EEG data for further processing.
- **feature_extraction**: Contains implementations of different feature extraction methods used to extract features from EEG data.
- **similarity**: Contains implementations of different similarity measures used to compare the extracted features.
- **container**: General data container classes used to store EEG data throught various stages of processing.

Additionally to these components, the library contains an example implementation called KeyWave, which can be configured using the different components of the library.
Examples of how to use the various components of the library can be found in:
- [A short introduction to NeuroPack](./examples/introduction.ipynb)
- [Recreation of the recording process described by Krigolson et al. [1]](./examples/P300_Krigolson.ipynb)
- [Playground for the different ERP acquisition tasks](./examples/tasks.ipynb)

## Examples
NeuroPack's component can be used in a variety of different use cases. Through prepared utility functions, 
the library allows for a quick setup and usage. Likewise, the library can be used to implement more complex use cases either by configuring the provided component or by implementing custom ones adhering to the provided interfaces.

### Recording EEG in just a few lines of code
```python
from neuropack.devices import BrainFlowDevice
from neuropack.utils.recording import record

with BrainFlowDevice.CreateMuse2Device() as device:
    data = record(device, duration_s=15, verbose=True, start_on_wear=True)
    data.save_signals("recording.csv")
```

### Load data and apply various preprocessing steps as pipeline
```python
from neuropack.preprocessing import PreprocessingPipeline
from neuropack.preprocessing.filters import DetrendFilter, BandpassFilter
from neuropack.preprocessing.filters import ReductionFilter
from neuropack.containers import EEGContainer

pipeline = PreprocessingPipeline(DetrendFilter(), BandpassFilter())
pipeline.add_filter(ReductionFilter("TP9", "TP10"))

data = EEGContainer.from_file("recording.csv", 256, ["TP9", "Fp1", "Fp2", "TP10"])
pipeline.apply(data)
```

### Using KeyWave, an end-to-end implementation of brainwave-based authentication
```python
from neuropack.devices import BrainFlowDevice
from neuropack.feature_extraction import BandpowerModel
from neuropack.keywave import KeyWave, TemplateDatabase
from neuropack.preprocessing import PreprocessingPipeline
from neuropack.similarity_metrics import bounded_cosine_similarity
from neuropack.tasks import PersistentColorTask

device  = BrainFlowDevice.CreateMuse2Device()
device.connect()

task = PersistentColorTask(3, 5, "green", "blue", 200, inter_stim_time=300)

k = KeyWave(device, task, PreprocessingPipeline(), BandpowerModel(), TemplateDatabase(), bounded_cosine_similarity, .75)

k.enroll("Hari Seldon")

if k.authenticate("Hari Seldon"):
    print("User authenticated")
```

### Integration into applications
An example of how to use the package, or more specific KeyWave, can be integrated into an application can be found in the form of the [Foundation Password Manager](https://github.com/markus-ro/fpm).

# References
[1] O. E. Krigolson, C. C. Williams, A. Norton, C. D. Hassall, and F. L. Colino, “Choosing MUSE: Validation of a Low-Cost, Portable EEG System for ERP Research,” Front. Neurosci., vol. 11, Mar. 2017, doi: 10.3389/fnins.2017.00109.
