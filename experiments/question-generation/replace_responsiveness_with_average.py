import argparse
import itertools
from sacrerouge.data import Metrics, MetricsDict
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Dict, List


def aggregate_metrics(metrics_list: List[Metrics]) -> Dict[str, MetricsDict]:
    # The instances must be sorted by the key in order to use itertools.groupby
    metrics_list = sorted(metrics_list, key=lambda metrics: metrics.summarizer_id)
    for metrics in metrics_list:
        metrics.select_metrics(['overall_responsiveness'])
    key_to_metrics = {}
    for key, group in itertools.groupby(metrics_list, lambda metrics: metrics.summarizer_id):
        group_metrics = [member.metrics for member in group]
        key_to_metrics[key] = sum(group_metrics) / len(group_metrics)
    return key_to_metrics


def main(args):
    metrics_list = JsonlReader(args.input_file, Metrics).read()
    aggregated_metrics = aggregate_metrics(metrics_list)

    with JsonlWriter(args.output_file) as out:
        # I'm being lazy and just iterating twice because the aggregate method edited the metrics inplace
        for metrics in JsonlReader(args.input_file, Metrics).read():
            metrics.metrics['overall_responsiveness'] = aggregated_metrics[metrics.summarizer_id]['overall_responsiveness']
            out.write(metrics)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_file')
    argp.add_argument('output_file')
    args = argp.parse_args()
    main(args)