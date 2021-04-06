import argparse
from collections import defaultdict
from sacrerouge.io import JsonlReader, JsonlWriter


def main(args):
    # Make one pass over the inputs to collect all of the questions
    questions = defaultdict(dict)
    for file_path in args.input_files:
        for instance in JsonlReader(file_path).read():
            instance_id = instance['instance_id']
            for reference in instance['references']:
                summarizer_id = reference['summarizer_id']
                for question_dict in reference['questions']:
                    question_id = question_dict['question_id']
                    questions[(instance_id, summarizer_id)][question_id] = question_dict

    # Make one pass over just the first file to collect all of the questions
    with JsonlWriter(args.output_file) as out:
        first_file = args.input_files[0]
        for instance in JsonlReader(first_file).read():
            instance_id = instance['instance_id']
            for reference in instance['references']:
                summarizer_id = reference['summarizer_id']
                question_list = list(questions[(instance_id, summarizer_id)].values())
                reference['questions'] = question_list
            out.write(instance)

if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('--input-files', nargs='+')
    argp.add_argument('--output-file')
    args = argp.parse_args()
    main(args)