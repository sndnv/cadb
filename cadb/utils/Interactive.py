# MIT License
# Copyright (c) 2016 https://github.com/sndnv
# See the project's LICENSE file for the full text

import multiprocessing
import os
import pprint
import time
from cmd import Cmd
from datetime import datetime
from time import localtime, strftime
from cadb.utils import Config, FileSystem, Types, Build
from cadb.data import Processing


def monitor_file(source_data, compiler_config, check_interval):
    """
    Starts monitoring the specified source file, compiling it when changes are detected.

    :param source_data: the data for the source file to be monitored
    :param compiler_config: the compiler configuration to be used
    :param check_interval: the time to wait between checks for changes; in seconds
    :return: nothing
    """
    try:
        last_hash = None
        while True:
            current_hash = FileSystem.get_file_hash(source_data.file_path)
            if current_hash != last_hash:
                print("Compiling file [{0}]".format(source_data.file_path))
                Build.remove_object_file(source_data.object_file_path)
                Build.create_object_file_dir(source_data.object_file_path)
                return_code, stdout, stderr = Build.compile_object(source_data, compiler_config)

                if len(stdout) > 0:
                    print("stdout for [{0}]: {1}".format(source_data.file_path, stdout))

                if len(stderr) > 0:
                    print("stderr for [{0}]: {1}".format(source_data.file_path, stderr))

                if return_code is 0:
                    print("Compilation completed successfully for file [{0}]".format(source_data.file_path))
                else:
                    print(
                        "*** Compilation failed with return code [{0}] for file [{1}]".format(
                            return_code,
                            source_data.file_path
                        )
                    )
                last_hash = current_hash

            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("Stopping 'autocompile' for [{0}] ...".format(source_data.file_path))


