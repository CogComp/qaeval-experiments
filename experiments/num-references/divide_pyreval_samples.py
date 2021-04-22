import argparse
import json
import os
from sacrerouge.io import JsonlReader


def main(args):
    writers = {}
    with JsonlReader(args.input_jsonl) as f:
        for instance in f:
            summarizer_id, num_references, sample = instance['summarizer_id'].split('_')
            instance['summarizer_id'] = summarizer_id

            key = (num_references, sample)
            if key not in writers:
                os.makedirs(f'{args.output_dir}/{num_references}', exist_ok=True)
                writers[key] = open(f'{args.output_dir}/{num_references}/{sample}.jsonl', 'w')
            writer = writers[key]
            writer.write(json.dumps(instance) + '\n')

    for writer in writers.values():
        writer.close()


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('output_dir')
    args = argp.parse_args()
    main(args)