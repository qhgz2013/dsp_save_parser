from ast import arg
import dsp_save_parser as s
import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('save_path', help='Save data path for .dsv file. If not specified, use the last exit save'
                                          ' data by default', nargs='?')
    args = parser.parse_args()
    if args.save_path is None:
        args.save_path = os.path.expanduser(r'~\Documents\Dyson Sphere Program\Save\_lastexit_.dsv')
    assert os.path.isfile(args.save_path), '%s is not a file' % args.save_path
    with open(args.save_path, 'rb') as f:
        data = s.GameSave.parse(f)
        print(data)
        # do sth with the save data here, for example, exporting the vein amounts for each planet:
        # for factory in data.game_data.factories:
        #     print(factory.planet_id, factory.planet_theme, factory.planet.vein_amounts)


if __name__ == '__main__':
    main()
