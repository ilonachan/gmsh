import logging.config
import yaml

#
# Logger Configuration
#
with open('logging.yaml', 'r') as lf:
    log_cfg = yaml.safe_load(lf.read())
logging.config.dictConfig(log_cfg)

import gmsh_terminal.features.dpyserver
from gmsh_terminal import *

load_all_features()

gmsh_terminal.features.dpyserver.start()

unload_all_features()
