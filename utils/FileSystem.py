# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

from glob import glob
import json
import os


def get_source_files_list(sources_path, extensions):
    """
    Creates a list of source file paths, based on the supplied config.

    :param sources_path: the parent sources directory
    :param extensions: the extensions to be used for filtering the files in the sources dir
    :return: a list of source file paths
    """
    files = []
    for extension in extensions:
        files.extend(glob(sources_path + "/**/*." + extension, recursive=True))
    return files


def load_json_file(file_path):
    """
    Attempts to load a JSON file from the specified path.

    :param file_path: the file to be loaded
    :return: a dict representing the json data
    :raise: ValueError if an invalid path is supplied
    """
    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        raise ValueError("Invalid JSON file path specified: [" + file_path + "]")


def store_json_file(file_path, data):
    """
    Attempts to store the supplied data as a JSON file.

    :param file_path: the path to be used for the JSON file
    :param data: the data to be stored
    :return: nothing
    """
    with open(file_path, "w") as database:
        json.dump(data, database, indent=4, sort_keys=True)
