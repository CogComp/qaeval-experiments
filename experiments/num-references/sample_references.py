import argparse
import random
from collections import defaultdict
from sacrerouge.io import JsonlReader, JsonlWriter
from tqdm import tqdm
from typing import Any, Dict, List


def get_references(instances: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    references = defaultdict(dict)
    for instance in instances:
        for reference in instance['references']:
            references[instance['instance_id']][reference['summarizer_id']] = reference
    return references


def sample_references(instance_id_to_references: Dict[str, Dict[str, Dict[str, Any]]],
                      num_references: int) -> Dict[str, List[Dict[str, Any]]]:
    sample = {}
    for instance_id in sorted(instance_id_to_references.keys()):
        reference_ids = sorted(instance_id_to_references[instance_id].keys())
        random.shuffle(reference_ids)
        sample[instance_id] = [instance_id_to_references[instance_id][reference_id] for reference_id in sorted(reference_ids[:num_references])]
    return sample


def main(args):
    random.seed(4)

    instances = JsonlReader(args.input_jsonl).read()
    instance_id_to_references = get_references(instances)

    with JsonlWriter(args.output_file) as out:
        for num_references in tqdm([2, 3, 4]):
            for sample_index in tqdm(range(args.num_samples)):
                sample = sample_references(instance_id_to_references, num_references)
                for instance in instances:
                    copy = dict(instance)
                    copy['summarizer_id'] = f'{instance["summarizer_id"]}_{num_references}_{sample_index}'
                    copy['references'] = sample[instance['instance_id']]
                    out.write(copy)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('num_samples', type=int)
    argp.add_argument('output_file')
    args = argp.parse_args()
    main(args)