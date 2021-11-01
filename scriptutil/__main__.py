from shutil import copy
from os.path import dirname, join

copy(join(dirname(__file__), "_requirements.py"), "requirements.py")
