cadb - C/C++ Auto-Discover Build
================================

The tool is intended to be a 'make' replacement for building C/C++ projects of low to medium complexity. See the `How it works`_ section to determine if it's the right tool for your project.

This readme includes the following sections: `Motivation`_ , Requirements_, Install_, Build_, Usage_, Actions_, Options_, Examples_, Notes_, Configuration_ and `How it works`_.

Motivation
~~~~~~~~~~

::

    - Simple replacement for 'make' that's easier to configure and deal with
    - Updating makefiles can be tedious, especially if there is no IDE to help
    - IDEs can can create makefiles that are not usable on any system other than the developer's
    - Timestamps are not reliable for determining if a file has changed
    - 'make' can get confused about what has or hasn't changed, resulting in frustrating compile/runtime errors
    - Checking external dependencies (std, boost, whathaveyou ...) for changes is almost never necessary

Requirements
~~~~~~~~~~~~

::

    - Python            3.5
    - networkx          1.11  (for action 'graph')
    - pydotplus         2.0.2 (for action 'graph')
    - terminaltables    3.1.0 (for actions 'stats' and 'deps')

If one or more of the dependencies are missing, only the actions that require them will not be available.

Install
~~~~~~~

Download
    The latest .whl file can be found in `releases <https://github.com/sndnv/cadb/releases>`_.

Install
    *pip install <path to .whl file>*

    OR

    *python -m pip install <path to .whl file>*

Build
~~~~~

- Clone repo
- Go to repo root
- Build Wheel

Example
^^^^^^^

::

    cd /home/myUser/repos
    git clone https://github.com/sndnv/cadb.git
    cd cadb
    python setup.py bdist_wheel
    pip install ./dist/cadb-<version>-py3-none-any.whl


Usage
~~~~~

::

    cadb <actions>      [options]
    cadb clean          --build <build name>
    cadb clean,build    --build <build name>
    cadb clean,build    --build <build name> [--source-file <path>] [--config-data <data>] [--config-file <path>]
    cadb interactive    --build <build name> [--source-file <path>] [--config-data <data>] [--config-file <path>]
    cadb help

Actions
~~~~~~~

::

    Multiple actions can be specified by separating them with commas (without whitespace). They are executed in the
    order that they have been entered.

    build       If '--source-file' is NOT specified, compile all files that have changed since the last build and
                link them into an executable. If '--source-file' is specified, compile only that file; no linking
                is done.
    clean       If '--source-file' is NOT specified, remove all object files and the target executable, if they exist.
                If '--source-file' is specified, remove only that file.
    deps        If '--source-file' is NOT specified, generate a dependency table for all sources. If '--source-file'
                is specified, generate a dependency table only for that file.
    graph       If '--source-file' is NOT specified, generate a Graphviz '.dot' file representing the dependencies
                of all sources. If '--source-file' is specified, generate a Graphviz '.dot' file only for that
                source.
    stats       Show information about all source files ('--source-file' value is ignored).
    help        Show this message.
    interactive Starts an interactive session; '--source-file' is passed to the session as part of the 'options'
                dict and can be used by any of the available commands (run 'help' or 'help <command>' in the
                interactive session to see more information).

Options
~~~~~~~

::

    The options can be specified in any order, with each one directly followed by its value (separated by whitespace).

    --build         <build name>    (required)  Specifies the build configuration name to be used (as defined in the
                                                configuration file/data).
    --source-file   <path>          (optional)  Sets the source file with which to work (see each action for more
                                                information on how they use this option).
    --config-data   <data>          (optional)  Sets additional config data to be merged with what is set in the
                                                config file. This data overrides any option coming from the file.
                                                The format of each piece of configuration data is: 'a.b.c=123'.
                                                That will create a nested map with the following structure:
                                                {'a': {'b': {'c': 123}}}
                                                Multiple pieces of data can be separated with commas:
                                                'a.b=123,a.c="d"' (resulting in {'a': {'b': 123, 'c': 'd'}}).
    --config-file   <path>          (optional)  Sets the configuration file to be used; default is:
                                                './config/core.conf'.

Examples
~~~~~~~~

::

    cadb clean          --build prod
    cadb build          --build prod
    cadb clean,build    --build prod
    cadb clean,build    --build dev --source-file "/home/myUser/repos/awesome_app/src/main/main.cpp"
    cadb build          --build dev --config-data "builds.dev.options.parallel=False,name=\"test_name\""
    cadb build          --build dev --config-file "/home/myUser/repos/awesome_app/config/dev.conf"
    cadb help

