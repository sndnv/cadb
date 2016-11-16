import os


def get_graph_path(graphs_path, sources_path, graph_name, requested_file=None):
    """
    Generates a graph file path, based on the supplied parameters.

    :param graphs_path: the configured graphs directory path
    :param sources_path: the sources base directory path
    :param graph_name: the base graph name
    :param requested_file: the specific source file for which graph is generated(default is None)
    :return: the generated graph path
    """
    if requested_file is None:
        graph_subname = "full"
    else:
        graph_subname = requested_file.replace(sources_path, '').replace(os.path.sep, "_")

    graph_path = "{0}{1}{2}_{3}.dot".format(
        graphs_path,
        os.path.sep,
        graph_name,
        graph_subname
    )

    return graph_path


def normalize_node_name(node_name):
    """
    Processes OS-specific path-based node names to have them display consistently, regardless of OS.

    :param node_name: the OS-specific node name
    :return: the normalized node name
    """
    return node_name.replace(os.path.sep, "/")
