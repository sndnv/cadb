#!/usr/bin/env python3

# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

from data import Processing
from utils import Config, Database, Build, Graph, Stats, Interactive
from utils.Types import SourceType
from getopt import getopt, GetoptError
from datetime import datetime
import multiprocessing
import logging
import signal
import sys

usageMessage = """
C++ Auto-Discover Build

Usage:
    cadb <actions>      [options]
    cadb clean          --build <build name>
    cadb clean,build    --build <build name>
    cadb clean,build    --build <build name> [--source-file <path>] [--config-data <data>] [--config-file <path>]
    cadb interactive    --build <build name> [--source-file <path>] [--config-data <data>] [--config-file <path>]
    cadb help

Actions:
    Multiple actions can be specified by separating them with commas (without whitespace). They are executed in the
    order that they have been entered.

    build       If '--source-file' is NOT specified, compile all files that have changed since the last build and link
                them into an executable. If '--source-file' is specified, compile only that file; no linking is done.
    clean       If '--source-file' is NOT specified, remove all object files and the target executable, if they exist.
                If '--source-file' is specified, remove only that file.
    deps        If '--source-file' is NOT specified, generate a dependency table for all sources. If '--source-file' is
                specified, generate a dependency table only for that file.
    graph       If '--source-file' is NOT specified, generate a Graphviz '.dot' file representing the dependencies of
                all sources. If '--source-file' is specified, generate a Graphviz '.dot' file only for that source.
    stats       Show information about all source files ('--source-file' value is ignored).
    help        Show this message.
    interactive Starts an interactive session; '--source-file' is passed to the session as part of the 'options' dict
                and can be used by any of the available commands (run 'help' or 'help <command>' in the interactive
                session to see more information).

Options:
    The options can be specified in any order, with each one directly followed by its value (separated by whitespace).

    --build         <build name>    (required)  Specifies the build configuration name to be used (as defined in the
                                                configuration file/data).
    --source-file   <path>          (optional)  Sets the source file with which to work (see each action for more
                                                information on how they use this option).
    --config-data   <data>          (optional)  Sets additional config data to be merged with what is set in the
                                                config file. This data overrides any option coming from the file.
                                                The format of each piece of configuration data is: 'a.b.c=123'.
                                                That will create a nested map with the following structure:
                                                {'a': {'b': {'c': 123}}}. Multiple piece of data can be separated with
                                                commas: 'a.b=123,a.c="d"' (resulting in {'a': {'b': 123, 'c': 'd'}}).
    --config-file   <path>          (optional)  Sets the configuration file to be used (default: './config/core.conf').

Examples:
    cadb clean          --build prod
    cadb build          --build prod
    cadb clean,build    --build prod
    cadb clean,build    --build dev --source-file "/home/myUser/repos/awesome_app/src/main/main.cpp"
    cadb build          --build dev --config-data "builds.dev.options.parallel=False,builds.dev.compiler.path=\"g++\""
    cadb build          --build dev --config-file "/home/myUser/repos/awesome_app/config/dev.conf"
    cadb help

Notes:
    - The options '--config-data' and '--config-file' are only used for building the final config object and are then
    stripped from the 'options' dict.
    - It is best not to use CTRL+C while a parallel build is being performed as keyboard interrupts are not handled
    correctly. Either wait until the compilation step is done or kill the processes manually.
"""


