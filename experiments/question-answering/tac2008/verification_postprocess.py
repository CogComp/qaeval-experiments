import argparse
import csv
import os
from sacrerouge.io import JsonlReader, JsonlWriter


def load_annotations(file_path: str):
    annotations_dict = {}
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                # header
                pass
            else:
                instance_id, summarizer_id, prompt_id, _, _, _, prediction, is_correct, is_intended_answer = row
                is_correct = is_correct.lower() == 'true'
                is_intended_answer = is_intended_answer.lower() == 'true'
                annotations_dict[(instance_id, summarizer_id, prompt_id, prediction)] = (is_correct, is_intended_answer)
    return annotations_dict


def filter_to_summarizer_type(instances, summarizer_type):
    return list(filter(lambda instance: instance['summarizer_type'] == summarizer_type, instances))


def get_ground_truth_answerable(instances):
    is_answerable_dict = {}
    for instance in instances:
        instance_id = instance['instance_id']
        summarizer_id = instance['summarizer_id']
        for reference in instance['references']:
            for question_dict in reference['questions']:
                prompt_id = question_dict['prompt_id']
                probability = question_dict['predictions'][0]['probability']
                null_probability = question_dict['predictions'][0]['null_probability']
                is_answerable = probability > null_probability
                is_answerable_dict[(instance_id, summarizer_id, prompt_id)] = is_answerable
    return is_answerable_dict


def process_expert_answers(instances, annotations_dict, is_answerable_dict) -> None:
    num_answers = 0
    num_correct_intended = 0
    num_correct_unintended = 0
    num_incorrect = 0

    num_unannotated_answers = 0

    for instance in instances:
        instance_id = instance['instance_id']
        summarizer_id = instance['summarizer_id']
        summary = ' '.join(instance['summary']['text'])
        for reference in instance['references']:
            for question_dict in reference['questions']:
                prompt_id = question_dict['prompt_id']
                question = question_dict['question']
                answer = question_dict['answer']
                prediction = question_dict['predictions'][0]['answer']
                probability = question_dict['predictions'][0]['probability']
                null_probability = question_dict['predictions'][0]['null_probability']
                is_answerable = probability > null_probability

                # A small number of labeling errors where prediction is None should not impact overall scores
                if is_answerable and prediction is not None:
                    is_em = answer.lower() == prediction.lower()
                    if is_em:
                        is_correct = True
                        is_intended_answer = True
                    else:
                        key = (instance_id, summarizer_id, prompt_id, prediction)
                        if key in annotations_dict:
                            is_correct, is_intended_answer = annotations_dict[key]
                        else:
                            num_unannotated_answers += 1
                            continue
                    num_answers += 1

                    ground_truth_is_answerable = is_answerable_dict[(instance_id, summarizer_id, prompt_id)]
                    if ground_truth_is_answerable:
                        if is_correct and is_intended_answer:
                            num_correct_intended += 1
                        elif is_correct and not is_intended_answer:
                            num_correct_unintended += 1
                        elif not is_correct:
                            num_incorrect += 1
                    else:
                        # Always true -- that's how these were decided
                        assert False  # Just in case
                        pass

    accuracy = num_correct_intended / num_answers
    accuracy_unintended = (num_correct_intended + num_correct_unintended) / num_answers

    print('Expert Answers Analysis')
    print('Total number of answers', num_answers)
    print('Total number of correct and intended answers', num_correct_intended)
    print('Total number of correct and unintended answers', num_correct_unintended)
    print('Total number of incorrect answers (disagrees with previous ground truth)', num_incorrect)
    print('Accuracy of intended answer', accuracy)
    print('Accuracy of intended or unintended answer', accuracy_unintended)


