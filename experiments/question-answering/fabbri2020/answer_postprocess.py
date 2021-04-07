import argparse
import csv
import hashlib
import html
import json
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import List


def get_prediction_id(instance_id: str, summarizer_id: str, question_id: str) -> str:
    m = hashlib.md5()
    m.update(instance_id.encode())
    m.update(summarizer_id.encode())
    m.update(question_id.encode())
    return m.hexdigest()


def load_annotations(file_paths: List[str]):
    annotations = {}

    for file_path in file_paths:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0:
                    input_ids_index = row.index('Input.input_ids')
                    index_to_is_answerable_index = {}
                    index_to_answer_index = {}
                    index = 0
                    while f'Answer.isAnswerable_{index}' in row:
                        index_to_is_answerable_index[index] = row.index(f'Answer.isAnswerable_{index}')
                        if f'Answer.answer_{index}' in row:
                            index_to_answer_index[index] = row.index(f'Answer.answer_{index}')
                        index += 1
                else:
                    input_ids_list = json.loads(html.unescape(row[input_ids_index]))
                    for j, input_ids in enumerate(input_ids_list):
                        is_answerable = row[index_to_is_answerable_index[j]]
                        answer = None
                        if j in index_to_answer_index:
                            answer = row[index_to_answer_index[j]].strip()
                            if len(answer) == 0:
                                answer = None

                        annotations[tuple(input_ids)] = {
                            'answer': answer,
                            'is_answerable': is_answerable.lower() == 'true'
                        }

    return annotations



def main(args):
    annotations = load_annotations(args.mturk_csvs)

    with JsonlWriter(args.output_jsonl) as out:
        with JsonlReader(args.questions_jsonl) as f:
            for instance in f:
                instance_id = instance['instance_id']
                summarizer_id = instance['summarizer_id']
                new_references = []
                for reference in instance['references']:
                    # only keep questions we have answers for
                    reference_id = reference['summarizer_id']
                    new_questions = []
                    for question_dict in reference['questions']:
                        question_id = question_dict['question_id']
                        prediction_id = get_prediction_id(instance_id, summarizer_id, question_id)

                        if (instance_id, summarizer_id, question_id) in annotations:
                            annotation = annotations[(instance_id, summarizer_id, question_id)]
                            answer = annotation['answer']
                            is_answerable = annotation['is_answerable']

                            if is_answerable:
                                prob = 1.0
                                null_prob = 0.0
                            else:
                                prob = 0.0
                                null_prob = 1.0

                            question_dict['predictions'] = [{
                                'prediction_id': prediction_id,
                                'answer': answer,
                                'probability': prob,
                                'null_probability': null_prob
                            }]
                            new_questions.append(question_dict)

                    if len(reference['questions']) != len(new_questions):
                        print(f'({instance_id}, {summarizer_id}, {reference_id}) only has {len(new_questions)} / {len(reference["questions"])} answered')

                    if len(new_questions) > 0:
                        reference['questions'] = new_questions
                        new_references.append(reference)

                if len(instance['references']) != len(new_references):
                    print(f'({instance_id}, {summarizer_id}) only has {len(new_references)} / {len(instance["references"])} references')

                if len(new_references) > 0:
                    instance['references'] = new_references
                    out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('--questions-jsonl')
    argp.add_argument('--mturk-csvs', nargs='+')
    argp.add_argument('--output-jsonl')
    args = argp.parse_args()
    main(args)