def build_action(config, options, db, sources, logger):
    build_config = config['builds'][options['build']]
    general_options = build_config['options']
    compiler_config = build_config['compiler']
    linker_config = build_config['linker']

    # runs pre-compile commands
    pre_compile_commands = build_config['pre']['compile']
    if len(pre_compile_commands) > 0:
        logger.info(
            "Running [{0}] pre-compile command(s) ...".format(len(pre_compile_commands)),
            extra={'action': 'build'}
        )
        for current_command in pre_compile_commands:
            Build.process_external_command(current_command, logger)
    else:
        logger.info("No pre-compile commands defined", extra={'action': 'build'})

    # gathers sources for re-build
    rebuild_sources = []
    if 'source-file' in options:
        requested_file = options['source-file']
        if requested_file in sources:
            requested_source = sources[requested_file]
            if requested_source.file_type == SourceType.Implementation:
                rebuild_sources = [requested_source]
            else:
                raise ValueError(
                    "Failed to compile single source file [{0}]; type [{1}] is not supported".format(
                        requested_file,
                        requested_source.file_type
                    )
                )
    else:
        for source in sources.values():
            if source.file_type == SourceType.Implementation:
                object_file_exists = Build.object_file_exists(source.object_file_path)

                if source.has_changed or not object_file_exists:
                    rebuild_sources.append(source)
                else:
                    for c in source.internal_dependencies:
                        current_dependency = sources[c]
                        if current_dependency.has_changed:
                            rebuild_sources.append(source)
                            break
            elif source.file_type == SourceType.Header:
                db[source.file_path] = source.file_hash
            else:
                raise ValueError(
                    "Unexpected source type encountered: [{0}] for file [{1}]".format(
                        source.file_type,
                        source.file_path
                    )
                )

    build_failed = False

    def process_compilation_result(source_data, result):
        return_code, stdout, stderr = result

        if len(stdout) > 0:
            logger.info("[{0}]: {1}".format(source_data.file_path, stdout), extra={'action': 'build'})

        if len(stderr) > 0:
            logger.error("[{0}]: {1}".format(source_data.file_path, stderr), extra={'action': 'build'})

        if return_code is 0:
            logger.info(
                "... compilation completed successfully for file [{0}]".format(
                    source_data.file_path
                ),
                extra={'action': 'build'}
            )

            db[source_data.file_path] = source_data.file_hash
        else:
            logger.error(
                "... compilation failed with return code [{0}] for file [{1}]".format(
                    return_code,
                    source_data.file_path
                ),
                extra={'action': 'build'}
            )

            nonlocal build_failed
            build_failed = True

    # builds sources
    if len(rebuild_sources) > 0:
        if general_options.get('parallel', False) is True:
            # does a parallel build
            logger.info(
                "Starting parallel build with [{0}] processes for [{1}] out of [{2}] source files ...".format(
                    multiprocessing.cpu_count(),
                    len(rebuild_sources),
                    len(sources)
                ),
                extra={'action': 'build'}
            )

            pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
            for source in rebuild_sources:
                Build.remove_object_file(source.object_file_path)
                Build.create_object_file_dir(source.object_file_path)
                pool.apply_async(
                    Build.compile_object,
                    args=(source, compiler_config),
                    callback=lambda result, captured_source=source: process_compilation_result(captured_source, result)
                )

            pool.close()
            pool.join()
        else:
            # does a sequential build
            logger.info(
                "Starting sequential build for [{1}] out of [{2}] source files ...".format(
                    multiprocessing.cpu_count(),
                    len(rebuild_sources),
                    len(sources)
                ),
                extra={'action': 'build'}
            )

            for source in rebuild_sources:
                Build.remove_object_file(source.object_file_path)
                Build.create_object_file_dir(source.object_file_path)
                compile_result = Build.compile_object(source, compiler_config)
                process_compilation_result(source, compile_result)
                if build_failed:
                    break

        Database.store_files_db(config['builds'][options['build']]['paths']['database'], db)
    else:
        logger.info("No new or updated sources found ...", extra={'action': 'build'})

    if build_failed:
        logger.error("... build failed.", extra={'action': 'build'})
    else:
        # run post-compile commands
        post_compile_commands = build_config['post']['compile']
        if len(post_compile_commands) > 0:
            logger.info(
                "... running [{0}] post-compile command(s) ...".format(len(post_compile_commands)),
                extra={'action': 'build'}
            )

            for current_command in post_compile_commands:
                Build.process_external_command(current_command, logger)
        else:
            logger.info("... no post-compile commands defined ...", extra={'action': 'build'})

        if 'source-file' not in options:
            # runs pre-link commands
            pre_link_commands = build_config['pre']['link']
            if len(pre_link_commands) > 0:
                logger.info(
                    "... running [{0}] pre-link command(s) ...".format(len(pre_link_commands)),
                    extra={'action': 'build'}
                )

                for current_command in pre_link_commands:
                    Build.process_external_command(current_command, logger)
            else:
                logger.info("... no pre-link commands defined ...", extra={'action': 'build'})

            Build.link_objects(sources, linker_config, logger)

            # run post-link commands
            post_link_commands = build_config['post']['link']
            if len(post_link_commands) > 0:
                logger.info(
                    "... running [{0}] post-link command(s) ...".format(len(post_link_commands)),
                    extra={'action': 'build'}
                )
                for current_command in post_link_commands:
                    Build.process_external_command(current_command, logger)
            else:
                logger.info("... no post-link commands defined ...", extra={'action': 'build'})
        else:
            logger.info("... single file compilation requested; linking skipped ...", extra={'action': 'build'})

        logger.info("... build completed.", extra={'action': 'build'})


