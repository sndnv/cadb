# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

import os
import subprocess
from utils.Types import SourceType


def get_object_file_path(source_path, sources_dir, build_dir):
    """
    Creates an object file path, based on the supplied source file path.

    :param source_path: source file path
    :param sources_dir: sources directory path
    :param build_dir: build directory path
    :return: the calculated object file path
    """
    build_path = source_path.replace(sources_dir, build_dir)
    return os.path.splitext(build_path)[0] + ".o"


def object_file_exists(object_file_path):
    """
    Checks if the supplied object file path exists.

    :param object_file_path: the path to check
    :return: True, if the path is valid and exists
    """
    return object_file_path is not None and os.path.isfile(object_file_path)


def create_object_file_dir(object_file_path):
    """
    Creates the directory structure required for the specified object file.

    :param object_file_path: target object file path
    :return: nothing
    """
    os.makedirs(os.path.dirname(object_file_path), exist_ok=True)


def remove_object_file(object_file_path):
    """
    Removes the specified object file.

    Only the object file is removed, while keeping the directory structure.

    :param object_file_path: the path to the object file to be removed
    :return: nothing
    """
    if object_file_path is not None and os.path.isfile(object_file_path):
        os.remove(object_file_path)


def run_external_command(command):
    """
    Runs the supplied command in a new subprocess and waits for it to complete.

    :param command: the command to be run
    :return: a tuple: (command return code, messages sent to stdout, messages sent to stderr)
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    stdout, stderr = process.communicate()
    return_code = process.returncode

    return return_code, stdout, stderr


def compile_object(source, compiler_config):
    """
    Compiles the supplied source file using the specified compiler configuration.

    The command is run in a new subprocess and the function waits for it to complete.

    :param source: the source file object describing the object to be compiled
    :param compiler_config: the compiler configuration to be used
    :return: a tuple: (compilation command return code, messages sent to stdout, messages sent to stderr)
    """
    command = '{0} -o "{2.object_file_path}" {1} "{2.file_path}"'.format(
        compiler_config['path'],
        " ".join(compiler_config['options']),
        source
    )

    return run_external_command(command)


def link_objects(sources, linker_config, logger):
    """
    Links the supplied sources (after object files have been created) using the specified linker configuration.

    The linking command is run in a new subprocess and the function waits for it to complete.

    :param sources: the source file objects to be used for the linking process
    :param linker_config: the linker configuration to be used
    :param logger: the object used for logging linker messages
    :return: nothing
    :raise: RuntimeError if the linking process fails
    """
    object_files = []
    for source in sources.values():
        if source.file_type == SourceType.Implementation:
            object_files.append(source.object_file_path)

    output_file = linker_config['output']['name']

    command = "{0} -o \"{1}\" {2} {3}".format(
        linker_config['path'],
        output_file,
        " ".join(object_files),
        " ".join(linker_config['options'])
    )

    return_code, stdout, stderr = run_external_command(command)

    if len(stdout) > 0:
        logger.info("[{0}]: {1}".format(output_file, stdout), extra={'action': 'link_objects'})

    if len(stderr) > 0:
        logger.error("[{0}]: {1}".format(output_file, stderr), extra={'action': 'link_objects'})

    if return_code is 0:
        logger.info(
            "... linking completed successfully for file [{0}] ...".format(output_file),
            extra={'action': 'link_objects'}
        )
    else:
        message = "... linking failed with return code [{0}] for file [{1}] ...".format(return_code, output_file)
        logger.error(message, extra={'action': 'link_objects'})
        raise RuntimeError(message)


def process_external_command(command, logger):
    """
    Processes the specified external command.

    The command is run in a new subprocess and the function waits for it to complete.

    :param command: the command to be run and processed
    :param logger: the object used for logging command messages
    :return: nothing
    :raise: RuntimeError if the command fails
    """
    return_code, stdout, stderr = run_external_command(command)

    if len(stdout) > 0:
        logger.info("[{0}]: {1}".format(command, stdout), extra={'action': 'process_external_command'})

    if len(stderr) > 0:
        logger.error("[{0}]: {1}".format(command, stderr), extra={'action': 'process_external_command'})

    if return_code is 0:
        logger.info(
            "... command completed successfully: [{0}]".format(command),
            extra={'action': 'process_external_command'}
        )
    else:
        message = "... command failed with return code [{0}]: [{1}]".format(return_code, command)
        logger.error(message, extra={'action': 'process_external_command'})
        raise RuntimeError(message)
