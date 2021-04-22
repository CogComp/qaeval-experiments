import argparse
import random
from collections import defaultdict
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import List


def load_references(file_path: str):
    instance_to_reference = defaultdict(dict)
    with JsonlReader(file_path) as f:
        for instance in f:
            for reference in instance['references']:
                if len(reference['questions']) > 0:
                    instance_to_reference[instance['instance_id']][reference['summarizer_id']] = reference
    return instance_to_reference


def load_peers(file_path: str):
    instance_to_peers = defaultdict(dict)
    with JsonlReader(file_path) as f:
        for instance in f:
            instance_to_peers[instance['instance_id']][instance['summarizer_id']] = instance
    return instance_to_peers


def get_candidate_peers(instance_to_reference, instance_to_peers) -> List[str]:
    peers = None
    for instance_id in instance_to_reference.keys():
        if peers is None:
            peers = set(instance_to_peers[instance_id].keys())
        else:
            peers |= set(instance_to_peers[instance_id].keys())

    system_peers = []
    for p in peers:
        try:
            int(p)
            system_peers.append(p)
        except:
            pass
    return list(sorted(system_peers))


def main(args):
    random.seed(4)

    instance_to_reference = load_references(args.questions_jsonl)
    instance_to_peers = load_peers(args.summaries_jsonl)

    candidates = get_candidate_peers(instance_to_reference, instance_to_peers)
    random.shuffle(candidates)
    sample = candidates[:args.num_peers]

    with JsonlWriter(args.output_jsonl) as out:
        for instance_id in sorted(instance_to_reference.keys()):
            reference_ids = list(sorted(instance_to_reference[instance_id].keys()))
            references = [instance_to_reference[instance_id][reference_id] for reference_id in reference_ids]

            for peer_id in sample:
                peer = instance_to_peers[instance_id][peer_id]
                peer['references'] = references
                out.write(peer)

            for i, reference_id in enumerate(reference_ids):
                jk_references = references[:i] + references[i + 1:]
                peer = instance_to_peers[instance_id][reference_id]
                peer['references'] = jk_references
                out.write(peer)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('questions_jsonl')
    argp.add_argument('summaries_jsonl')
    argp.add_argument('output_jsonl')
    argp.add_argument('--num-peers', type=int, default=5)
    args = argp.parse_args()
    main(args)