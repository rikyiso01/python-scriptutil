from shutil import copy, copytree, move, rmtree
from os.path import exists, isdir, basename, join
from os import listdir, mkdir as makedir, makedirs, remove
from collections.abc import Callable


def files_operation(
    operation: Callable[[str, str], None], source: str, files: tuple[str, ...]
) -> None:
    dest = files[-1]
    sources = [source] + list(files[:-1])
    if not exists(dest):
        if len(sources) > 1:
            raise FileNotFoundError(f"No such destination folder {dest}")
    else:
        dest = join(dest, "{}")
    for source in sources:
        operation(source, dest.format(basename(source)))


def cp(source: str, *files: str) -> None:
    """Copy multiple files from a source to a dest

    The last string passed is used a the destination file and all the other strings
    are used as source files
    """
    files_operation(
        lambda source, dest: copytree(source, dest)
        if isdir(source)
        else copy(source, dest),
        source,
        files,
    )


def ls(folder: str) -> list[str]:
    """Return a list of files in the given folder"""
    return [join(folder, file) for file in listdir(folder)]


def mkdir(folder: str, parents=False, exist_ok=True) -> None:
    """Create a directory

    if parents is true, all the parent directories are created
    if exist_ok is true, the function doesn't check if the file already exists
    """
    if parents:
        makedirs(folder, exist_ok=exist_ok)
    else:
        if not exist_ok or not exists(folder):
            makedir(folder)


def mv(source: str, *files: str) -> None:
    """Move multiple files from a source to a dest

    The last string passed is used a the destination file and all the other strings
    are used as source files
    """
    files_operation(lambda source, dest: move(source, dest), source, files)


def rm(*files: str, non_exist_ok=True) -> None:
    """Delete multiple files

    if non_exist_ok is true, the function doesn't raise an exception if one of the
    the files don't exist
    """
    for file in files:
        if isdir(file):
            rmtree(file)
        elif not non_exist_ok or exists(file):
            remove(file)


def cat(*files: str) -> str:
    """Read and concatenate the content of multiple files"""
    result = ""
    for file in files:
        with open(file, "rt") as f:
            result += f.read()
    return result


def read(file: str) -> str:
    with open(file, "rt") as f:
        return f.read()


def write(file: str, content: str) -> None:
    with open(file, "wt") as f:
        f.write(content)
