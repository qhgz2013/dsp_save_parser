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
        #
        # from collections import defaultdict
        # planet_data_node_list = data.game_data.galaxy.data
        # while planet_data_node_list is not None and planet_data_node_list.id != -1:
        #     amount_dict = defaultdict(int)
        #     # from 0.10.32.25783: vein data moved to GalaxyData
        #     for vein_data in planet_data_node_list.value.vein_groups:
        #         amount_dict[vein_data.type] += vein_data.amount
        #     print(planet_data_node_list.id, amount_dict)
        #     planet_data_node_list = planet_data_node_list.next
        #
        # or modifying save data:
        # data.account_data.user_name = 'my_name'
        # data.game_data.main_player.sand_count = 99999999  # modifying sands
        # re-calculate the whole file length
        # data.file_length = len(data)
        # once finished, export to dsv file via:
        # with open(args.save_path + '_modded.dsv', 'wb') as f:
        #     data.save(f)


if __name__ == '__main__':
    main()
