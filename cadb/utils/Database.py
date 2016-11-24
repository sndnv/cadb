# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

from cadb.utils.FileSystem import load_json_file, store_json_file


def load_files_db(database_path):
    """
    Loads a files database from the specified path.

    :param database_path: the file path to be used
    :return: the loaded database or an empty dict, if an issue occurs
    """
    try:
        return load_json_file(database_path)
    except ValueError:
        return {}


def store_files_db(database_path, data):
    """
    Stores the supplied data into a files database.

    :param database_path: the file path to be used for the database
    :param data: the data to be stored
    :return: nothing
    """
    return store_json_file(database_path, data)
