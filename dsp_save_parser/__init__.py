from .generator import generate_parser
from .common import ParserBase


def _bootstrap():
    import os
    for file in os.listdir(__name__):
        if file.endswith('format.txt'):
            basename = os.path.splitext(file)[0]
            generate_parser(f'{__name__}/{file}', f'{__name__}/{basename}_generated.py')

try:
    _bootstrap()
except OSError:
    pass

try:
    from .save_format_generated import GameSave
    from .blueprint_format_generated import BlueprintData
except ImportError:
    import abc as _abc

    # stub
    class GameSave(ParserBase, metaclass=_abc.ABCMeta):
        pass

__version__ = '1.0.4'