def clean_action(config, options, _, sources, logger):
    target_object_files = []

    if 'source-file' in options:
        requested_file = options['source-file']
        if requested_file in sources:
            source = sources[requested_file]
            if source.file_type == SourceType.Implementation and Build.object_file_exists(source.object_file_path):
                target_object_files.append(source.object_file_path)
    else:
        for source in sources.values():
            if source.file_type == SourceType.Implementation and Build.object_file_exists(source.object_file_path):
                target_object_files.append(source.object_file_path)

    if len(target_object_files) > 0:
        logger.info(
            "Removing [{0}] object files ...".format(len(target_object_files)),
            extra={'action': 'clean'}
        )

        for current_file in target_object_files:
            Build.remove_object_file(current_file)
            logger.info("... removed object file [{0}]".format(current_file), extra={'action': 'clean'})

        logger.info("... done.", extra={'action': 'clean'})
    else:
        logger.info("No object files found", extra={'action': 'clean'})

    output_file = config['builds'][options['build']]['linker']['output']['name']
    if Build.object_file_exists(output_file):
        logger.info(
            "Removing output file [{0}] ...".format(output_file),
            extra={'action': 'clean'}
        )

        Build.remove_object_file(output_file)

        logger.info("... done.", extra={'action': 'clean'})
    else:
        logger.info("No output file found", extra={'action': 'clean'})


def deps_action(config, options, _, sources, logger):
    try:
        from terminaltables import AsciiTable
    except ImportError:
        logger.error(
            "Package 'terminaltables 3.1.0' is required (see https://github.com/Robpol86/terminaltables)!",
            extra={'action': 'deps'}
        )
        return

    if 'source-file' in options:
        requested_file = options['source-file']
    else:
        requested_file = None

    sources_dir = config['builds'][options['build']]['paths']['sources']

    internal_dependencies, external_dependencies = Processing.process_dependencies(sources, requested_file)
    data = [("Dependency", "Type", "Used By")]

    internal_dependencies_list = list(internal_dependencies.keys())
    internal_dependencies_list.sort()
    for dependency_path in internal_dependencies_list:
        name = dependency_path.replace(sources_dir, '~')
        sources_names = []

        for current_source in internal_dependencies[dependency_path]:
            sources_names.append(current_source.file_path.replace(sources_dir, '~'))

        sources_names.sort()
        data.append((name, "Internal", "\n".join(sources_names)))

    external_dependencies_list = list(external_dependencies.keys())
    external_dependencies_list.sort()
    for dependency_path in external_dependencies_list:
        sources_names = []

        for current_source in external_dependencies[dependency_path]:
            sources_names.append(current_source.file_path.replace(sources_dir, '~'))

        sources_names.sort()
        data.append((dependency_path, "External", "\n".join(sources_names)))

    table = AsciiTable(data)
    table.inner_row_border = True
    logger.info(
        "\n{0}".format(table.table),
        extra={'action': 'deps'}
    )


