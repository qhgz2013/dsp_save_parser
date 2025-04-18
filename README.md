# DSP Save Parser

A python based save data parser for Dyson Sphere Program.

Current version: `0.10.32.25783` (Updated on 31 Mar, 2025)

## Usage

### Parse DSV file (deserialization)

Example:

```python
import dsp_save_parser as s

with open('your_save_data.dsv', 'rb') as f:
    print(s.GameSave.parse(f))
```

`main.py` provides a basic skeleton structure for parsing a DSP save file: run `python main.py [save_data_path]` and it would print something like:

```text
<GameSave [0-73758524] (header=<VFSaveHeader>, file_length=73758524, version=7, is_sandbox_mode=0, is_peace_mode=0, major_game_version=0, minor_game_version=10, release_game_version=32, build_game_version=25783, game_tick=14177593, now_ticks=638798114900094046, size_of_png_file=129727, screen_shot_png_file=<bytes>, account_data=<AccountData>, dyson_sphere_energy_gen_current_tick=54136362, game_data=<GameData>)>
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
    planet_data_node_list = data.game_data.galaxy.data
    while planet_data_node_list is not None and planet_data_node_list.id != -1:
        amount_dict = defaultdict(int)
        # from 0.10.32.25783: vein data moved to GalaxyData
        for vein_data in planet_data_node_list.value.vein_groups:
            amount_dict[vein_data.type] += vein_data.amount
        amount_dict = {EVeinType(k).name: v for k, v in amount_dict.items()}
        print(planet_data_node_list.id, amount_dict)
        planet_data_node_list = planet_data_node_list.next
```

### Export to DSV file (serialization)

Write access is now supported. Here is an example:

```python
import dsp_save_parser as s

with open('your_save_data.dsv', 'rb') as f:
    data = s.GameSave.parse(f)

# do some modifications, for example:
data.account_data.user_name = 'my_name'  # change player's name
data.game_data.main_player.sand_count = 99999999  # modify sands
# if your changes affect the size of the save data, don't forget to re-calculate the whole file length
data.file_length = len(data)

# save changes
with open('your_modded_save_data.dsv', 'wb') as f:
    data.save(f)
```

Type casting for basic data types (uints, ints, floats, strings and their arrays) is automatically executed during calling `save` method.

If you changed the element counts in an array, don't forget to change its length attribute of the array:
```python
data.game_data.game_desc.saved_theme_ids.pop()  # remove element
data.game_data.game_desc.num_saved_theme_ids -= 1  # also decrease the array length manually
```

## Save data file structure

Refers to [save_format.txt](dsp_save_parser/save_format.txt) for detail. It should be quite straightforward and easy-understanding, maybe?

As for the meaning of each field, ask the developers rather than me.