def get_header_files_size_data(sources_dir, header_files_by_size, rows_count):
    """
    Builds table rows list containing data about header files sizes (largest/smallest).

    :param sources_dir: configured sources directory
    :param header_files_by_size: list of header files ordered by size (smallest to largest)
    :param rows_count: number of rows to build
    :return: the requested table rows
    """
    data = [
        ("-------------------", "----", "--------------------", "----"),
        ("Largest Header File", "Size", "Smallest Header File", "Size"),
        ("-------------------", "----", "--------------------", "----")
    ]

    largest_headers = header_files_by_size[-rows_count:]
    largest_headers.reverse()
    smallest_headers = header_files_by_size[:rows_count]
    for n in range(0, rows_count):
        top = largest_headers[n] if len(largest_headers) > n else None
        bottom = smallest_headers[n] if len(smallest_headers) > n else None

        data.append(
            (
                top.file_path.replace(sources_dir, '~') if top is not None else "-",
                "{0:.2f} KB".format(top.size / 1024) if top is not None else "-",
                bottom.file_path.replace(sources_dir, '~') if bottom is not None else "-",
                "{0:.2f} KB".format(bottom.size / 1024) if bottom is not None else "-"
            )
        )

    return data


def get_implementation_files_size_data(sources_dir, implementation_files_by_size, rows_count):
    """
    Builds table rows list containing data about implementation files sizes (largest/smallest).

    :param sources_dir: configured sources directory
    :param implementation_files_by_size: list of implementation files ordered by size (smallest to largest)
    :param rows_count: number of rows to build
    :return: the requested table rows
    """
    data = [
        ("---------------------------", "----", "----------------------------", "----"),
        ("Largest Implementation File", "Size", "Smallest Implementation File", "Size"),
        ("---------------------------", "----", "----------------------------", "----")
    ]

    largest_implementations = implementation_files_by_size[-rows_count:]
    largest_implementations.reverse()
    smallest_implementations = implementation_files_by_size[:rows_count]
    for n in range(0, rows_count):
        top = largest_implementations[n] if len(largest_implementations) > n else None
        bottom = smallest_implementations[n] if len(smallest_implementations) > n else None

        data.append(
            (
                top.file_path.replace(sources_dir, '~') if top is not None else "-",
                "{0:.2f} KB".format(top.size / 1024) if top is not None else "-",
                bottom.file_path.replace(sources_dir, '~') if bottom is not None else "-",
                "{0:.2f} KB".format(bottom.size / 1024) if bottom is not None else "-"
            )
        )

    return data


def get_header_files_deps_data(sources_dir, header_files_by_deps_count, rows_count):
    """
    Builds table rows list containing data about header files dependency counts (most/least).

    :param sources_dir: configured sources directory
    :param header_files_by_deps_count: list of header files ordered by dependency count (least to most)
    :param rows_count: number of rows to build
    :return: the requested table rows
    """
    data = [
        ("-----------------------------", "-----", "------------------------------", "-----"),
        ("Most Dependencies Header File", "Count", "Least Dependencies Header File", "Count"),
        ("-----------------------------", "-----", "------------------------------", "-----")
    ]

    most_deps_headers = header_files_by_deps_count[-rows_count:]
    most_deps_headers.reverse()
    least_deps_headers = header_files_by_deps_count[:rows_count]
    for n in range(0, rows_count):
        top = most_deps_headers[n] if len(most_deps_headers) > n else None
        bottom = least_deps_headers[n] if len(least_deps_headers) > n else None

        if top is not None:
            top_count = (len(top.internal_dependencies) + len(top.external_dependencies))
        else:
            top_count = "-"

        if bottom is not None:
            bottom_count = (len(bottom.internal_dependencies) + len(bottom.external_dependencies))
        else:
            bottom_count = "-"

        data.append(
            (
                top.file_path.replace(sources_dir, '~') if top is not None else "-",
                top_count,
                bottom.file_path.replace(sources_dir, '~') if bottom is not None else "-",
                bottom_count
            )
        )

    return data