def graph_action(config, options, _, sources, logger):
    try:
        import networkx
    except ImportError:
        logger.error(
            "Package 'networkx 1.11' is required (see https://github.com/networkx/networkx)!",
            extra={'action': 'graph'}
        )
        return

    try:
        import pydotplus
    except ImportError:
        logger.error(
            "Package 'pydotplus 2.0.2' is required (see https://github.com/carlos-jenkins/pydotplus)!",
            extra={'action': 'graph'}
        )
        return

    if 'source-file' in options:
        requested_file = options['source-file']
    else:
        requested_file = None

    sources_dir = config['builds'][options['build']]['paths']['sources']
    graphs_dir = config['builds'][options['build']]['paths']['graphs']

    internal_dependencies, external_dependencies = Processing.process_dependencies(sources, requested_file)
    graph = networkx.MultiDiGraph()

    for dependency_path, dependency_sources in internal_dependencies.items():
        name = Graph.normalize_node_name(dependency_path.replace(sources_dir, '~'))

        for current_source in dependency_sources:
            current_source_name = current_source.file_path.replace(sources_dir, '~')
            graph.add_edge(
                Graph.normalize_node_name(name),
                Graph.normalize_node_name(current_source_name)
            )

    for dependency_path, dependency_sources in external_dependencies.items():
        for current_source in dependency_sources:
            current_source_name = current_source.file_path.replace(sources_dir, '~')
            graph.add_edge(
                Graph.normalize_node_name(dependency_path),
                Graph.normalize_node_name(current_source_name)
            )

    from networkx.drawing import nx_pydot
    graph_path = Graph.get_graph_path(graphs_dir, sources_dir, "deps_graph", requested_file)
    nx_pydot.write_dot(graph, graph_path)
    logger.info(
        "Graph file generated: [{0}]".format(graph_path),
        extra={'action': 'graph'}
    )


def stats_action(config, options, _, sources, logger):
    try:
        from terminaltables import AsciiTable
    except ImportError:
        logger.error(
            "Package 'terminaltables 3.1.0' is required (see https://github.com/Robpol86/terminaltables)!",
            extra={'action': 'stats'}
        )
        return

    sources_dir = config['builds'][options['build']]['paths']['sources']
    internal_dependencies, external_dependencies = Processing.process_dependencies(sources)

    total_lines_count = 0
    total_files_count = 0
    total_files_size = 0

    header_files_count = 0
    implementation_files_count = 0

    header_files_by_size = []
    implementation_files_by_size = []

    header_files_by_deps_count = []
    implementation_files_by_deps_count = []

    for current_source in sources.values():
        total_lines_count += current_source.total_lines
        total_files_size += current_source.size
        total_files_count += 1

        if current_source.file_type == SourceType.Header:
            header_files_count += 1
            header_files_by_size.append(current_source)
            header_files_by_deps_count.append(current_source)
        elif current_source.file_type == SourceType.Implementation:
            implementation_files_count += 1
            implementation_files_by_size.append(current_source)
            implementation_files_by_deps_count.append(current_source)

    mean_file_size = total_files_size / total_files_count
    mean_lines_count = total_lines_count / total_files_count
    header_files_by_size.sort(key=lambda current: current.size)
    implementation_files_by_size.sort(key=lambda current: current.size)

    header_files_by_deps_count.sort(
        key=lambda current: len(current.internal_dependencies) + len(current.external_dependencies)
    )

    implementation_files_by_deps_count.sort(
        key=lambda current: len(current.internal_dependencies) + len(current.external_dependencies)
    )

    internal_deps_count = len(internal_dependencies)
    external_deps_count = len(external_dependencies)

    internal_deps_by_use_count = sorted(
        internal_dependencies.keys(),
        key=lambda current: len(internal_dependencies[current])
    )

    external_deps_by_use_count = sorted(
        external_dependencies.keys(),
        key=lambda current: len(external_dependencies[current])
    )

    main_data = []
    main_data.extend(Stats.get_header_files_size_data(sources_dir, header_files_by_size, 10))
    main_data.extend(Stats.get_implementation_files_size_data(sources_dir, implementation_files_by_size, 10))
    main_data.extend(Stats.get_header_files_deps_data(sources_dir, header_files_by_deps_count, 10))
    main_data.extend(Stats.get_implementation_files_deps_data(sources_dir, implementation_files_by_deps_count, 10))
    main_data.extend(Stats.get_internal_deps_data(sources_dir, internal_deps_by_use_count, internal_dependencies, 10))
    main_data.extend(Stats.get_external_deps_data(external_deps_by_use_count, external_dependencies, 10))

    main_table = AsciiTable(main_data)
    main_table.inner_heading_row_border = False

    misc_table = AsciiTable(
        [
            ("Lines of Code", "{0:,}".format(total_lines_count)),
            ("Average Lines of Code", "{0:,.0f}".format(mean_lines_count)),
            ("Files", "{0:,}".format(total_files_count)),
            ("Files Size", "{0:.2f} KB".format(total_files_size / 1024)),
            ("Average File Size", "{0:.2f} KB".format(mean_file_size / 1024)),
            ("Header Files", "{0:,}".format(header_files_count)),
            ("Implementation Files", "{0:,}".format(implementation_files_count)),
            ("Internal Dependencies", "{0:,}".format(internal_deps_count)),
            ("External Dependencies", "{0:,}".format(external_deps_count))
        ]
    )
    misc_table.inner_heading_row_border = False

    logger.info(
        "\n{0}\n{1}".format(
            main_table.table,
            misc_table.table
        ),
        extra={'action': 'stats'}
    )


