import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from lifehjb.model import load_params

CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "config.yaml")


@pytest.fixture(scope="session")
def params():
    return load_params(CONFIG)