class InteractiveSession(Cmd):
    intro = "Type 'help' to see a list of commands or 'qq' to exit"
    prompt = ">: "

    def __init__(self, available_actions, initial_config, initial_options, initial_db, initial_sources, logger,
                 completekey='tab', stdin=None, stdout=None):
        """
        Creates a new interactive session with the supplied parameters.

        Notes:\n
        - The session needs to be started via a call to the 'cmdloop()' method.\n
        - The process will block (while handling user commands) until the session is terminated.\n
        - Any changes made to 'config' and 'options' in the session will be kept and used for any actions running
          after the session has ended.

        :param available_actions:
        :param initial_config: the current config object
        :param initial_options: the current options object
        :param initial_db: the current DB object
        :param initial_sources: the current sources data
        :param logger: the core logger object
        :param completekey: completion key (default is 'tab'); see 'cmd.Cmd'
        :param stdin: input file object (default is None); see 'cmd.Cmd'
        :param stdout: output file object (default is None); see 'cmd.Cmd'
        """
        super().__init__(completekey, stdin, stdout)
        self.id = strftime("%Y%m%d_%H%M%S", localtime())
        self.actions = available_actions
        self.config = initial_config
        self.options = initial_options
        self.db = initial_db
        self.sources = initial_sources
        self.logger = logger
        self.pp = pprint.PrettyPrinter(indent=2)
        self._autocompile_processes = {}
        self._command_history = {'current': [], 'previous': []}

    def emptyline(self):
        pass

    @staticmethod
    def help_config():
        print("Gets or sets the system config:")
        print("\t>: config get -> retrieves the current system config")
        print("\t>: config set a.b.c=\"some value\" -> merges the specified config path into the system config")

    def do_config(self, args):
        if len(args) > 0:
            args = args.split(" ", maxsplit=1)
            command = args[0]

            if command == "set":
                try:
                    new_config = Config.parse_from_string(args[1])
                    Config.merge(self.config, new_config)
                    self.sources = Processing.process_sources(self.config, self.options, self.db)
                    print("Done!")
                except Exception as e:
                    print("*** Exception encountered while processing new config: [({0}) {1}]".format(e.__class__, e))
            elif command == "get":
                self.pp.pprint(self.config)
            else:
                print("*** Unexpected command for 'config': [{0}]".format(command))
        else:
            print("*** 'config' expects more parameters")

    @staticmethod
    def help_options():
        print("Gets or (un)sets the system options:")
        print("\t>: options get -> retrieves the current system config")
        print("\t>: options set abc 123 -> sets the specified option (abc) to the specified value (123) as a string")
        print("\t>: options unset abc -> removes the specified option (abc)")

    def do_options(self, args):
        if len(args) > 0:
            args = args.split(" ", maxsplit=2)
            command = args[0]

            if command == "set":
                try:
                    self.options[args[1]] = args[2]
                    self.sources = Processing.process_sources(self.config, self.options, self.db)
                    print("Done!")
                except Exception as e:
                    print("*** Exception encountered while processing new options: [({0}) {1}]".format(e.__class__, e))
            elif command == "unset":
                self.options.pop(args[1], None)
                self.sources = Processing.process_sources(self.config, self.options, self.db)
                print("Done!")
            elif command == "get":
                self.pp.pprint(self.options)
            else:
                print("*** Unexpected command for 'options': [{0}]".format(command))
        else:
            print("*** 'options' expects more parameters")

    @staticmethod
    def help_autocompile():
        print("Gets, starts or stops auto-compile processes:")
        print("\t>: autocompile get -> lists all running auto-compile processes (if any)")
        print("\t>: autocompile start <file path> -> starts a process for the specified file (if not running already)")
        print("\t>: autocompile stop all -> stops all auto-compile processes (if any)")
        print("\t>: autocompile stop <file path> -> stops the process for the specified file (if started)")

    def do_autocompile(self, args):
        if len(args) > 0:
            args = args.split(" ", maxsplit=1)
            command = args[0]

            try:
                if command == "start":
                    source_file = args[1].replace('"', '').replace('\'', '')
                    if source_file in self._autocompile_processes:
                        print(
                            "*** A process [{0}] already exists for file [{1}]".format(
                                self._autocompile_processes[source_file].pid, source_file
                            )
                        )
                    else:
                        source_data = self.sources[source_file]
                        compiler_config = self.config['builds'][self.options['build']]['compiler']
                        if source_data.file_type == Types.SourceType.Implementation:
                            new_process = multiprocessing.Process(
                                target=monitor_file,
                                args=(source_data, compiler_config, 2)
                            )
                            new_process.start()
                            self._autocompile_processes[source_file] = new_process
                            print("Initializing ...")
                        else:
                            print("*** File [{0}] is not an implementation file".format(source_file))
                elif command == "stop":
                    source_file = args[1].replace('"', '').replace('\'', '')
                    if source_file == "all":
                        for current_process in self._autocompile_processes.values():
                            current_process.terminate()
                            current_process.join()
                        self._autocompile_processes.clear()
                    elif source_file not in self._autocompile_processes:
                        print("*** Process not found for file [{0}]".format(source_file))
                    else:
                        existing_process = self._autocompile_processes[source_file]
                        existing_process.terminate()
                        existing_process.join()
                        self._autocompile_processes.pop(source_file)
                        print("Done!")
                elif command == "get":
                    if len(self._autocompile_processes) > 0:
                        for source_file, process in self._autocompile_processes.items():
                            print(
                                "{0}\t->\tPID: {1}\t(Alive: {2})".format(
                                    source_file,
                                    process.pid,
                                    "Yes" if process.is_alive() else "No"
                                )
                            )
                    else:
                        print("No processes found")
                else:
                    print("*** Unexpected command for 'autocompile': [{0}]".format(command))
            except Exception as e:
                print(
                    "*** Exception encountered while processing action 'autocompile': [({0}) {1}]".format(
                        e.__class__,
                        e
                    )
                )
        else:
            print("*** 'autocompile' expects more parameters")

    @staticmethod
    def help_session():
        print("Gets, saves or loads interactive session configs:")
        print("\t>: session get -> lists all available session configs in the build dir (if any)")
        print("\t>: session save -> saves the current session config in the build dir")
        print("\t>: session load <file path> -> loads the session config from the specified path")

    def do_session(self, args):
        if len(args) > 0:
            args = args.split(" ", maxsplit=1)
            command = args[0]
            build_dir = self.config['builds'][self.options['build']]['paths']['build']

            try:
                if command == "save":
                    config = self.config.copy()
                    Config.merge(
                        config,
                        {
                            'session_options': self.options,
                            'command_history': self._command_history['current']
                        }
                    )
                    FileSystem.store_json_file("{0}{1}session_{2}.conf".format(build_dir, os.sep, self.id), config)
                    print("Done!")
                elif command == "load":
                    session_config = FileSystem.load_json_file(args[1])
                    session_options = session_config.pop('session_options')
                    command_history = session_config.pop('command_history')
                    self.config = session_config
                    self.options = session_options
                    self._command_history['previous'] = command_history
                    self.sources = Processing.process_sources(self.config, self.options, self.db)
                    print("Done!")
                elif command == "get":
                    saved_sessions = FileSystem.get_session_files_list(build_dir)
                    saved_sessions.sort()
                    if len(saved_sessions) > 0:
                        for current_session in saved_sessions:
                            print(current_session)
                    else:
                        print("No saved sessions found")
                else:
                    print("*** Unexpected command for 'session': [{0}]".format(command))
            except Exception as e:
                print(
                    "*** Exception encountered while processing action 'session': [({0}) {1}]".format(
                        e.__class__,
                        e
                    )
                )
        else:
            print("*** 'session' expects more parameters")

    @staticmethod
    def help_build():
        print("Executes the 'build' action:")
        print("\t>: build -> do action with current config, options and sources")
        print("\t>: build <file path> -> do action for specified source only (replaces 'source-file' in options)")
        print("\t>: build all -> do action for all sources (ignores 'source-file' in options)")

    def do_build(self, args):
        if len(self._autocompile_processes) > 0:
            print("*** Cannot start a build while there are active auto-compile processes")
        else:
            try:
                source_file = args.replace('"', '').replace('\'', '') if len(args) > 0 else None
                if source_file is None:
                    self._run_timed_action('build')
                else:
                    options = self.options.copy()
                    if source_file.lower() == "all":
                        options.pop("source-file")
                    else:
                        options["source-file"] = source_file
                    self._run_timed_action('build', with_options=options)
                self.sources = Processing.process_sources(self.config, self.options, self.db)
            except Exception as e:
                print(
                    "*** Exception encountered while processing action 'build': [({0}) {1}]".format(
                        e.__class__,
                        e
                    )
                )

    @staticmethod
    def help_clean():
        print("Executes the 'clean' action:")
        print("\t>: clean -> do action with current config, options and sources")
        print("\t>: clean <file path> -> do action for specified source only (replaces 'source-file' in options)")
        print("\t>: clean all -> do action for all sources (ignores 'source-file' in options)")

    def do_clean(self, args):
        if len(self._autocompile_processes) > 0:
            print("*** Cannot start a build while there are active auto-compile processes")
        else:
            try:
                source_file = args.replace('"', '').replace('\'', '') if len(args) > 0 else None
                if source_file is None:
                    self._run_timed_action('clean')
                else:
                    options = self.options.copy()
                    if source_file.lower() == "all":
                        options.pop("source-file")
                    else:
                        options["source-file"] = source_file
                    self._run_timed_action('clean', with_options=options)
                self.sources = Processing.process_sources(self.config, self.options, self.db)
            except Exception as e:
                print(
                    "*** Exception encountered while processing action 'clean': [({0}) {1}]".format(
                        e.__class__,
                        e
                    )
                )

    @staticmethod
    def help_deps():
        print("Executes the 'deps' action with the current config, options and sources.")

    def do_deps(self, _):
        try:
            self._run_timed_action('deps')
        except Exception as e:
            print(
                "*** Exception encountered while processing action 'deps': [({0}) {1}]".format(
                    e.__class__,
                    e
                )
            )

    @staticmethod
    def help_graph():
        print("Executes the 'graph' action with the current config, options and sources.")

    def do_graph(self, _):
        try:
            self._run_timed_action('graph')
        except Exception as e:
            print(
                "*** Exception encountered while processing action 'graph': [({0}) {1}]".format(
                    e.__class__,
                    e
                )
            )

    @staticmethod
    def help_stats():
        print("Executes the 'stats' action with the current config, options and sources.")

    def do_stats(self, _):
        try:
            self._run_timed_action('stats')
        except Exception as e:
            print(
                "*** Exception encountered while processing action 'stats': [({0}) {1}]".format(
                    e.__class__,
                    e
                )
            )

    @staticmethod
    def help_sources():
        print("Gets or refreshes the available sources:")
        print("\t>: sources get [filter] -> retrieves a sorted list of source files; accepts an optional filter string")
        print("\t>: sources refresh -> performs sources processing with the current config and options")

    def do_sources(self, args):
        if len(args) > 0:
            args = args.split(" ", maxsplit=1)
            command = args[0]

            try:
                if command == "refresh":
                    self.sources = Processing.process_sources(self.config, self.options, self.db)
                    print("Done!")
                elif command == "get":
                    sources_filter = args[1].lower() if len(args) > 1 else None
                    sources = list(self.sources.keys())
                    if sources_filter is not None:
                        sources = [current for current in sources if sources_filter in current.lower()]
                    sources.sort()

                    for source_path in sources:
                        print(source_path)
                else:
                    print("*** Unexpected command for 'sources': [{0}]".format(command))
            except Exception as e:
                print(
                    "*** Exception encountered while processing action 'sources': [({0}) {1}]".format(
                        e.__class__,
                        e
                    )
                )
        else:
            print("*** 'sources' expects more parameters")

    @staticmethod
    def help_history():
        print("Gets or clears command histories:")
        print("\t>: history [current] -> retrieves the current session's command history")
        print("\t>: history previous -> retrieves the loaded session's command history (if any)")
        print("\t>: history clear -> clears the current session's command history")

    def do_history(self, args):
        if len(args) > 0:
            args = args.split(" ", maxsplit=1)
            command = args[0]

            if command == "previous":
                selected_history = self._command_history['previous']
            elif command == "current":
                selected_history = self._command_history['current']
            elif command == "clear":
                self._command_history['current'].clear()
                selected_history = []
            else:
                print("*** Unexpected command for 'history': [{0}]".format(command))
                selected_history = []
        else:
            selected_history = self._command_history['current']

        if len(selected_history) > 0:
            for index, command in enumerate(selected_history):
                print("[{0:03d}]\t[{1}]".format(index, command))
        else:
            print("No commands found")

    @staticmethod
    def help_qq():
        print("Exits the interactive session and allows any remaining actions to complete.")

    def do_qq(self, _):
        for current_process in self._autocompile_processes.values():
            current_process.terminate()
            current_process.join()
        self._autocompile_processes.clear()
        return True

    def precmd(self, line):
        if line and line.strip():
            self._command_history['current'].append(line.strip())
        return line

    def _run_timed_action(self, action, with_options=None):
        """
        Runs the specified action with the supplied options (or the default ones).

        :param action: the action to be run
        :param with_options: the options to use for the action (if not supplied, the default options are used)
        :return: nothing
        """
        action_start = datetime.now()
        options = with_options if with_options is not None else self.options
        self.actions[action](self.config, options, self.db, self.sources, self.logger)
        action_end = datetime.now()
        self.logger.info(
            "Action in session [{0}] completed in [{1:.2f}] seconds".format(
                self.id,
                (action_end - action_start).total_seconds()
            ),
            extra={'action': action}
        )
