from labrad import types as T

class NoDatasetError(T.Error):
    """Please open a dataset first."""
    code = 2

class DatasetNotFoundError(T.Error):
    code = 3
    def __init__(self, name):
        self.msg = "Dataset '{0}' not found!".format(name)

class DirectoryExistsError(T.Error):
    code = 4
    def __init__(self, name):
        self.msg = "Directory '{0}' already exists!".format(name)

class DirectoryNotFoundError(T.Error):
    code = 5

class EmptyNameError(T.Error):
    """Names of directories or keys cannot be empty"""
    code = 6
    def __init__(self, path):
        self.msg = "Directory {0} does not exist!".format(path)

class ReadOnlyError(T.Error):
    """Points can only be added to datasets created with 'new'."""
    code = 7

class BadDataError(T.Error):
    code = 8
    def __init__(self, varcount, gotcount):
        self.msg = "Dataset requires {0} values per datapoint not {1}.".format(varcount, gotcount)

class BadParameterError(T.Error):
    code = 9
    def __init__(self, name):
        self.msg = "Parameter '{0}' not found.".format(name)

class ParameterInUseError(T.Error):
    code = 10
    def __init__(self, name):
        self.msg = "Already a parameter called '{0}'.".format(name)

class DataVersionMismatchError(T.Error):
    code = 11
    def __init__(self):
        self.msg = "Dataset was created with newer API, cannot be read.  Use get_ex"
