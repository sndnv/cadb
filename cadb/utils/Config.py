# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

from ast import literal_eval
from cadb.utils.FileSystem import load_json_file


def load_from_file(config_path):
    """
    Loads the specified configuration file.

    :param config_path: the path to the configuration file to be loaded
    :return: a dict representing the configuration
    """
    return load_json_file(config_path)


def parse_from_string(config_pair):
    """
    Parses the specified configuration string.

    Converts a string (in the format 'a.b.c=123') into a nested dict (in the format {'a': {'b': {'c': 123}}}).

    Note: The value in the string (after the equals sign) is treated as a literal, therefore strings need to be quoted;
    for example: 'a.b.c="some string"'.

    :param config_pair: the configuration string to be parsed
    :return: a dict representing the configuration
    """
    key, value = config_pair.split("=")
    value = literal_eval(value)
    current_config_keys = key.split('.')[::-1]
    last_config_value = {current_config_keys[0]: value}
    for current_config_subkey in current_config_keys[1:]:
        last_config_value = {current_config_subkey: last_config_value}
    return last_config_value


def merge(target_config, other_config):
    """
    Merges the supplied 'other' configuration dict in the specified target configuration dict.

    :param target_config: the target config to merge into
    :param other_config: the config to be merged
    :return: nothing (the target config is modified)
    """
    for key, value in other_config.items():
        if key not in target_config or not isinstance(value, dict):
            target_config[key] = value
        else:
            merge(target_config[key], other_config[key])
