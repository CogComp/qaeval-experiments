import argparse
import hashlib
import json
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Any, Dict, Tuple


def get_prediction_id(instance_id: str, summarizer_id: str, question_id: str) -> str:
    m = hashlib.md5()
    m.update(instance_id.encode())
    m.update(summarizer_id.encode())
    m.update(question_id.encode())
    return m.hexdigest()


def load_answers(file_path: str) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
    answers = {}
    data = json.load(open(file_path, 'r'))
    for key, answer_list in data.items():
        instance_id, summarizer_id, question_id = key.split('_')
        best_non_null = None
        best_non_null_prob = None
        null_prob = None
        for answer_dict in answer_list:
            if answer_dict['text'] == '':
                null_prob = answer_dict['probability']
            elif best_non_null is None:
                best_non_null = answer_dict['text']
                best_non_null_prob = answer_dict['probability']

            if best_non_null_prob is not None and null_prob is not None:
                break

        assert best_non_null_prob and null_prob
        answers[(instance_id, summarizer_id, question_id)] = {
            'prediction_id': get_prediction_id(instance_id, summarizer_id, question_id),
            'answer': best_non_null,
            'probability': best_non_null_prob,
            'null_probability': null_prob
        }

    return answers


def main(args):
    answers = load_answers(args.nbest_file)

    with JsonlWriter(args.output_jsonl) as out:
        with JsonlReader(args.questions_jsonl) as f:
            for instance in f:
                instance_id = instance['instance_id']
                summarizer_id = instance['summarizer_id']
                for reference in instance['references']:
                    for question_dict in reference['questions']:
                        question_id = question_dict['question_id']
                        answer = answers[(instance_id, summarizer_id, question_id)]
                        question_dict['predictions'] = [answer]

                out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('questions_jsonl')
    argp.add_argument('nbest_file')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)