import argparse
import json
import os
from collections import defaultdict
from uuid import uuid4


def load_questions(file_path: str):
    questions = defaultdict(lambda: defaultdict(list))
    with open(file_path, 'r') as f:
        for line in f:
            data = json.loads(line)
            instance_id = data['instance_id']
            annotator = data['annotator']
            prompt_id = data['prompt_id']
            group_id = data['group_id'] if 'group_id' in data else None
            question = data['question']
            answer = data['answer']
            coreference_cluster = data['coreference_cluster']

            questions[instance_id][annotator].append({
                'question_id': str(uuid4()),
                'prompt_id': prompt_id,
                'group_id': group_id,
                'question': question,
                'answer': answer,
                'alternative_answers': coreference_cluster
            })
    return questions


def main(args):
    questions_dict = load_questions(args.questions_jsonl)

    dirname = os.path.dirname(args.output_jsonl)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(args.output_jsonl, 'w') as out:
        with open(args.summaries_jsonl, 'r') as f:
            for line in f:
                data = json.loads(line)
                instance_id = data['instance_id']
                for reference in data['references']:
                    annotator = reference['summarizer_id']
                    reference['questions'] = questions_dict[instance_id][annotator]
                out.write(json.dumps(data) + '\n')


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('summaries_jsonl')
    argp.add_argument('questions_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)