def process_model_answers(instances, annotations_dict, is_answerable_dict,
                          right_for_wrong_reasons_file: str) -> None:
    num_answers = 0
    num_correct_intended = 0
    num_correct_unintended = 0
    num_incorrect_but_correct_is_answerable = 0
    num_right_for_wrong_reasons = 0
    num_incorrect_and_incorrect_is_answerable = 0

    is_answerable_tp = 0
    is_answerable_fp = 0
    is_answerable_fn = 0

    num_unannotated_answers = 0

    dirname = os.path.dirname(right_for_wrong_reasons_file)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(right_for_wrong_reasons_file, 'w') as out:
        writer = csv.writer(out)
        writer.writerow(['instance_id', 'summarizer_id', 'prompt_id' 'summary', 'question', 'answer', 'prediction'])

        for instance in instances:
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            summary = ' '.join(instance['summary']['text'])
            for reference in instance['references']:
                for question_dict in reference['questions']:
                    prompt_id = question_dict['prompt_id']
                    question = question_dict['question']
                    answer = question_dict['answer']
                    prediction = question_dict['predictions'][0]['answer']
                    probability = question_dict['predictions'][0]['probability']
                    null_probability = question_dict['predictions'][0]['null_probability']
                    is_answerable = probability > null_probability

                    ground_truth_is_answerable = is_answerable_dict[(instance_id, summarizer_id, prompt_id)]
                    if is_answerable:
                        is_em = answer.lower() == prediction.lower()
                        if is_em:
                            is_correct = True
                            is_intended_answer = True
                        else:
                            key = (instance_id, summarizer_id, prompt_id, prediction)
                            if key in annotations_dict:
                                is_correct, is_intended_answer = annotations_dict[key]
                            else:
                                num_unannotated_answers += 1
                                continue
                        num_answers += 1

                        if ground_truth_is_answerable:
                            is_answerable_tp += 1
                            if is_correct and is_intended_answer:
                                num_correct_intended += 1
                            elif is_correct and not is_intended_answer:
                                num_correct_unintended += 1
                            elif not is_correct:
                                num_incorrect_but_correct_is_answerable += 1
                            else:
                                # Should not happen
                                assert False
                        else:
                            is_answerable_fp += 1
                            if is_correct:
                                # Answered correctly for the wrong reasons -- these disagree with the
                                # is_answerable ground-truth
                                num_right_for_wrong_reasons += 1
                                writer.writerow([instance_id, summarizer_id, prompt_id, summary, question, answer, prediction])
                            else:
                                num_incorrect_and_incorrect_is_answerable += 1

                    else:
                        # Not answerable
                        if ground_truth_is_answerable:
                            is_answerable_fn += 1



    accuracy = num_correct_intended / num_answers
    accuracy_unintended = (num_correct_intended + num_correct_unintended) / num_answers

    accuracy_given_gt_is_answerable = num_correct_intended / (num_correct_intended + num_correct_unintended + num_incorrect_but_correct_is_answerable)
    accuracy_given_gt_is_answerable_unintended = (num_correct_intended + num_correct_unintended) / (num_correct_intended + num_correct_unintended + num_incorrect_but_correct_is_answerable)

    is_answerable_precision = is_answerable_tp / (is_answerable_tp + is_answerable_fp)
    is_answerable_recall = is_answerable_tp / (is_answerable_tp + is_answerable_fn)
    is_answerable_f1 = (2 * is_answerable_precision * is_answerable_recall) / (is_answerable_precision + is_answerable_recall)

    print('Model Answer Analysis')
    print('Total number of answers', num_answers)
    print('Total number of unannotated answers', num_unannotated_answers)
    print('Total number of correct and intended answers', num_correct_intended)
    print('Total number of correct and unintended answers', num_correct_unintended)
    print('Total number of incorrect answers, but is-answerable is correct', num_incorrect_but_correct_is_answerable)
    print('Total number of correct answers, but correct for the wrong reasons (disagrees with ground truth)', num_right_for_wrong_reasons)
    print('Total number of incorrect answers and is-answerable incorrect', num_incorrect_and_incorrect_is_answerable)
    print('Accuracy of intended answer', accuracy)
    print('Accuracy of intended or unintended answer', accuracy_unintended)
    print('Accuracy given ground-truth question is answerable', accuracy_given_gt_is_answerable)
    print('Accuracy given ground-truth question is answerable and answer could be unintended', accuracy_given_gt_is_answerable_unintended)
    print('Denominator', num_correct_intended + num_correct_unintended + num_incorrect_but_correct_is_answerable)
    print('Is-Answerable F1', is_answerable_f1)


def save_human_judgments(instances, annotations_dict, file_path):
    num_skipped = 0
    with JsonlWriter(file_path) as out:
        for instance in instances:
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            summary = ' '.join(instance['summary']['text'])
            new_references = []
            for reference in instance['references']:
                new_questions = []
                for question_dict in reference['questions']:
                    prompt_id = question_dict['prompt_id']
                    question = question_dict['question']
                    answer = question_dict['answer']
                    prediction = question_dict['predictions'][0]['answer']
                    probability = question_dict['predictions'][0]['probability']
                    null_probability = question_dict['predictions'][0]['null_probability']
                    is_answerable = probability > null_probability

                    # A small number of labeling errors where prediction is None should not impact overall scores
                    if is_answerable and prediction is not None:
                        is_em = answer.lower() == prediction.lower()
                        if is_em:
                            is_correct = True
                            is_intended = True
                        else:
                            key = (instance_id, summarizer_id, prompt_id, prediction)
                            if key in annotations_dict:
                                is_correct, is_intended = annotations_dict[key]
                            else:
                                # Not annotated yet
                                num_skipped += 1
                                continue
                    else:
                        # Don't give credit for this answer since the model didn't output anything
                        is_correct = False
                        is_intended = False

                    question_dict['predictions'][0]['is_correct'] = is_correct and is_intended
                    new_questions.append(question_dict)

                if len(new_questions) > 0:
                    reference['questions'] = new_questions
                    new_references.append(reference)

            if len(new_references) > 0:
                instance['references'] = new_references
                out.write(instance)

        print('Number of answers skipped', num_skipped)


def main(args):
    annotations_dict = load_annotations(args.annotations_csv)
    expert_answers = JsonlReader(args.expert_answers_jsonl).read()
    model_answers = JsonlReader(args.model_answers_jsonl).read()

    expert_answers = filter_to_summarizer_type(expert_answers, args.summarizer_type)
    model_answers = filter_to_summarizer_type(model_answers, args.summarizer_type)

    is_answerable_dict = get_ground_truth_answerable(expert_answers)

    process_expert_answers(expert_answers, annotations_dict, is_answerable_dict)
    print()
    process_model_answers(model_answers, annotations_dict, is_answerable_dict, args.output_right_for_wrong_reasons_csv)
    print()

    save_human_judgments(expert_answers, annotations_dict, args.output_expert_jsonl)
    save_human_judgments(model_answers, annotations_dict, args.output_model_jsonl)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('expert_answers_jsonl')
    argp.add_argument('model_answers_jsonl')
    argp.add_argument('annotations_csv')
    argp.add_argument('summarizer_type')
    argp.add_argument('output_right_for_wrong_reasons_csv')
    argp.add_argument('output_expert_jsonl')
    argp.add_argument('output_model_jsonl')
    args = argp.parse_args()
    main(args)