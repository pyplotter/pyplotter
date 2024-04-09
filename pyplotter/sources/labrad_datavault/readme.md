## [Dataset of labrad is defined as per the doc](https://github.com/labrad/servers/blob/master/datavault/dataset_format.txt)
HDF datasets are stored in the following fashion

HDF5 root:
    Attribute: 'Version' = [2,0,0] for extended, [1,0,0] for standard
    datasets: 'DataVault' = All data and parameters for a single dataset
        Simple datasets: 1-D array of (f,f,f, ...) cluster -- one float per column
        Extended datasets: 1-D array of structs matching the column types

        attributes:
            'Title':                  Dataset title
            'Access Time':            Access time (stored as float64)  
            'Modification Time':      Modification time
            'Creation Time':          Creation time
            'Comments':               1-D array of comments, type is (float64, vstr, vstr) == (timestamp, username, comment)

          for each param Foo (by name):
            'Param.Foo':              value stored as urlencoded flattened data

          for each independent variable X (by index):
            'IndependentX.label':     string (label)
            'IndependentX.shape:      n-d array of int
            'IndependentX.datatype':  [istvc]
            'IndependentX.unit':      'ns' -- only if type is c or v

          for each dependent variable Y (by index):
            'DependentX.legend':     string (legend)
            'DependentX.label':      string (label)
            'DependentX.shape':      n-d array of int
            'DependentX.datatype':   [istvc]
            'DependentX.unit':       'ns' -- only if type is c or v


## change hdf5 file open to read only, and swmr=True
    def open_hdf5_file(filename):
        """Factory for HDF5 files.  

        We check the version of the file to construct the proper class.  Currently, only two
        options exist: version 2.0.0 -> legacy format, 3.0.0 -> extended format.
        Version 1 is reserved for CSV files.
        """
        fh = SelfClosingFile(h5py.File, open_args=(filename, 'a'))
        version = fh().attrs['Version']
        if version[0] == 2:
            return SimpleHDF5Data(fh)
        else:
            return ExtendedHDF5Data(fh)
