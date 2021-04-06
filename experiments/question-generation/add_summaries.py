import argparse
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Any, Dict, List, Tuple


def load_reference_to_questions(file_path: str) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    reference_to_questions = {}
    for instance in JsonlReader(file_path).read():
        instance_id = instance['instance_id']
        for reference in instance['references']:
            summarizer_id = reference['summarizer_id']
            if len(reference['questions']) > 0:
                reference_to_questions[(instance_id, summarizer_id)] = reference['questions']
    return reference_to_questions


def main(args):
    reference_to_questions = load_reference_to_questions(args.questions_jsonl)
    with JsonlWriter(args.output_jsonl) as out:
        for instance in JsonlReader(args.all_summaries_jsonl).read():
            instance_id = instance['instance_id']

            # Also fix the summary so it's a string
            instance['summary']['text'] = ' '.join(instance['summary']['text'])
            if len(instance['summary']['text']) == 0:
                continue

            new_references = []
            for reference in instance['references']:
                summarizer_id = reference['summarizer_id']
                key = (instance_id, summarizer_id)
                if key in reference_to_questions:
                    reference['questions'] = reference_to_questions[key]
                    new_references.append(reference)
                else:
                    reference['questions'] = []

            if len(new_references) > 0:
                instance['references'] = new_references
                out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('all_summaries_jsonl')
    argp.add_argument('questions_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)