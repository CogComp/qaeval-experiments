import argparse
import hashlib
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Any, Dict


def get_prompt_id(candidate_id: str):
    # Right now, there is a 1:1 mapping between the candidate and the prompt
    return hashlib.md5(candidate_id.encode()).hexdigest()


def process_instance(instance: Dict[str, Any]):
    prompts = []
    for candidate in instance['summary']['candidates']:
        prompts.append({
            'instance_id': instance['instance_id'],
            'annotator': instance['summarizer_id'],
            'candidate_id': candidate['candidate_id'],
            'group_id': candidate['group_id'],
            'prompt_id': get_prompt_id(candidate['candidate_id']),
            'context': instance['summary']['text'],
            'answer': candidate['candidate'],
            'answer_start': candidate['candidate_start'],
            'answer_end': candidate['candidate_end'],
            'sent_start': candidate['sent_start'],
            'sent_end': candidate['sent_end'],
            'coreference_cluster': candidate['coreference_cluster']
        })
    return prompts


def main(args):
    with JsonlWriter(args.output_jsonl) as out:
        for instance in JsonlReader(args.candidates_jsonl).read():
            if instance['summarizer_type'] == 'reference':
                for prompt in process_instance(instance):
                    out.write(prompt)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('candidates_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)