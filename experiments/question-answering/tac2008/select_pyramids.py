import argparse
from collections import defaultdict
from sacrerouge.data import Pyramid
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Dict, Set, Tuple


def load_expert_peers(file_path: str) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    # We only load peers because they require the same reference Pyramids. References
    # would require a different Pyramid each, and that's not currently supported
    # by sacrerouge
    instance_to_peers = defaultdict(set)
    instance_to_references = defaultdict(set)
    with JsonlReader(file_path) as f:
        for instance in f:
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            summarizer_type = instance['summarizer_type']
            if summarizer_type == 'peer':
                instance_to_peers[instance_id].add(summarizer_id)
                for reference in instance['references']:
                    reference_id = reference['summarizer_id']
                    instance_to_references[instance_id].add(reference_id)
    return instance_to_peers, instance_to_references


def main(args):
    instance_to_peers, instance_to_references = load_expert_peers(args.expert_answers_jsonl)
    with JsonlWriter(args.output_pyramid_jsonl) as out:
        with JsonlReader(args.pyramid_jsonl, Pyramid) as f:
            for pyramid in f:
                instance_id = pyramid.instance_id
                if instance_id in instance_to_references:
                    for reference in instance_to_references[instance_id]:
                        index = pyramid.summarizer_ids.index(reference)
                        pyramid = pyramid.remove_summary(index)
                    out.write(pyramid)

    with JsonlWriter(args.output_annotation_jsonl) as out:
        with JsonlReader(args.annotation_jsonl) as f:
            for instance in f:
                instance_id = instance['instance_id']
                summarizer_id = instance['summarizer_id']
                if instance_id in instance_to_peers and summarizer_id in instance_to_peers[instance_id]:
                    out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('expert_answers_jsonl')
    argp.add_argument('pyramid_jsonl')
    argp.add_argument('annotation_jsonl')
    argp.add_argument('output_pyramid_jsonl')
    argp.add_argument('output_annotation_jsonl')
    args = argp.parse_args()
    main(args)