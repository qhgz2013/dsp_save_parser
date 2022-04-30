from typing import *
from typing import BinaryIO
from struct import unpack
from abc import ABCMeta

__all__ = ['ParserBase', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float32', 'float64',
           'string', 'boolean', 'int24', 'FlexibleInt', 'SaveObject']

_BYTE_ORDER = 'little'  # type: Literal['little', 'big']
_IO_TYPE = BinaryIO
_BUILTIN_TYPES = set(__all__) | {'NoneType', 'int', 'float', 'str', 'bool'}


class ParserBase:
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        raise NotImplementedError()

    def _repr_internal_get_field_repr(self):
        data = []
        for name in self.__slots__:
            value = getattr(self, name)
            if value.__class__.__name__ in _BUILTIN_TYPES:
                data.append(f'{name}={value!r}')
            else:
                data.append(f'{name}=<{value.__class__.__name__}>')
        return ", ".join(data)

    def __repr__(self):
        return f'<{self.__class__.__name__} ({self._repr_internal_get_field_repr()})>'


# noinspection PyPep8Naming
class int8(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint8(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class boolean(int8, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(bool(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=False)))


# noinspection PyPep8Naming
class int16(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(2), byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint16(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(2), byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class int24(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(3), byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class int32(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(4), byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint32(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(4), byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class int64(int32, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(8), byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint64(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(8), byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class float32(float, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        if _BYTE_ORDER == 'big':
            return cls(unpack('>f', data.read(4))[0])
        else:
            return cls(unpack('<f', data.read(4))[0])


# noinspection PyPep8Naming
class float64(float32, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        if _BYTE_ORDER == 'big':
            return cls(unpack('>d', data.read(8))[0])
        else:
            return cls(unpack('<d', data.read(8))[0])


# noinspection PyPep8Naming
class varint(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        assert _BYTE_ORDER == 'little', 'big endian varint is not implemented'
        value = 0
        while True:
            byte = data.read(1)
            if not byte:
                raise EOFError()
            byte = int.from_bytes(byte, byteorder=_BYTE_ORDER, signed=False)
            value = value << 7 | (byte & 0x7F)
            if byte & 0x80 == 0:
                break
        return cls(value)


# noinspection PyPep8Naming
class string(str, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        length = varint.parse(data)
        return cls(data.read(length).decode('utf-8'))


# IOHelper.WriteFlexibleInt
class FlexibleInt(int32, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        indicator = uint8.parse(data)
        if indicator > 4:
            return cls(indicator)
        else:
            return cls(int.from_bytes(data.read(indicator), byteorder=_BYTE_ORDER, signed=True))


class SaveObject(ParserBase, metaclass=ABCMeta):
    location_start: int
    """The start location of the serialized object in the file."""
    location_end: int
    """The end location of the serialized object in the file."""

    def __repr__(self):
        if self.location_start == -1 and self.location_end == -1:
            return super().__repr__()
        return f'<{self.__class__.__name__} [{self.location_start}-{self.location_end}] ' \
               f'({self._repr_internal_get_field_repr()})>'
