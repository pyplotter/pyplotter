# This Python file uses the following encoding: utf-8
from setuptools import setup, find_packages

setup(name='plotter',
      version='0.1.0',
      use_2to3=False,
      author='Étienne Dumur',
      author_emal='etienne.dumur@gmail.com',
      maintainer='Étienne Dumur',
      maintainer_email='etienne.dumur@gmail.com',
      description='A data browser and vizualizer for QCoDes database, csv, s2p and BlueFors logging files.',
      long_description=open('README.md').read(),
      classifiers=[
        'Programming Language :: Python :: 3',
        'Intended Audience :: Science/Research'
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering'
      ],
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'qcodes>=0.26.0',
          'qdarkstyle',
          'lmfit',
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
              'plotter = plotter.plotter:main',
          ]
       })
