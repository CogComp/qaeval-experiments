import argparse
import csv
import html
import json
from collections import defaultdict
from sacrerouge.io import JsonlReader, JsonlWriter
from uuid import uuid4


def load_prompts(file_path: str):
    prompts = {}
    with JsonlReader(file_path) as f:
        for instance in f:
            prompts[instance['prompt_id']] = instance
    return prompts


def load_annotations(file_path: str):
    annotations = defaultdict(list)
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                prompt_ids_index = row.index('Input.prompt_ids')
                question_indices = []
                index = 0
                while f'Answer.question_{index}' in row:
                    question_indices.append(row.index(f'Answer.question_{index}'))
                    index += 1
            else:
                prompt_ids = json.loads(html.unescape(row[prompt_ids_index]))
                for prompt_id, index in zip(prompt_ids, question_indices):
                    question = row[index].strip()
                    assert len(question) > 0
                    annotations[prompt_id].append(question)
    return annotations


def remap_questions(prompts, annotations):
    remapping = defaultdict(lambda: defaultdict(list))
    count = 0
    for prompt_id in sorted(annotations.keys()):
        if prompt_id not in prompts:
            print(f'Skipping prompt {prompt_id}')
            continue
        count += 1
        prompt = prompts[prompt_id]
        instance_id = prompt['instance_id']
        annotator = prompt['annotator']
        questions = annotations[prompt_id]
        for question in questions:
            remapping[instance_id][annotator].append({
                'question_id': str(uuid4()),
                'prompt_id': prompt_id,
                'question': question,
                'answer': prompt['answer'],
                'alternative_answers': prompt['coreference_cluster']
            })
    print(f'Remapped {count} prompts')
    return remapping


def main(args):
    prompts = load_prompts(args.prompt_jsonl)
    annotations = load_annotations(args.input_csv)
    questions_dict = remap_questions(prompts, annotations)

    with JsonlWriter(args.output_jsonl) as out:
        with JsonlReader(args.candidates_jsonl) as f:
            for data in f:
                instance_id = data['instance_id']
                for reference in data['references']:
                    annotator = reference['summarizer_id']
                    reference['questions'] = questions_dict[instance_id][annotator]
                out.write(data)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('candidates_jsonl')
    argp.add_argument('input_csv')
    argp.add_argument('prompt_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)