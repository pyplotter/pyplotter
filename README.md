# Plotter

A data browser and vizualizer for QCoDes database.


## Getting Started

Simply launch the plotter.py file to launch the software:

```
python plotter.py
```

Once the software is launched, you access the main window:

![main 01](doc/main_01.png)

The top left corner allows you to browse the dataserver and reached your database file, the bottom left corner displays the runs saved in your database, the top right shows the dependent parameters saved during your runs and the bottom right the meta-data associated with a run.
Once you have find your database and run and have clicked on it, you get this window:

![main 02](doc/main_02.png)

To plot your data you check the available checkbox and get a 1D plot window

![1D plot](doc/plot_1d_01.png)

or a 2D one

![2D plot](doc/plot_2d_01.png)

Plot windows allow live interaction.


## Installing

The easiest way is to clone the repository

```
git clone https://gitlab.com/edumur/plotter
```

You need QCodes to be installed and also the following libraries:

```
conda install pyqtgraph pandas matplotlib lmfit
```

## Authors

* **Etienne Dumur**


## License

Surely free but I have to chose one.