# DSP Save Parser

A python based save data parser for Dyson Sphere Program.

Current version: `0.9.26.12913` (Updated on 13 Jun, 2022)

## Usage

Example:

```python
import dsp_save_parser as s

with open('your_save_data.dsv', 'rb') as f:
    print(s.GameSave.parse(f))
```

Or run command: `python main.py [save_data_path]`.

If `save_data_path` is not specified, the program will use the last exit save data `~\Documents\Dyson Sphere Program\Save\_lastexit_.dsv` by default.

## Save data file structure

Refers to [save_format.txt](dsp_save_parser/save_format.txt) for detail. It should be quite straightforward and easy-understanding, maybe?