Notes
~~~~~

::

    - The options '--config-data' and '--config-file' are only used for building the final config object and
    are then stripped from the 'options' dict.

    - It is best not to use CTRL+C while a parallel build is being performed as keyboard interrupts are not
    handled correctly. Either wait until the compilation step is done or kill the processes manually.

Configuration
~~~~~~~~~~~~~

The reference JSON config file can be found `here <https://github.com/sndnv/cadb/blob/master/config/reference.conf>`_.

Configuration Options
^^^^^^^^^^^^^^^^^^^^^
    **name** - project name (String)

    **version** - project version (String)

    **includes**

        **external**
            **start** - character(s) denoting start of external include (default is '<')

            **end** - character(s) denoting end of external include (default is '>')

            If the defaults are used, the line '#include <string>' will be considered an external dependency.

        **internal**
            **start** - character(s) denoting start of external include (default is '\\"')

            **end** - character(s) denoting end of external include (default is '\\"')

            If the defaults are used, the line '#include "string.h"' will be considered an internal dependency.

    **builds**

        **<user-defined build name>**
            **options** - general build options
                *parallel*
                    *- compile source files in parallel on sequentially (Boolean)*

                *logging* - logging options
                    *level* - one of 'critical', 'error', 'warning', 'info', 'debug' (String)

                    *target* - 'console' (for logging to stdout) or 'file' (String)

                    *path* - when 'target' == 'file', logs to the path specified (String)

                    *append* - when 'target' == 'file', denotes whether to append to or rewrite the log (Boolean)

            **compiler** - compiler options
                *path* - full path to C/C++ compiler binary

                *options* - list/array of options to be passed to the compiler for each invocation

            **linker** - linker options
                *path* - full path to linker binary

                *options* - list/array of options to be passed to the linker

            **headerFileExtensions**
                *- list of extensions that will determine which files are headers*

            **implementationFileExtensions**
                *- list of extensions that will determine which files are implementations*

            **paths** - various paths used by the tool
                *sources* - target directory for source files

                *exclude* - list of files and directories to exclude

                *build* - target directory for storing build output files

                *database* - target directory for storing the database file

                *graphs* - target directory for storing graph output files

            **pre**
                *compile* - commands to execute before starting file compilation

                *link* - commands to execute before starting object linking

            **post**
                *compile* - commands to execute after file compilation ends

                *link* - commands to execute after object linking ends

Configuration Notes
___________________

::

    - The 'pre' and 'post' commands are executed only once, before/after each stage
    is executed. For example, if 'n' number of files need to be compiled, the 'pre-compile'
    commands will be run only once, before compilation of those files starts and NOT 'n'
    number of times, before/after each file is compiled. Similarly, the 'post-compile'
    commands will be run once, after the compilation of all of the files completes.

    - Pre/post link commands will be executed only if linking is going to be performed.
    If one file is to be compiled (via the --source-file option), no linking will be done,
    therefore the pre/post link commands will not run. If no '--source-file' is specified,
    but only one file has changed and is to be compiled, linking will proceed as normal
    and the pre/post commands will be executed.

How it works
~~~~~~~~~~~~

::

    - Gathers all config and options
    - Loads the DB file (if any), containing the last source hashes
    - Processes all source files, splitting them into headers and implementations
    - For each source file a new hash is calculated and compared to the hash from the DB
    - Each action is executed, in the order specified when starting the script
        - 'clean' - removes all object files and/or linker output
        - 'build' - compiles all source files that have changed and links them:
            1) runs pre-compile commands
            2) compiles all applicable source files
            3) updates DB file
            4) runs post-compile commands
            5) runs pre-link commands (optional)
            6) links all object files (optional)
            7) runs post-link commands (optional)
        - 'deps' - builds a table showing all dependencies and the source files using them
        - 'graph' - creates a '.dot' graph file (for graphviz) representing all dependencies
        - 'stats' - compiles various stats for the project, such as number of lines, files,
                    file sizes, top 'n' number of dependencies/files based on usage, etc
        - 'interactive' - starts an interactive shell allowing the execution of all actions
                          without having to restart the script, plus some additional
                          functionality (sessions, autocompile, etc)

        Note: When a '--source-file' is specified, the behaviour of each action can change.
        See the description for each action for more info.

