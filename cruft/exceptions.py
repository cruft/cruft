"""Contains all custom exceptions raised by cruft"""
from pathlib import Path
from typing import Union


class CruftError(Exception):
    """The base exception for any error originating from the cruft project"""


class UnableToFindCookiecutterTemplate(CruftError):
    """Raised when Cruft is unable to find a cookiecutter template"""

    def __init__(self, directory: Union[str, Path]):
        if not isinstance(directory, str):
            directory = str(directory)
        super().__init__(self, f"Was unable to locate a Cookiecutter template in `{directory}` !")
        self.directory = directory


class NoCruftFound(CruftError):
    """Raised when no .cruft.json state is found in the current directory"""

    def __init__(self, directory: Union[str, Path]):
        if not isinstance(directory, str):
            directory = str(directory)
        super().__init__(
            self, f"Was unable to locate a `.cruft.json` state file in `{directory}` !"
        )
        self.directory = directory


class CruftAlreadyPresent(CruftError):
    """Raised when there is an attempt to create a new .cruft.json file but one already exists"""

    def __init__(self, file_location: Union[str, Path]):
        if not isinstance(file_location, str):
            file_location = str(file_location)
        super().__init__(self, f"`.cruft.json` is already defined at `{file_location}` !")
        self.file_location = file_location


class InvalidCookiecutterRepository(CruftError):
    """Raised when an invalid cookiecutter repository is provided"""

    pass
