# cadb - C++ Auto-Discover Build

### Usage
    cadb <actions>      [options]
    cadb clean          --build <build name>
    cadb clean,build    --build <build name>
    cadb clean,build    --build <build name> [--source-file <path>] [--config-data <data>] [--config-file <path>]
    cadb interactive    --build <build name>
    cadb help

### Actions
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
    stats       <Not Implemented>
    help        Show this message.
    interactive <Not Implemented>

### Options
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

### Examples
    cadb clean          --build prod
    cadb build          --build prod
    cadb clean,build    --build prod
    cadb clean,build    --build dev --source-file "/home/myUser/repos/awesome_app/src/main/main.cpp"
    cadb build          --build dev --config-data "builds.dev.options.parallel=False,builds.dev.compiler.path=\"g++\""
    cadb build          --build dev --config-file "/home/myUser/repos/awesome_app/config/dev.conf"
    cadb help

### Notes
    - It is best not to use CTRL+C while a parallel build is being performed as keyboard interrupts are not handled
    correctly. Either wait until the compilation step is done or kill the processes manually.
