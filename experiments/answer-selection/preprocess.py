import argparse
import csv
import html
import itertools
import json
import os
from sacrerouge.io import JsonlReader
from typing import Any, Dict, List


def writerow(writer: csv.writer, prompt_ids: List[str], current: Dict[str, Any]) -> None:
    writer.writerow([
        html.escape(json.dumps(prompt_ids)),
        html.escape(json.dumps(current))
    ])


def main(args):
    dirname = os.path.dirname(args.output_csv)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    instances = JsonlReader(args.input_jsonl).read()

    with open(args.output_csv, 'w') as out:
        writer = csv.writer(out)
        writer.writerow(['prompt_ids', 'instancejson'])

        # Group instances by (instance_id, annotator), which should group
        # prompts together by the same summary
        key = lambda instance: (instance['instance_id'], instance['annotator'])
        instances.sort(key=key)
        for _, group in itertools.groupby(instances, key):
            # Sort the group by offset
            group = list(group)
            group.sort(key=lambda member: member['answer_start'])

            prompt_ids = []
            current = None
            for instance in group:
                if current is None:
                    prompt_ids = []
                    current = {
                        'summary': instance['context'],
                        'offsets': []
                    }

                prompt_ids.append(instance['prompt_id'])
                current['offsets'].append({
                    'foregroundStart': instance['sent_start'],
                    'foregroundEnd': instance['sent_end'],
                    'highlightStart': instance['answer_start'],
                    'highlightEnd': instance['answer_end'],
                })

                if len(prompt_ids) == args.num_prompts_per_assignment:
                    writerow(writer, prompt_ids, current)
                    prompt_ids = []
                    current = None

            if len(prompt_ids) > 0:
                writerow(writer, prompt_ids, current)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('output_csv')
    argp.add_argument('--num-prompts-per-assignment', type=int, default=5)
    args = argp.parse_args()
    main(args)