def help_action(*_):
    print(usageMessage)


def interactive_action(config, options, db, sources, logger):
    session = Interactive.InteractiveSession(available_actions, config, options, db, sources, logger)

    logger.info(
        "Started interactive session with ID [{0}] ...".format(session.id),
        extra={'action': 'interactive'}
    )

    session.cmdloop()

    logger.info(
        "... session with ID [{0}] closed.".format(session.id),
        extra={'action': 'interactive'}
    )


available_actions = {
    'build': build_action,
    'clean': clean_action,
    'deps': deps_action,
    'graph': graph_action,
    'stats': stats_action,
    'help': help_action,
    'interactive': interactive_action
}


def get_command_input():
    if len(sys.argv) == 2 and sys.argv[1] == 'help':
        help_action()
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Error: Not enough arguments supplied.")
        print(usageMessage)
        sys.exit(2)

    actions = sys.argv[1].split(',')
    for currentAction in actions:
        if currentAction not in available_actions:
            print("Error: Action [" + currentAction + "] is not supported.")
            print(usageMessage)
            sys.exit(2)

    options = {}
    try:
        opts, _ = getopt(sys.argv[2:], '', ['build=', 'source-file=', 'config-data=', 'config-file='])
        for currentOpt in opts:
            options[currentOpt[0].replace('--', '')] = currentOpt[1]
    except GetoptError as e:
        print("Error: " + e.msg)
        print(usageMessage)
        sys.exit(2)

    if 'build' not in options:
        print("Error: '--build' is a required option.")
        print(usageMessage)
        sys.exit(2)

    return actions, options


def get_config(options=None):
    config = Config.load_from_file(options.get('config-file', "config/core.conf"))

    if options is not None and 'config-data' in options:
        for currentConfigOption in options['config-data'].split(','):
            current_config = Config.parse_from_string(currentConfigOption)
            Config.merge(config, current_config)

    return config


def main():
    # gathers all config and data
    actions, options = get_command_input()
    config = get_config(options)
    options.pop('config-data', None)
    options.pop('config-file', None)
    db = Database.load_files_db(config['builds'][options['build']]['paths']['database'])
    sources = Processing.process_sources(config, options, db)

    # configures logging
    logging_options = config['builds'][options['build']]['options']['logging']
    logger = logging.getLogger(name="logger")
    formatter = logging.Formatter('%(asctime)s | %(action)s | %(levelname)s > %(message)s')
    logger.setLevel(logging.getLevelName(logging_options['level'].upper()))
    logger.propagate = False

    logging_target = logging_options['target']
    if logging_target == 'file':
        if logging_options['append'] is True:
            file_mode = 'a'
        else:
            file_mode = 'w'

        logger_handler = logging.FileHandler(logging_options['path'], mode=file_mode)
        logger_handler.setFormatter(formatter)
    elif logging_target == 'console':
        logger_handler = logging.StreamHandler()
        logger_handler.setFormatter(formatter)
    else:
        raise ValueError("Invalid logging target encountered: [{0}] in config".format(logging_target))

    logger.addHandler(logger_handler)

    # executes all actions
    for currentAction in actions:
        action_start = datetime.now()
        available_actions[currentAction](config, options, db, sources, logger)
        action_end = datetime.now()
        logger.info(
            "Action completed in [{0:.2f}] seconds".format((action_end - action_start).total_seconds()),
            extra={'action': currentAction}
        )

    logger_handler.close()


def interrupt_handler(*_):
    print("Terminating ...")
    print()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_handler)
    main()
