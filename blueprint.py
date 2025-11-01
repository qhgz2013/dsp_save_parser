import os
from dataclasses import dataclass
from enum import IntEnum
import datetime
from urllib.parse import unquote
from gzip import decompress
from dsp_save_parser import BlueprintData
from io import BytesIO
from base64 import b64decode
# from hashlib import md5
from buggy_md5 import MD5
import argparse

class EIconLayout(IntEnum):
    NONE = 0
    NO_ICON = 1
    ONE_ICON = 10
    ONE_ICON_SMALL = 11
    TWO_ICON_46 = 20
    TWO_ICON_53 = 21
    TWO_ICON_59 = 22
    TWO_ICON_57 = 23
    TWO_ICON_51 = 24
    THREE_ICON_813 = 30
    THREE_ICON_279 = 31
    THREE_ICON_573 = 32
    THREE_ICON_591 = 33
    FOUR_ICON_7913 = 40
    FOUR_ICON_8462 = 41
    FIVE_ICON_57913 = 50
    FIVE_ICON_PENTA = 51

@dataclass
class Blueprint:
    layout: EIconLayout  # [1]
    icon0: int  # [2]
    icon1: int  # [3]
    icon2: int  # [4]
    icon3: int  # [5]
    icon4: int  # [6]
    time: datetime.datetime  # [8]
    game_version: str  # [9]
    short_desc: str  # [10], should be unescaped
    desc: str  # [11], should be unescaped
    data: BlueprintData

_epoch = datetime.date(1970, 1 , 1)
_dotnet_minvalue = datetime.date(1, 1, 1)
_offset = (_epoch - _dotnet_minvalue).total_seconds()
_ten_million = 10000000

def datetime_from_tick(tick: int) -> datetime.datetime:
    seconds = tick / _ten_million
    timestamp = seconds - _offset
    return datetime.datetime.fromtimestamp(timestamp)

def load_blueprint_data(file: str):  # impl: BlueprintData.LoadBlueprintData
    assert os.path.isfile(file), f'file "{file}" not exist'

    with open(file, 'r', encoding='ascii') as f:
        data = f.read()
    
    # construct from base64 string

    # header from base64 string
    assert len(data) >= 28, f'length corrupt, expected no less than 28 bytes, but got {len(data)}'
    assert data.startswith('BLUEPRINT:'), 'corrupt header'

    data_begin_pos = data.find('"', 28, min(len(data), 8192))
    assert data_begin_pos >= 0, 'corrupt data, expected quote char (") near the beginning of the file'

    header_array = data[10:data_begin_pos].split(',')
    assert len(header_array) >= 12, f'invalid header array length, expected no less than 12, but got {len(header_array)}'

    check_idx = max(len(data) - 36, 0)
    data_end_pos = data.rfind('"', check_idx)
    assert data_end_pos >= 0, 'corrupt data, expected quote char (") near the end of the file'
    assert len(data) - 1 - data_end_pos >= 32, 'invalid position for quote char (") near the end of the file'

    md5_obj = MD5()
    md5_obj.update(data[:data_end_pos].encode('ascii'))
    data_sign = md5_obj.hexdigest().lower()
    expected_sign = data[data_end_pos+1:data_end_pos+33].lower()
    assert data_sign == expected_sign, f'md5 signature check failed (computed {data_sign}, recorded value {expected_sign})'

    blobs = data[data_begin_pos+1:data_end_pos].encode('ascii')
    blobs = b64decode(blobs)
    blobs = decompress(blobs)
    with BytesIO(blobs) as f:
        data = BlueprintData.parse(f)

    return Blueprint(EIconLayout(int(header_array[1])), int(header_array[2]), int(header_array[3]),
                     int(header_array[4]), int(header_array[5]), int(header_array[6]),
                     datetime_from_tick(int(header_array[8])), header_array[9], unquote(header_array[10]),
                     unquote(header_array[11]), data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('blueprint_path', help=r'Blueprint file path, normally located in ~\Documents\Dyson Sphere Program\Blueprint', nargs='?')
    args = parser.parse_args()
    blueprint = load_blueprint_data(args.blueprint_path)
    print(blueprint)


if __name__ == '__main__':
    main()
