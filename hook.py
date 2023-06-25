import os
import sys

# os.environ['PROJ_LIB'] = os.path.dirname(sys.argv[0]) + r"\Library\share\proj"
# os.environ['GDAL_DRIVER_PATH'] = os.path.dirname(sys.argv[0]) + r"\Library\lib\gdalplugins"
# os.environ['GDAL_DATA'] = os.path.dirname(sys.argv[0]) + r"\Library\share\gdal"
os.environ['PROJ_LIB'] = r".\Library\share\proj"
os.environ['GDAL_DRIVER_PATH'] = r".\Library\lib\gdalplugins"
os.environ['GDAL_DATA'] = r".\Library\share\gdal"
