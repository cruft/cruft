from pathlib import Path

from cruft import exceptions


def test_invalid_cookiecutter_repository():
    instance = exceptions.InvalidCookiecutterRepository(".")
    assert isinstance(instance, exceptions.CruftError)
    assert instance.cookiecutter_repo == "."


def test_unable_to_find_cookiecutter_template():
    instance = exceptions.UnableToFindCookiecutterTemplate(".")
    assert instance.directory == "."
    assert isinstance(instance, exceptions.CruftError)


def test_unable_to_find_cookiecutter_template_path():
    instance = exceptions.UnableToFindCookiecutterTemplate(Path("."))
    assert instance.directory == "."
    assert isinstance(instance, exceptions.CruftError)


def test_no_cruft():
    instance = exceptions.NoCruftFound(".")
    assert instance.directory == "."
    assert isinstance(instance, exceptions.CruftError)


def test_cruft_already_present():
    instance = exceptions.CruftAlreadyPresent(".")
    assert instance.file_location == "."
    assert isinstance(instance, exceptions.CruftError)
