import os

import pytest


@pytest.fixture()
def project_dir():
    yield os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
