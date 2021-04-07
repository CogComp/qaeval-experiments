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
        writer.writerow(['input_ids', 'instancejson'])

        # Group instances by (instance_id, summarizer_id), which should group
        # prompts together by the same summary
        key = lambda instance: (instance['instance_id'], instance['summarizer_id'])
        instances.sort(key=key)
        for _, group in itertools.groupby(instances, key):
            for instance in group:
                summary = instance['summary']['text']
                input_ids = []
                current = None
                for reference in instance['references']:
                    for question_dict in reference['questions']:
                        if current is None:
                            input_ids = []
                            current = {
                                'summary': summary,
                                'questions': []
                            }

                        # This tuple needs to uniquely identify both the question
                        # and the summary
                        input_ids.append((
                            instance['instance_id'],
                            instance['summarizer_id'],
                            question_dict['question_id'],
                        ))
                        current['questions'].append(question_dict['question'])

                        if len(input_ids) == args.num_questions_per_assignment:
                            writerow(writer, input_ids, current)
                            input_ids = []
                            current = None

                if len(input_ids) > 0:
                    writerow(writer, input_ids, current)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('output_csv')
    argp.add_argument('--num-questions-per-assignment', type=int, default=5)
    args = argp.parse_args()
    main(args)