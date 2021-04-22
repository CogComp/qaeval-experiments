import argparse
from sacrerouge.io import JsonlReader, JsonlWriter


def main(args):
    errors = set()
    with JsonlWriter(args.output_questions_jsonl) as out:
        with JsonlReader(args.input_questions_jsonl) as f:
            for instance in f:
                for reference in instance['references']:
                    new_questions = []
                    for question in reference['questions']:
                        if question['question'] == 'error':
                            errors.add(question['prompt_id'])
                            print(f'Error: {question["prompt_id"]}')
                        else:
                            new_questions.append(question)

                    if len(new_questions) > 0:
                        reference['questions'] = new_questions
                out.write(instance)

    with JsonlWriter(args.output_prompts_jsonl) as out:
        with JsonlReader(args.input_prompts_jsonl) as f:
            for instance in f:
                if instance['prompt_id'] not in errors:
                    out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_questions_jsonl')
    argp.add_argument('input_prompts_jsonl')
    argp.add_argument('output_questions_jsonl')
    argp.add_argument('output_prompts_jsonl')
    args = argp.parse_args()
    main(args)