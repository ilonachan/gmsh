import os
import sys

import gmsh_terminal.features.dpyserver
import logging.config
import yaml
import importlib.util
from os.path import isfile, join, abspath, basename, splitext
from os import listdir

#
# Logger Configuration
#
with open('logging.yaml', 'r') as lf:
    log_cfg = yaml.safe_load(lf.read())
logging.config.dictConfig(log_cfg)

log = logging.getLogger(__name__)


#
# features
#
feature_list = []


def load_feature(name):
    """
    Load the feature from the python file at the specified location

    :param name: the name of the feature
    """
    module_name = f'gmsh_terminal.features.{name}'

    if module_name in sys.modules:
        module = sys.modules[module_name]
        if hasattr(module, 'load_feature'):
            module.load_feature(None)
        feature_list.append(module)
        return

    dirpath = os.path.dirname(__file__)+'/features';

    # do the python magic boogie-woogie
    if isfile(f'{dirpath}/{name}.py'):
        spec = importlib.util.spec_from_file_location(module_name, abspath(f'{dirpath}/{name}.py'))
    else:
        spec = importlib.util.spec_from_file_location(module_name, abspath(f'{dirpath}/{name}/__init__.py'))
    module = importlib.util.module_from_spec(spec)
    if module_name in sys.modules:
        old_module = sys.modules[module_name]
    else:
        old_module = None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if hasattr(module, 'load_feature'):
        module.load_feature(old_module)

    feature_list.append(module)


def unload_feature(name):
    module_name = f'gmsh_terminal.features.{name}'
    global feature_list
    # TODO: There has to be a better way!
    new_features = []
    for f in feature_list:
        if f.__name__ == module_name:
            if hasattr(f, 'unload_feature'):
                f.unload_feature()
        else:
            new_features.append(f)
    feature_list = new_features


def load_all_features():
    cmd_base = os.path.dirname(__file__)+'/features'
    for file in [join(cmd_base, f) for f in listdir(cmd_base)]:
        if isfile(file):
            file = splitext(file)[0]
        if basename(file).startswith('__'):
            continue
        load_feature(basename(file))
        log.info(f'Loaded feature from module {file}')


def unload_all_features():
    for feature in feature_list:
        if hasattr(feature, 'unload_feature'):
            feature.unload_feature()


if __name__ == '__main__':
    load_all_features()

    gmsh_terminal.features.dpyserver.start()

    unload_all_features()
