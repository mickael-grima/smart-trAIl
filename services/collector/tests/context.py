from __future__ import absolute_import

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "src")))


# import packages
import scrapers
import models
import database
import controller
import main
import utils
