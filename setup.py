from setuptools import find_packages, setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='neuropack',
    packages=find_packages(),
    version='1.0a3',
    license='BSD-3-Clause',
    description='Library to implement prototypes of brainwave-based authentication and to work with brainwaves in general',
    long_description=readme(),
    author='Markus Röse',
    author_email='mroese@mail.uni-paderborn.de',
    url='https://github.com/markus-ro/neuropack',
    download_url='https://github.com/markus-ro/neuropack/archive/refs/tags/1.0a3.tar.gz',
    keywords=[
        'EEG',
        'AUTHENTICATION'],
    install_requires=[
        'playsound==1.2.2',
        'play_sounds',
        'scipy',
        'matplotlib',
        'statsmodels',
        'brainflow',
        'numpy',
        "pyEDFlib"],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ])