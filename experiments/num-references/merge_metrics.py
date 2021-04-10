import argparse
from collections import defaultdict
from sacrerouge.data import Metrics
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import List


def load_metrics(metrics_files: List[str]) -> List[Metrics]:
    metrics_dicts = defaultdict(dict)
    for metrics_file in metrics_files:
        with JsonlReader(metrics_file, Metrics) as f:
            for metrics in f:
                if metrics.summarizer_id not in metrics_dicts[metrics.instance_id]:
                    metrics_dicts[metrics.instance_id][metrics.summarizer_id] = metrics
                else:
                    metrics_dicts[metrics.instance_id][metrics.summarizer_id].merge(metrics)

    metrics_list = []
    for metrics_dict in metrics_dicts.values():
        metrics_list.extend(list(metrics_dict.values()))
    return metrics_list


def main(args):
    metrics_list = load_metrics(args.input_files)
    with JsonlWriter(args.output_file) as out:
        for metrics in metrics_list:
            out.write(metrics)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('output_file')
    argp.add_argument('input_files', nargs='+')
    args = argp.parse_args()
    main(args)