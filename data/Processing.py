# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

from data.SourceFile import SourceFile
from utils import FileSystem, Build
from utils.Types import SourceType


def process_sources(config, options, db):
    """
    Builds a dict of source files and their data, based on the supplied configuration.

    :param config: the config to be used for processing
    :param options: all user-supplied options
    :param db: data loaded from the database, if any
    :return: a dict containing all source files data
    """
    build_config = config['builds'][options['build']]
    sources_dir = build_config['paths']['sources']
    excludes = build_config['paths']['excludes']
    build_dir = build_config['paths']['build']
    header_file_extensions = build_config['headerFileExtensions']
    implementation_file_extensions = build_config['implementationFileExtensions']

    header_files = FileSystem.get_source_files_list(sources_dir, header_file_extensions)
    implementation_files = FileSystem.get_source_files_list(sources_dir, implementation_file_extensions)

    sources = {}
    for current_file in header_files:
        if not any(current_file.startswith(current_exclude) for current_exclude in excludes):
            source_file = SourceFile(
                includes_config=config['includes'],
                path=current_file,
                file_type=SourceType.Header,
                db_hash=db.get(current_file),
                object_file_path=None
            )

            sources[current_file] = source_file

    for current_file in implementation_files:
        if not any(current_file.startswith(current_exclude) for current_exclude in excludes):
            source_file = SourceFile(
                includes_config=config['includes'],
                path=current_file,
                file_type=SourceType.Implementation,
                db_hash=db.get(current_file),
                object_file_path=Build.get_object_file_path(current_file, sources_dir, build_dir)
            )

            sources[current_file] = source_file

    return sources


def process_dependencies(sources, requested_file=None):
    """
    Builds two dicts containing all internal and external dependencies based on the supplied sources data.

    :param sources: a dict of the processed source files
    :param requested_file: a path to a specific file that is needed, if any (default is None)
    :return: (internal dependencies dict, external dependencies dict)
    """
    internal_dependencies = {}
    external_dependencies = {}

    if requested_file is not None:
        if requested_file in sources:
            sources = {requested_file: sources[requested_file]}
        else:
            sources = {}

    for source in sources.values():
        for current_internal_dependency in source.internal_dependencies:
            if current_internal_dependency in internal_dependencies:
                internal_dependencies[current_internal_dependency].append(source)
            else:
                internal_dependencies[current_internal_dependency] = [source]

        for current_external_dependency in source.external_dependencies:
            if current_external_dependency in external_dependencies:
                external_dependencies[current_external_dependency].append(source)
            else:
                external_dependencies[current_external_dependency] = [source]

    return internal_dependencies, external_dependencies
