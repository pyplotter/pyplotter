# This Python file uses the following encoding: utf-8
from setuptools import setup, find_packages

setup(name='pyplotter',
      version='0.3.0',
      author='Étienne Dumur',
      author_email='etienne.dumur@cea.fr',
      maintainer='Étienne Dumur',
      maintainer_email='etienne.dumur@cea.fr',
      description='A data browser and vizualizer for QCoDes database, csv, s2p and BlueFors logging files.',
      url='https://github.com/pyplotter/pyplotter',
      long_description=open('README.md', encoding="utf8").read(),
      classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering'
      ],
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'qdarkstyle',
          'lmfit',
          'multiprocess',
          'numpy>=1.17.0',
          'pandas>=1.0.0',
          'pyopengl',
          'pyqt5',
          'pyqt5-sip',
          'pyqtgraph>=0.12.3',
          'scikit-rf',
          'scipy',
      ],
      entry_points={
          'console_scripts':[
              'plotter = pyplotter.pyplotter:main',
              'pyplotter = pyplotter.pyplotter:main',
          ]
       })
