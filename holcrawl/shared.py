"""Shared resources for the Rotten Needles package."""

import os
import re
import json
import warnings
import functools

_HOMEDIR = os.path.expanduser("~")
_DEF_CFG_FILE_NAME = '.holcrawl_cfg.json'
_DEF_CFG_FILE_PATH = os.path.join(_HOMEDIR, _DEF_CFG_FILE_NAME)
_DEF_DATA_DIR_NAME = 'holcrawl_data'
_DEF_DATA_DIR_PATH = os.path.join(_HOMEDIR, _DEF_DATA_DIR_NAME)


# === configuration ===

@functools.lru_cache(maxsize=2)
def _get_cfg():
    try:
        with open(_DEF_CFG_FILE_PATH, 'r') as cfg_file:
            return json.load(cfg_file)
    except FileNotFoundError:
        return {}
    except Exception:  # pylint: disable=W0703
        warnings.warn(
            "Reading {} failed. Ignoring user configuration.".format(
                _DEF_CFG_FILE_NAME))
        return {}


def print_cfg():
    """Prints the current configuration of holcrawl to screen."""
    print(_get_cfg())


class _CfgKey(object):
    DATADIR = 'data_dir'


def set_data_dir_path(dir_path):
    """Sets the a directory path as the path of holcrawl's data directory."""
    current_cfg = _get_cfg()
    current_cfg[_CfgKey.DATADIR] = dir_path
    with open(_DEF_CFG_FILE_PATH, 'w+') as cfg_file:
        json.dump(current_cfg, cfg_file)


def _get_data_dir_path():
    try:
        return _get_cfg()[_CfgKey.DATADIR]
    except KeyError:
        return _DEF_DATA_DIR_PATH


_UNITED_PROF_DIR_NAME = 'united_profiles'

def _get_united_dir_path():
    return os.path.join(_get_data_dir_path(), _UNITED_PROF_DIR_NAME)


_IMDB_PROF_DIR_NAME = 'imdb_profiles'

def _get_imdb_dir_path():
    return os.path.join(_get_data_dir_path(), _IMDB_PROF_DIR_NAME)


_WIKI_LISTS_DIR_NAME = 'wiki_lists'

def _get_wiki_dir_path():
    return os.path.join(_get_data_dir_path(), _WIKI_LISTS_DIR_NAME)


def _get_wiki_list_file_path(year):
    return os.path.join(_get_wiki_dir_path(), '{}_titles.txt'.format(year))


_METACRITIC_PROF_DIR_NAME = 'metacritic_profiles'

def _get_metacritic_dir_path():
    return os.path.join(_get_data_dir_path(), _METACRITIC_PROF_DIR_NAME)


_DATASET_DIR_NAME = 'datasets'

def _get_dataset_dir_path():
    return os.path.join(_get_data_dir_path(), _DATASET_DIR_NAME)


# === utilities ===

def clear_empty_profiles():
    """Clears all empty profiles in the profile directories."""
    print("Clearing empty movie profiles...")
    for dir_path in [
            _get_imdb_dir_path(), _get_metacritic_dir_path()]:
        if not os.path.exists(dir_path):
            continue
        for profile_file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, profile_file)
            with open(file_path, 'r') as json_file:
                if sum(1 for line in json_file) < 1:
                    os.remove(file_path)

class _result:
    SUCCESS = 'succeeded'
    FAILURE = 'failed'
    EXIST = 'already exist'
    ALL_TYPES = [SUCCESS, FAILURE, EXIST]


def _file_length(file_path):
    length = 0
    with open(file_path, 'r') as movies_file:
        length = sum(1 for _ in movies_file)
    return length


def _titles_from_file(file_path):
    with open(file_path, 'r') as titles_file:
        return [line.strip() for line in titles_file]


def _parse_string(string):
    return string.lower().strip().replace(' ', '_')


_CHARS_TO_REMOVE = r"[\:\;,\.'/\!\?]"

def _parse_name_for_file_name(movie_name):
    parsed = re.sub(_CHARS_TO_REMOVE, '', movie_name)
    return parsed.replace(' ', '_').lower()
