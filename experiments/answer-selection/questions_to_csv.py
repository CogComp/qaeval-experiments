import argparse
import csv
from collections import defaultdict
from sacrerouge.io import JsonlReader
from typing import Dict, Set


def load_questions(file_path: str):
    questions = {}
    with JsonlReader(file_path) as f:
        for instance in f:
            for reference in instance['references']:
                for question in reference['questions']:
                    prompt_id = question['prompt_id']
                    questions[prompt_id] = question
    return questions


def load_prompts(file_path: str):
    prompts = defaultdict(lambda: defaultdict(list))
    with JsonlReader(file_path) as f:
        for instance in f:
            instance_id = instance['instance_id']
            annotator = instance['annotator']
            prompts[instance_id][annotator].append(instance)
    return prompts


def load_prompt_to_strategy_map(prompts_ner_jsonl: str,
                                prompts_top_nps_jsonl: str,
                                prompts_all_nps_jsonl: str) -> Dict[str, Set[str]]:
    prompt_to_strategy = defaultdict(set)
    for strategy, file_path in zip(['ner', 'top-nps', 'all-nps'], [prompts_ner_jsonl, prompts_top_nps_jsonl, prompts_all_nps_jsonl]):
        for instance in JsonlReader(file_path).read():
            prompt_to_strategy[instance['prompt_id']].add(strategy)
    return prompt_to_strategy


def main(args):
    questions = load_questions(args.questions_jsonl)
    prompts = load_prompts(args.prompts_jsonl)

    prompt_to_strategies = load_prompt_to_strategy_map(args.prompts_ner_jsonl,
                                                       args.prompts_top_nps_jsonl,
                                                       args.prompts_all_nps_jsonl)

    with open(args.output_csv, 'w') as out:
        writer = csv.writer(out)
        writer.writerow([
            'instance_id',
            'annotator',
            'question_id',
            'strategies',
            'context',
            'sentence',
            'question_text',
            'answer'
        ])
        for instance_id in sorted(prompts.keys()):
            for annotator in sorted(prompts[instance_id].keys()):
                prompts_list = list(prompts[instance_id][annotator])
                prompts_list.sort(key=lambda p: p['answer_start'])
                for prompt in prompts_list:
                    prompt_id = prompt['prompt_id']
                    annotator = prompt['annotator']
                    context = prompt['context']
                    sentence = context[prompt['sent_start']:prompt['sent_end']]

                    if prompt_id not in questions:
                        print(f'Skipping prompt {prompt_id}')
                        continue

                    question_dict = questions[prompt_id]
                    question_id = question_dict['question_id']
                    question_text = question_dict['question']
                    answer = question_dict['answer']

                    strategies = ','.join(list(sorted(prompt_to_strategies[prompt_id])))

                    writer.writerow([
                        instance_id,
                        annotator,
                        question_id,
                        strategies,
                        context,
                        sentence,
                        question_text,
                        answer
                    ])


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('questions_jsonl')
    argp.add_argument('prompts_jsonl')
    argp.add_argument('prompts_ner_jsonl')
    argp.add_argument('prompts_top_nps_jsonl')
    argp.add_argument('prompts_all_nps_jsonl')
    argp.add_argument('output_csv')
    args = argp.parse_args()
    main(args)