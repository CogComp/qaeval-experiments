import argparse
import random
from collections import defaultdict
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Any, Dict


def load_instances(file_path: str) -> Dict[str, Dict[str, Any]]:
    instances = defaultdict(dict)
    with JsonlReader(file_path) as f:
        for instance in f:
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            summarizer_type = instance['summarizer_type']
            if summarizer_type == 'reference':
                instances[instance_id][summarizer_id] = instance
    return instances



def main(args):
    random.seed(4)

    num_instances = 10
    num_references = 2

    instances = load_instances(args.summaries_jsonl)

    instance_ids = list(instances.keys())
    random.shuffle(instance_ids)
    sample_instance_ids = instance_ids[:num_instances]

    with JsonlWriter(args.output_jsonl) as out:
        for instance_id in sorted(sample_instance_ids):
            annotators = list(instances[instance_id].keys())
            random.shuffle(annotators)
            sample_annotators = annotators[:num_references]

            for annotator in sorted(sample_annotators):
                out.write(instances[instance_id][annotator])


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('summaries_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)