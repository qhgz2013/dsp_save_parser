# DSP Save Parser

A python based save data parser for Dyson Sphere Program.

Current version: `0.9.27.15033` (Updated on 2 November, 2022)

## Usage

Example:

```python
import dsp_save_parser as s

with open('your_save_data.dsv', 'rb') as f:
    print(s.GameSave.parse(f))
```

`main.py` provides a basic skeleton structure for parsing a DSP save file: run `python main.py [save_data_path]` and it would print something like:

```text
<GameSave [0-109813724] (header=<VFSaveHeader>, file_length=109813724, version=7, is_sandbox_mode=0, is_peace_mode=1, major_game_version=0, minor_game_version=9, release_game_version=27, build_game_version=15033, game_tick=25330163, now_ticks=638031766897127509, size_of_png_file=247932, screen_shot_png_file=<bytes>, account_data=<AccountData>, dyson_sphere_energy_gen_current_tick=1402540368, game_data=<GameData>)>
```

*If `save_data_path` is not specified, the program will use the last exit save data `~\Documents\Dyson Sphere Program\Save\_lastexit_.dsv` by default.*

**A more advanced one -- exporting vein amounts for all explored planets:**

```python
from enum import IntEnum
from collections import defaultdict


class EVeinType(IntEnum):
    NONE = 0
    Iron = 1
    Copper = 2
    Silicium = 3
    Titanium = 4
    Stone = 5
    Coal = 6
    Oil = 7
    Fireice = 8
    Diamond = 9
    Fractal = 10
    Crysrub = 11
    Grat = 12
    Bamboo = 13
    Mag = 14
    MAX = 15


with open('xxx.dsv', 'rb') as f:
    data = s.GameSave.parse(f)
    for factory in data.game_data.factories:
        amount_dict = defaultdict(int)
        # from 0.9.27: "factory.planet.vein_amounts" is not used and keeps zero
        for vein_data in factory.vein_pool:
            if vein_data.id == 0:
                continue
            amount_dict[vein_data.type] += vein_data.amount
        amount_dict = {EVeinType(k).name: v for k, v in amount_dict.items()}
        print(factory.planet_id, factory.planet_theme, amount_dict)
```

## Save data file structure

Refers to [save_format.txt](dsp_save_parser/save_format.txt) for detail. It should be quite straightforward and easy-understanding, maybe?

As for the meaning of each field, ask the developers rather than me.