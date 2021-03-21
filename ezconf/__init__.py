import yaml
import logging
import os
import re

log = logging.getLogger(__name__)


class PathChainer:
    def __init__(self, parent, name=None, attr_access=False):
        self.__dict__['_name'] = name
        self.__dict__['_parent'] = parent
        self.__dict__['_attr_access'] = attr_access

    def __repr__(self):
        _, joined = self.__follow_path__(*self.__trace_path__())
        return f"PathChainer {joined}"

    def __getattr__(self, name):
        return PathChainer(self, name, attr_access=True)

    def __setattr__(self, key, value):
        root, path_components = PathChainer(self, key, attr_access=True).__trace_path__()

        cursor, _ = self.__follow_path__(root, path_components, create_if_missing=True)

        name, _ = path_components[-1]
        cursor[name] = value
        return

    def __getitem__(self, name):
        return PathChainer(self, name)

    def __setitem__(self, key, value):
        root, path_components = PathChainer(self, key, attr_access=False).__trace_path__()

        cursor, _ = self.__follow_path__(root, path_components, create_if_missing=True)

        name, _ = path_components[-1]
        cursor[name] = value
        return

    def __call__(self, *args, **kwargs):
        root, path_components = self.__trace_path__()

        try:
            cursor, joined = self.__follow_path__(root, path_components)
            if cursor == None:
                return root._parent

            name, attr_access = path_components[-1]

            if name not in cursor:
                raise KeyError(joined)
            return cursor[name]
        except KeyError:
            if 'default' in kwargs:
                return kwargs['default']
            if len(args) > 0:
                return args[0]
            raise

    def exists(self):
        try:
            self()
            return True
        except KeyError:
            return False

    def __trace_path__(self):
        newpath = []
        current = self
        while isinstance(current._parent, PathChainer):
            newpath.insert(0, (current._name, current._attr_access))
            current = current._parent
        return current, newpath

    @staticmethod
    def __follow_path__(root, path_components, create_if_missing=False):
        joined = root._name
        cursor = root._parent
        for name, attr_access in path_components[:-1]:
            joined += f'.{name}' if attr_access else f'[\'{name}\']'
            if name not in cursor:
                if create_if_missing:
                    cursor[name] = {}
                else:
                    raise KeyError(joined)
            cursor = cursor[name]
            if type(cursor) not in [dict, list]:
                raise TypeError(f'{joined}: not a dict or list')
        if len(path_components) > 0:
            name, attr_access = path_components[-1]
            joined += f'.{name}' if attr_access else f'[\'{name}\']'
            return cursor, joined
        return None, joined


cfg = PathChainer({}, 'cfg')


def merge_dicts(base, new):
    result = {**base}
    for key in new:
        if type(new[key]) == dict and key in base and type(base[key]) == dict:
            result[key] = merge_dicts(base[key], new[key])
        result[key] = new[key]
    return result


def from_dict(content):
    cfg.__dict__['_parent'] = merge_dicts(cfg._parent, content)


def from_env_var(key, env_var):
    if env_var in os.environ:
        cfg[key] = os.environ[env_var]


def map2dict(mapping, source=os.environ):
    result = {}
    for key in mapping:
        if type(mapping[key]) is str and mapping[key] in source:
            result[key] = source[mapping[key]]
        if type(mapping[key]) is dict:
            result[key] = map2dict(mapping[key], source=source)
    return result


def from_env_mapping(mapping):
    from_dict(map2dict(mapping))


def from_file(path, type='yaml'):
    try:
        if type == 'yaml':
            with open(path, 'r') as lf:
                file_content = yaml.safe_load(lf.read())
            from_dict(file_content)
        else:
            log.warning(f'Config file type "{type}" not implemented: skipping file "{path}"')
    except Exception:
        log.error(f'Failed to read "{path}" as a config file of type "{type}"')
        raise


def from_directory(path, type=None, filter=r'.*\.yaml'):
    log.info(f'Reading config from directory {path}')
    for f in os.listdir(path):
        t = type or 'yaml'
        p = os.path.join(path, f)
        if not re.match(filter, p):
            continue
        if os.path.isfile(p):
            from_file(p, type=t)
        if os.path.isdir(p):
            from_directory(p, type)
