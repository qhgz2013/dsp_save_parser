from .generator import generate_parser
from .common import ParserBase


def _bootstrap():
    generate_parser('%s/save_format.txt' % __name__, '%s/generated.py' % __name__)


try:
    _bootstrap()
except OSError:
    pass

try:
    from .generated import GameSave
except ImportError:
    import abc as _abc

    # stub
    class GameSave(ParserBase, metaclass=_abc.ABCMeta):
        pass

__version__ = '1.0.2'
