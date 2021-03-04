
import logging.config

import yaml

# Read the logger configuration from a config file
with open('logging.yaml', 'r') as lf:
    log_cfg = yaml.safe_load(lf.read())
logging.config.dictConfig(log_cfg)

import gmsh.discord


def load_modules():
    import gmsh.discord.commands
    import gmsh.discord.database
    import gmsh.discord.knife
    import gmsh.discord.dcsings
    import gmsh.discord.determination

    gmsh.discord.commands.load()


load_modules()
gmsh.discord.start()