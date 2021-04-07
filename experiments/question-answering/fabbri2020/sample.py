import argparse
import random
import sys

from sacrerouge.io import JsonlReader, JsonlWriter


def sample_instances(summaries, n):
    instances = set()
    for summary in summaries:
        instances.add(summary['instance_id'])
    instances = sorted(instances)
    random.shuffle(instances)
    return set(instances[:n])


def sample_summarizers(summaries, n):
    summarizers = set()
    for summary in summaries:
        summarizers.add(summary['summarizer_id'])
    summarizers = sorted(summarizers)
    random.shuffle(summarizers)
    return set(summarizers[:n])


def sample_next_summarizers(summaries, already_chosen, n):
    summarizers = set()
    for summary in summaries:
        summarizers.add(summary['summarizer_id'])
    summarizers -= already_chosen
    summarizers = sorted(summarizers)
    random.shuffle(summarizers)
    return set(summarizers[:n])


def save(iterable, instance_ids, summarizer_ids, output_file):
    with JsonlWriter(output_file) as out:
        for item in iterable:
            if item['instance_id'] in instance_ids and item['summarizer_id'] in summarizer_ids:
                out.write(item)


def main(args):
    random.seed(args.random_seed)

    summaries = JsonlReader(args.summaries_jsonl).read()
    metrics_list = JsonlReader(args.metrics_jsonl).read()

    instance_ids = sample_instances(summaries, args.num_instances)
    summarizer_ids1 = sample_summarizers(summaries, args.num_summaries)
    summarizer_ids2 = sample_next_summarizers(summaries, summarizer_ids1, 16 - args.num_summaries)
    union = summarizer_ids1 | summarizer_ids2

    print(summarizer_ids1)
    print(summarizer_ids2)

    save(summaries, instance_ids, union, args.output_summaries_jsonl)
    save(metrics_list, instance_ids, union, args.output_metrics_jsonl)

    save(summaries, instance_ids, summarizer_ids1, args.output_summaries_jsonl_1)
    save(metrics_list, instance_ids, summarizer_ids1, args.output_metrics_jsonl_1)

    save(summaries, instance_ids, summarizer_ids2, args.output_summaries_jsonl_2)
    save(metrics_list, instance_ids, summarizer_ids2, args.output_metrics_jsonl_2)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('--summaries-jsonl', required=True)
    argp.add_argument('--metrics-jsonl', required=True)
    argp.add_argument('--num-summaries', type=int, required=True)
    argp.add_argument('--num-instances', type=int, required=True)
    argp.add_argument('--output-summaries-jsonl', required=True)
    argp.add_argument('--output-metrics-jsonl', required=True)
    argp.add_argument('--output-summaries-jsonl-1', required=True)
    argp.add_argument('--output-metrics-jsonl-1', required=True)
    argp.add_argument('--output-summaries-jsonl-2', required=True)
    argp.add_argument('--output-metrics-jsonl-2', required=True)
    argp.add_argument('--random-seed', type=int, default=4)
    args = argp.parse_args()
    main(args)