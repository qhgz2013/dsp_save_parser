from typing import *
from typing import BinaryIO
from struct import unpack, pack
from abc import ABCMeta
from io import BytesIO

__all__ = ['ParserBase', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float32', 'float64',
           'string', 'boolean', 'int24', 'FlexibleInt', 'SaveObject']

_BYTE_ORDER = 'little'  # type: Literal['little', 'big']
_IO_TYPE = BinaryIO
_BUILTIN_TYPES = set(__all__) | {'NoneType', 'int', 'float', 'str', 'bool'}
_REPR_SKIP_ENTRIES = {'location_start', 'location_end'}

assert _BYTE_ORDER in {'little', 'big'}


class ParserBase:
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        raise NotImplementedError()

    def save(self, stream: _IO_TYPE):
        raise NotImplementedError()

    def _repr_internal_get_field_repr(self):
        data = []
        for name in self.__slots__:
            if name in _REPR_SKIP_ENTRIES:
                continue
            value = getattr(self, name)
            if value.__class__.__name__ in _BUILTIN_TYPES:
                data.append(f'{name}={value!r}')
            elif isinstance(value, list) and len(value) == 0:
                data.append(f'{name}=[]')  # special cast for empty list
            else:
                data.append(f'{name}=<{value.__class__.__name__}>')
        return ", ".join(data)

    def __repr__(self):
        return f'<{self.__class__.__name__} ({self._repr_internal_get_field_repr()})>'

    def get_size(self) -> int:
        return 0

    def _get_size_via_save(self) -> int:
        ms = BytesIO()
        self.save(ms)
        return ms.tell()

    def __len__(self):
        return self.get_size()


# noinspection PyPep8Naming
class int8(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=True))

    def get_size(self):
        return 1


# noinspection PyPep8Naming
class uint8(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=False))

    def get_size(self):
        return 1


# noinspection PyPep8Naming
class boolean(int8, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(bool(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=False)))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=False))

    def get_size(self):
        return 1


# noinspection PyPep8Naming
class int16(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(2), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(2, byteorder=_BYTE_ORDER, signed=True))

    def get_size(self):
        return 2


# noinspection PyPep8Naming
class uint16(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(2), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(2, byteorder=_BYTE_ORDER, signed=False))

    def get_size(self):
        return 2


# noinspection PyPep8Naming
class int24(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(3), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(3, byteorder=_BYTE_ORDER, signed=True))

    def get_size(self):
        return 3


# noinspection PyPep8Naming
class int32(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(4), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(4, byteorder=_BYTE_ORDER, signed=True))

    def get_size(self):
        return 4


# noinspection PyPep8Naming
class uint32(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(4), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(4, byteorder=_BYTE_ORDER, signed=False))

    def get_size(self):
        return 4


# noinspection PyPep8Naming
class int64(int32, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(8), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(8, byteorder=_BYTE_ORDER, signed=True))

    def get_size(self):
        return 8


# noinspection PyPep8Naming
class uint64(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(8), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(8, byteorder=_BYTE_ORDER, signed=False))

    def get_size(self):
        return 8


if _BYTE_ORDER == 'little':
    # noinspection PyPep8Naming
    class float32(float, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('<f', data.read(4))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('<f', self))

        def get_size(self):
            return 4

else:
    # noinspection PyPep8Naming
    class float32(float, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('>f', data.read(4))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('>f', self))

        def get_size(self):
            return 4


if _BYTE_ORDER == 'little':
    # noinspection PyPep8Naming
    class float64(float32, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('<d', data.read(8))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('<d', self))

        def get_size(self):
            return 8
else:
    # noinspection PyPep8Naming
    class float64(float32, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('>d', data.read(8))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('>d', self))

        def get_size(self):
            return 8


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

    def save(self, stream: _IO_TYPE):
        data_list = []
        value = int(self)
        while value > 0x7F:
            data_list.append(0x80 | value & 0x7F)
            value >>= 7
        data_list.append(value)
        stream.write(bytes(data_list))

    def get_size(self) -> int:
        return self._get_size_via_save()

# noinspection PyPep8Naming
class string(str, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        length = varint.parse(data)
        return cls(data.read(length).decode('utf-8'))

    def save(self, stream: _IO_TYPE):
        b_str = self.encode('utf-8')
        varint(len(b_str)).save(stream)
        stream.write(b_str)

    def get_size(self) -> int:
        return self._get_size_via_save()


# IOHelper.WriteFlexibleInt
class FlexibleInt(int32, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        indicator = uint8.parse(data)
        if indicator > 4 or indicator == 0:
            return cls(indicator)
        elif indicator < 4:
            return cls(int.from_bytes(data.read(indicator), byteorder=_BYTE_ORDER, signed=False))
        else:
            return cls(int.from_bytes(data.read(indicator), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        if self == 0:
            stream.write(b'\x00')
        elif self < 0:
            stream.write(b'\x04')
            stream.write(self.to_bytes(4, byteorder=_BYTE_ORDER, signed=True))
        elif self <= 0xFF:
            if self <= 4:
                stream.write(b'\x01')
            stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=False))
        elif self <= 0xFFFF:
            stream.write(b'\x02')
            stream.write(self.to_bytes(2, byteorder=_BYTE_ORDER, signed=False))
        elif self <= 0xFFFFFF:
            stream.write(b'\x03')
            stream.write(self.to_bytes(3, byteorder=_BYTE_ORDER, signed=False))
        else:
            stream.write(b'\x04')
            stream.write(self.to_bytes(4, byteorder=_BYTE_ORDER, signed=True))

    def get_size(self) -> int:
        if self == 0:
            return 1
        elif self < 0:
            return 5
        elif self <= 0xFF:
            if self <= 4:
                return 2
            return 1
        elif self <= 0xFFFF:
            return 3
        elif self <= 0xFFFFFF:
            return 4
        else:
            return 5


class SaveObject(ParserBase, metaclass=ABCMeta):
    location_start: int
    """The start location of the deserialized object in the file."""
    location_end: int
    """The end location of the deserialized object in the file."""

    def __repr__(self):
        if self.location_start == -1 and self.location_end == -1:
            return super().__repr__()
        return f'<{self.__class__.__name__} [{self.location_start}-{self.location_end}] ' \
               f'({self._repr_internal_get_field_repr()})>'
