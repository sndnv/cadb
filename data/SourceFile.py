import hashlib
import re
import os

READ_BUFFER_SIZE = 65536
PATTERN_DIRECTIVES = re.compile(r"^(#.+)")
PATTERN_INCLUDES = re.compile(r"^#include (.+)")


class SourceFile:
    def __init__(self, includes_config, path, file_type, db_hash=None, object_file_path=None):
        """
        Creates a new source file object.

        The file contents are hashed as part of this object's creation and all internal/external dependencies are
        gathered. The source file is marked as changed if the current hash does not match the hash provided by the
        database (if any).

        :param includes_config: JSON configuration object describing how to handle include directive parsing
        :param path: the file's full FS path
        :param file_type: the file's type (utils.Types.SourceType)
        :param db_hash: the previously calculated hash for the file, if any (default: None)
        :param object_file_path: the corresponding full object file path, if any (default: None)
        """
        self.file_path = path
        self.file_type = file_type
        self.object_file_path = object_file_path

        hasher = hashlib.sha256()
        with open(path, "rb") as currentFile:
            data = currentFile.read(READ_BUFFER_SIZE)
            while len(data) > 0:
                hasher.update(data)
                data = currentFile.read(READ_BUFFER_SIZE)
        self.file_hash = hasher.hexdigest()

        self.raw_directives = []
        self.external_dependencies = []
        self.internal_dependencies = []
        with open(path, "r") as currentFile:
            for currentLine in currentFile:
                for directive in PATTERN_DIRECTIVES.findall(currentLine):
                    self.raw_directives.append(directive)
                    for include in PATTERN_INCLUDES.findall(currentLine):
                        if include.startswith(includes_config['external']['start']) and include.endswith(
                                includes_config['external']['end']):
                            self.external_dependencies.append(include[1:-1])
                        elif include.startswith(includes_config['internal']['start']) and include.endswith(
                                includes_config['internal']['end']):
                            relative_path = include[1:-1]
                            file_dir = os.path.dirname(path)
                            absolute_path = os.path.normpath(file_dir + os.path.sep + relative_path)
                            self.internal_dependencies.append(absolute_path)

        self.has_changed = self.file_hash != db_hash
