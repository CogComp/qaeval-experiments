import argparse
import random
from collections import defaultdict
from sacrerouge.data import Metrics, MetricsDict
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Any, Dict, List, Set, Tuple


def map_summarizer_id_to_results(instances: List[Metrics]) -> Dict[Tuple[str, str], Dict[str, MetricsDict]]:
    mapping = defaultdict(dict)
    for instance in instances:
        instance_id = instance.instance_id
        summarizer_id, reference_id = instance.summarizer_id.split('_')
        summarizer_type = instance.summarizer_type
        mapping[(instance_id, summarizer_id, summarizer_type)][reference_id] = instance.metrics
    return mapping


def get_instance_id_to_references(instances: List[Metrics]) -> Dict[str, Set[str]]:
    instance_to_references = defaultdict(set)
    for instance in instances:
        instance_id = instance.instance_id
        _, reference_id = instance.summarizer_id.split('_')
        instance_to_references[instance_id].add(reference_id)
    return instance_to_references


def sample_references(instance_to_references: Dict[str, Set[str]], num_references: int) -> Dict[str, List[str]]:
    sampled = {}
    for instance_id, reference_ids in instance_to_references.items():
        reference_ids = list(sorted(reference_ids))
        random.shuffle(reference_ids)
        sample = reference_ids[:num_references]
        sampled[instance_id] = sample
    return sampled


def main(args):
    random.seed(args.random_seed)

    instances = JsonlReader(args.input_jsonl, Metrics).read()
    mapping = map_summarizer_id_to_results(instances)

    # Pick the specific references which are sampled for each instance_id. Be consistent and use these to score
    # all of the peer summaries
    instance_to_references = get_instance_id_to_references(instances)
    sampled_references = sample_references(instance_to_references, args.num_references)

    with JsonlWriter(args.output_file) as out:
        for (instance_id, summarizer_id, summarizer_type), metrics_dict in mapping.items():
            reference_ids = sampled_references[instance_id]
            metrics = sum([metrics_dict[reference_id] for reference_id in reference_ids]) / len(reference_ids)
            # Hacky: APES_num_correct should be the sum, not the average, so undo the division
            if 'APES' in metrics:
                metrics['APES']['num_correct'] *= len(reference_ids)

            out.write(Metrics(instance_id, summarizer_id, summarizer_type, metrics))


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('num_references', type=int)
    argp.add_argument('random_seed', type=int)
    argp.add_argument('output_file')
    args = argp.parse_args()
    main(args)