def get_implementation_files_deps_data(sources_dir, implementation_files_by_deps_count, rows_count):
    """
    Builds table rows list containing data about implementation files dependency counts (most/least).

    :param sources_dir: configured sources directory
    :param implementation_files_by_deps_count: list of implementation files ordered by dependency count (least to most)
    :param rows_count: number of rows to build
    :return: the requested table rows
    """
    data = [
        ("---------------------------", "-----", "----------------------------", "-----"),
        ("Most Dependencies Impl File", "Count", "Least Dependencies Impl File", "Count"),
        ("---------------------------", "-----", "----------------------------", "-----")
    ]

    most_deps_implementations = implementation_files_by_deps_count[-rows_count:]
    most_deps_implementations.reverse()
    least_deps_implementations = implementation_files_by_deps_count[:rows_count]
    for n in range(0, rows_count):
        top = most_deps_implementations[n] if len(most_deps_implementations) > n else None
        bottom = least_deps_implementations[n] if len(least_deps_implementations) > n else None

        if top is not None:
            top_count = (
                len(top.internal_dependencies) + len(top.external_dependencies)
            )
        else:
            top_count = "-"

        if bottom is not None:
            bottom_count = (
                len(bottom.internal_dependencies) + len(bottom.external_dependencies)
            )
        else:
            bottom_count = "-"

        data.append(
            (
                top.file_path.replace(sources_dir, '~') if top is not None else "-",
                top_count,
                bottom.file_path.replace(sources_dir, '~') if bottom is not None else "-",
                bottom_count
            )
        )

    return data


def get_internal_deps_data(sources_dir, internal_deps_by_use_count, internal_dependencies, rows_count):
    """
    Builds table rows list containing data about internal dependency use counts (most/least).

    :param sources_dir: configured sources directory
    :param internal_deps_by_use_count: list of internal dependencies by use count (least to most)
    :param internal_dependencies: dict with all internal dependencies
    :param rows_count: number of rows to build
    :return: the requested table rows
    """
    data = [
        ("-----------------------------", "-----", "------------------------------", "-----"),
        ("Most Used Internal Dependency", "Count", "Least Used Internal Dependency", "Count"),
        ("-----------------------------", "-----", "------------------------------", "-----")
    ]

    most_used_deps = internal_deps_by_use_count[-rows_count:]
    most_used_deps.reverse()
    least_used_deps = internal_deps_by_use_count[:rows_count]
    for n in range(0, rows_count):
        top = most_used_deps[n] if len(most_used_deps) > n else None
        bottom = least_used_deps[n] if len(least_used_deps) > n else None

        data.append(
            (
                top.replace(sources_dir, '~') if top is not None else "-",
                len(internal_dependencies[top]) if top is not None else "-",
                bottom.replace(sources_dir, '~') if bottom is not None else "-",
                len(internal_dependencies[bottom]) if bottom is not None else "-"
            )
        )

    return data


def get_external_deps_data(external_deps_by_use_count, external_dependencies, rows_count):
    """
    Builds table rows list containing data about external dependency use counts (most/least).

    :param external_deps_by_use_count: list of external dependencies by use count (least to most)
    :param external_dependencies: dict with all external dependencies
    :param rows_count: number of rows to build
    :return: the requested table rows
    """
    data = [
        ("-----------------------------", "-----", "------------------------------", "-----"),
        ("Most Used External Dependency", "Count", "Least Used External Dependency", "Count"),
        ("-----------------------------", "-----", "------------------------------", "-----")
    ]

    most_used_deps = external_deps_by_use_count[-rows_count:]
    most_used_deps.reverse()
    least_used_deps = external_deps_by_use_count[:rows_count]
    for n in range(0, rows_count):
        top = most_used_deps[n] if len(most_used_deps) > n else None
        bottom = least_used_deps[n] if len(least_used_deps) > n else None

        data.append(
            (
                top if top is not None else "-",
                len(external_dependencies[top]) if top is not None else "-",
                bottom if bottom is not None else "-",
                len(external_dependencies[bottom]) if bottom is not None else "-"
            )
        )

    return data
