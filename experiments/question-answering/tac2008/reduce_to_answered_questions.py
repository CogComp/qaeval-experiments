import argparse
from sacrerouge.io import JsonlReader, JsonlWriter
from typing import Set, Tuple


def load_answered_questions(file_path: str) -> Set[Tuple[str, str, str, str]]:
    aqs = set()
    with JsonlReader(file_path) as f:
        for instance in f:
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            for reference in instance['references']:
                reference_id = reference['summarizer_id']
                for question in reference['questions']:
                    prompt_id = question['prompt_id']
                    if len(question['predictions']) > 0:
                        aqs.add((instance_id, summarizer_id, reference_id, prompt_id))
    return aqs


def main(args):
    aqs = load_answered_questions(args.expert_answers_jsonl)
    with JsonlWriter(args.output_jsonl) as out:
        for instance in JsonlReader(args.questions_jsonl).read():
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            new_references = []
            for reference in instance['references']:
                reference_id = reference['summarizer_id']
                new_questions = []
                for question in reference['questions']:
                    prompt_id = question['prompt_id']
                    key = (instance_id, summarizer_id, reference_id, prompt_id)
                    if key in aqs:
                        new_questions.append(question)

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
    argp.add_argument('expert_answers_jsonl')
    argp.add_argument('questions_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)