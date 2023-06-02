# NeuroPack

[![License](https://img.shields.io/badge/License-BSD_3--Clause-green.svg)](https://opensource.org/licenses/BSD-3-Clause) [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)]() [![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/) [![status: experimental](https://github.com/GIScience/badges/raw/master/status/experimental.svg)](https://github.com/GIScience/badges#experimental)

Simple library to implement prototypes of brainwave-based authentication in Python. Further, it allows for the general usage of brainwave data in Python. I wrote this library as part of my master thesis. At the time of submission, the future of it was uncertain. Hence, I decided to publish it and provide some missing features. If you come across this library and find it useful, feel free to use it and contribute if you like.

## Installation
To use NeuroPack, simply clone the repository and install the needed dependencies via pip:
```
playsound==1.2.2
play_sounds
scipy
matplotlib
statsmodels
brainflow
numpy
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

## Todo
The following list contains features I am planning to implement in the future:
- [ ] Broader data file support
- [X] AudioTask truly multi platform
- [X] Invisible AudioTask
- [X] Live plotting of EEG data
- [X] Optimize wear detection performance
- [ ] Support for multiple event markers
- [ ] Support for more EEG devices
- [X] Improve repo structure
- [X] Support for more elaborate artifact rejection
- [ ] Tests for artifact rejection
- [ ] Support for classifiers
- [ ] Representation learning based on siamese networks
- [ ] Change graphics backend of tasks
- [ ] Benchmarking framework
- [X] More examples

# References
[1] O. E. Krigolson, C. C. Williams, A. Norton, C. D. Hassall, and F. L. Colino, “Choosing MUSE: Validation of a Low-Cost, Portable EEG System for ERP Research,” Front. Neurosci., vol. 11, Mar. 2017, doi: 10.3389/fnins.2017.00109.