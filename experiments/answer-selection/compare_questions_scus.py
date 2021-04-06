import argparse
import csv
from collections import defaultdict
from sacrerouge.data import Pyramid
from sacrerouge.io import JsonlReader
from typing import Dict


def load_annotations(file_path: str):
    annotations = defaultdict(lambda: defaultdict(dict))
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                instance_id_index = row.index('instance_id')
                annotator_index = row.index('annotator')
                question_id_index = row.index('question_id')
                scus_index = row.index('scus')
                context_index = row.index('context')
                sentence_index = row.index('sentence')
                question_index = row.index('question_text')
                answer_index = row.index('answer')
                comments_index = row.index('comments')
                continue

            instance_id = row[instance_id_index]
            annotator = row[annotator_index]
            question_id = row[question_id_index]
            scus = row[scus_index]
            if len(scus.strip()) == 0:
                scus = []
            else:
                scus = list(map(int, scus.split(',')))
            annotations[instance_id][annotator][question_id] = {
                'instance_id': instance_id,
                'annotator': annotator,
                'question_id': question_id,
                'context': row[context_index],
                'sentence': row[sentence_index],
                'question': row[question_index],
                'answer': row[answer_index],
                'scus': scus,
                'comments': row[comments_index]
            }
    return annotations


def load_questions(file_path: str):
    questions = {}
    for instance in JsonlReader(file_path).read():
        for reference in instance['references']:
            for question in reference['questions']:
                questions[question['question_id']] = question
    return questions


def main(args):
    pyramids: Dict[str, Pyramid] = {pyramid.instance_id: pyramid for pyramid in JsonlReader(args.pyramid_jsonl, Pyramid).read()}
    annotations = load_annotations(args.question_to_scu_csv)

    summary_coverages = []
    instance_coverages = []

    num_questions_with_scu = 0
    num_questions_without_scu = 0
    precisions = []

    missing_scus_map = {}
    no_scus_map = defaultdict(list)

    num_questions = 0
    num_summaries = 0

    for instance_id in annotations.keys():
        annotators = list(annotations[instance_id].keys())
        pyramid = pyramids[instance_id]

        all_pyramid_scus = set()
        all_question_scus = set()
        for annotator in annotators:
            index = pyramid.summarizer_ids.index(annotator)
            pyramid_scus = pyramid.get_scu_id_set(index)
            all_pyramid_scus |= pyramid_scus

            num_questions_with_scu_summary = 0
            num_questions_without_scu_summary = 0
            question_scus = set()
            for annotation in annotations[instance_id][annotator].values():
                scus = annotation['scus']
                question_scus |= set(scus)
                if len(scus) > 0:
                    num_questions_with_scu_summary += 1
                else:
                    num_questions_without_scu_summary += 1
                    no_scus_map[(instance_id, annotator)].append(annotation)

                num_questions += 1
            all_question_scus |= question_scus

            summary_intersection = pyramid_scus & question_scus
            summary_coverages.append(len(summary_intersection) / len(pyramid_scus))

            num_questions_with_scu += num_questions_with_scu_summary
            num_questions_without_scu += num_questions_without_scu_summary
            precisions.append(num_questions_with_scu_summary / (num_questions_with_scu_summary + num_questions_without_scu_summary))

            missing_scus_map[(instance_id, annotator)] = ','.join(list(map(str, sorted(pyramid_scus - question_scus))))

            num_summaries += 1

        instance_intersection = all_pyramid_scus & all_question_scus
        instance_coverages.append(len(instance_intersection) / len(all_pyramid_scus))

    num_questions = num_questions_with_scu + num_questions_without_scu
    percent_questions_with_scu = num_questions_with_scu / num_questions
    print(f'Percent of questions that map to at least 1 SCU (overall): {num_questions_with_scu} / {num_questions} = {percent_questions_with_scu}')
    print(f'Percent of questions that map to at least 1 SCU (summary-average): {sum(precisions) / len(precisions)}')

    avg_summary_coverage = sum(summary_coverages) / len(summary_coverages)
    print(f'Average percent of SCUs covered at reference-level: {avg_summary_coverage}')

    avg_instance_coverage = sum(instance_coverages) / len(instance_coverages)
    print(f'Average percent of SCUs covered at instance-level: {avg_instance_coverage}')

    print(f'Total number of questions: {num_questions}')
    print(f'Average number of questions per summary: {num_questions / num_summaries}')

    with open(args.missing_scus_tsv, 'w') as out:
        for (instance_id, annotator), scus in missing_scus_map.items():
            out.write(f'{instance_id}\t{annotator}\t{scus}\n')

    with open(args.questions_no_scus_tsv, 'w') as out:
        for (instance_id, annotator), annotations in no_scus_map.items():
            for annotation in annotations:
                out.write('\t'.join([
                    instance_id,
                    annotator,
                    annotation['question']
                ]) + '\n')


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('pyramid_jsonl')
    argp.add_argument('question_to_scu_csv')
    argp.add_argument('missing_scus_tsv')
    argp.add_argument('questions_no_scus_tsv')
    args = argp.parse_args()
    main(args)