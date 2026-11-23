import sys
import os
sys.path.append(os.path.abspath("backend"))

from app.modules.identity.models import User
from app.modules.farmer.models import Farmer
from app.modules.farm.models import Farm
from app.modules.crop_season.models import CropSeason

print("Imports successful")
