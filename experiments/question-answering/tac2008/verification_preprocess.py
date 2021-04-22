import argparse
import csv
import os
from sacrerouge.io import JsonlReader


def main(args):
    dirname = os.path.dirname(args.output_csv)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(args.output_csv, 'w') as out:
        writer = csv.writer(out)
        writer.writerow([
            'instance_id',
            'summarizer_id',
            'prompt_id',
            'summary',
            'question',
            'answer',
            'prediction'
        ])
        seen = set()
        num_exact = 0
        num_skipped = 0
        num_written = 0
        for file_path in [args.expert_answers_jsonl, args.model_answers_jsonl]:
            with JsonlReader(file_path) as f:
                for instance in f:
                    instance_id = instance['instance_id']
                    summarizer_id = instance['summarizer_id']
                    summary = instance['summary']['text']
                    if isinstance(summary, list):
                        summary = ' '.join(summary)
                    for reference in instance['references']:
                        for question_dict in reference['questions']:
                            prompt_id = question_dict['prompt_id']
                            question = question_dict['question']
                            answer = question_dict['answer']
                            prediction = question_dict['predictions'][0]['answer']
                            probability = question_dict['predictions'][0]['probability']
                            null_probability = question_dict['predictions'][0]['null_probability']
                            is_answerable = probability > null_probability

                            if is_answerable:
                                # Don't bother labeling if they're exactly the same
                                if prediction is None:
                                    # I think there were a handful of annotation errors in which the prediction is None.
                                    # Just skip them -- there aren't enough to change the overall numbers.
                                    continue
                                if answer.lower() == prediction.lower():
                                    num_exact += 1
                                    continue

                                # Skip duplicates across model and expert
                                key = (instance_id, summarizer_id, prompt_id, prediction)
                                if key in seen:
                                    num_skipped += 1
                                    continue
                                seen.add(key)

                                num_written += 1
                                writer.writerow([
                                    instance_id,
                                    summarizer_id,
                                    prompt_id,
                                    summary,
                                    question,
                                    answer,
                                    prediction
                                ])

    print('Num rows written', num_written)
    print('Num exact match skipped', num_exact)
    print('Num duplicates skipped', num_skipped)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('expert_answers_jsonl')
    argp.add_argument('model_answers_jsonl')
    argp.add_argument('output_csv')
    args = argp.parse_args()
    main(args)