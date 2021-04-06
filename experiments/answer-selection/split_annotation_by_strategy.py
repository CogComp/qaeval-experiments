import argparse
import csv


def main(args):
    with open(args.output_all_nps_csv, 'w') as out_all:
        with open(args.output_top_nps_csv, 'w') as out_top:
            with open(args.output_ner_csv, 'w') as out_ner:
                writer_all = csv.writer(out_all)
                writer_top = csv.writer(out_top)
                writer_ner = csv.writer(out_ner)

                with open(args.input_csv, 'r') as f:
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        if i == 0:
                            strategy_index = row.index('strategies')
                            writer_all.writerow(row)
                            writer_top.writerow(row)
                            writer_ner.writerow(row)
                        else:
                            strategies = row[strategy_index].split(',')
                            for strategy in strategies:
                                if strategy == 'all-nps':
                                    writer_all.writerow(row)
                                elif strategy == 'top-nps':
                                    writer_top.writerow(row)
                                elif strategy == 'ner':
                                    writer_ner.writerow(row)
                                else:
                                    raise Exception(f'Unknown strategy: {strategy}')


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_csv')
    argp.add_argument('output_all_nps_csv')
    argp.add_argument('output_top_nps_csv')
    argp.add_argument('output_ner_csv')
    args = argp.parse_args()
    main(args)