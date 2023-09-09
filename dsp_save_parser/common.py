from typing import *
from typing import BinaryIO
from struct import unpack, pack
from abc import ABCMeta

__all__ = ['ParserBase', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float32', 'float64',
           'string', 'boolean', 'int24', 'FlexibleInt', 'SaveObject']

_BYTE_ORDER = 'little'  # type: Literal['little', 'big']
_IO_TYPE = BinaryIO
_BUILTIN_TYPES = set(__all__) | {'NoneType', 'int', 'float', 'str', 'bool'}

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

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint8(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class boolean(int8, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(bool(int.from_bytes(data.read(1), byteorder=_BYTE_ORDER, signed=False)))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(1, byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class int16(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(2), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(2, byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint16(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(2), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(2, byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class int24(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(3), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(3, byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class int32(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(4), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(4, byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint32(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(4), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(4, byteorder=_BYTE_ORDER, signed=False))


# noinspection PyPep8Naming
class int64(int32, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(8), byteorder=_BYTE_ORDER, signed=True))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(8, byteorder=_BYTE_ORDER, signed=True))


# noinspection PyPep8Naming
class uint64(int, ParserBase):
    @classmethod
    def parse(cls, data: _IO_TYPE, props: tuple = ()):
        return cls(int.from_bytes(data.read(8), byteorder=_BYTE_ORDER, signed=False))

    def save(self, stream: _IO_TYPE):
        stream.write(self.to_bytes(8, byteorder=_BYTE_ORDER, signed=False))


if _BYTE_ORDER == 'little':
    # noinspection PyPep8Naming
    class float32(float, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('<f', data.read(4))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('<f', self))
else:
    # noinspection PyPep8Naming
    class float32(float, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('>f', data.read(4))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('>f', self))


if _BYTE_ORDER == 'little':
    # noinspection PyPep8Naming
    class float64(float32, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('<d', data.read(8))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('<d', self))
else:
    # noinspection PyPep8Naming
    class float64(float32, ParserBase):
        @classmethod
        def parse(cls, data: _IO_TYPE, props: tuple = ()):
            return cls(unpack('>d', data.read(8))[0])

        def save(self, stream: _IO_TYPE):
            stream.write(pack('>d', self))


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


class SaveObject(ParserBase, metaclass=ABCMeta):
    location_start: int
    """The start location of the deserialized object in the file."""
    location_end: int
    """The end location of the deserialized object in the file."""
    # _skip_setattr_check: bool
    # """Controlled by generated codes, set to True during __init__ calls to accelerate parsing"""

    def __repr__(self):
        if self.location_start == -1 and self.location_end == -1:
            return super().__repr__()
        return f'<{self.__class__.__name__} [{self.location_start}-{self.location_end}] ' \
               f'({self._repr_internal_get_field_repr()})>'

    # def __setattr__(self, key, value):
    #     if SaveObject._skip_setattr_check:
    #         object.__setattr__(self, key, value)
    #         return
    #     if key not in self.__annotations__:
    #         super().__setattr__(key, value)
    #         return
    #     # type casting for basic types like (u)int8/16/24/32 & float32/64 & string in setattr hook
    #     if value is not None:
    #         # typing handling
    #         annotation = self.__annotations__[key]
    #         if isinstance(annotation, str):
    #             # user-defined class in save_format.txt, skip type conversion: user should handle it properly
    #             pass
    #         elif annotation.__module__ == 'typing':
    #             annotation_name = getattr(annotation, '__name__', None)
    #             if annotation_name is None:  # fallback option: in Py3.6 __name__ is unavailable for Union type
    #                 annotation_name = annotation.__class__.__name__
    #             if annotation_name == 'List':
    #                 assert isinstance(value, list)
    #                 elem_type = annotation.__args__[0]
    #                 if type(elem_type) == type:
    #                     for i, elem in enumerate(value):
    #                         if not isinstance(elem, elem_type):
    #                             value[i] = elem_type(elem)
    #             elif annotation_name == 'Union' or annotation_name.startswith('_Union'):
    #                 # Optional[T] -> Union[T, None]
    #                 elem_type = annotation.__args__[0]
    #                 if type(elem_type) == type and not isinstance(value, elem_type):
    #                     value = elem_type(value)
    #         elif type(value) != annotation:
    #             # non typing types
    #             value = annotation(value)
    #     object.__setattr__(self, key, value)
