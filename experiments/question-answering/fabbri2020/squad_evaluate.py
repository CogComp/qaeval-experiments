import argparse
import collections
import json
import os
import re
import string
from sacrerouge.io import JsonlReader
from typing import Dict, Tuple


def load_answers(file_path: str, summarizer_type: str) -> Dict[str, Tuple[bool, str]]:
    answers = {}
    with JsonlReader(file_path) as f:
        for instance in f:
            instance_id = instance['instance_id']
            summarizer_id = instance['summarizer_id']
            if summarizer_type == 'all' or (summarizer_type == instance['summarizer_type']):
                for reference in instance['references']:
                    for question in reference['questions']:
                        prompt_id = question['prompt_id']
                        assert len(question['predictions']) == 1
                        is_answerable = question['predictions'][0]['probability'] > question['predictions'][0]['null_probability']
                        if is_answerable:
                            prediction = question['predictions'][0]['answer']
                        else:
                            prediction = ''

                        if prediction is None:
                            print(f'Skipping ({instance_id}, {summarizer_id}, {prompt_id}) due to unexpected `None` answer, '
                                  f'which is likely due to an annotation error')
                            continue

                        key = (instance_id, summarizer_id, prompt_id)
                        assert key not in answers
                        answers[key] = (is_answerable, prediction)
    return answers


def calculate_is_answerable_stats(ground_truth: Dict[str, Tuple[bool, str]],
                                  predictions: Dict[str, Tuple[bool, str]],
                                  positive_weight: float,
                                  negative_weight: float) -> Dict[str, float]:
    tp, fp, fn, tn = 0, 0, 0, 0
    for key in ground_truth.keys():
        gt_is_answerable, _ = ground_truth[key]
        pred_is_answerable, _ = predictions[key]
        if gt_is_answerable:
            if pred_is_answerable:
                tp += positive_weight
            else:
                fn += positive_weight
        else:
            if pred_is_answerable:
                fp += negative_weight
            else:
                tn += negative_weight

    p = tp / (tp + fp)
    r = tp / (tp + fn)
    f1 = (2 * p * r) / (p + r)
    num_gt_positive = tp + fn
    num_gt_negative = tn + fp
    portion_gt_positive = num_gt_positive / (num_gt_positive + num_gt_negative)
    return {
        'precision': p,
        'recall': r,
        'f1': f1,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn,
        'ground_truth_num_positive': num_gt_positive,
        'ground_truth_num_negative': num_gt_negative,
        'portion_ground_truth_positive': portion_gt_positive
    }


# https://github.com/huggingface/transformers/blob/master/src/transformers/data/metrics/squad_metrics.py
def normalize_answer(s):
    """Lower text and remove punctuation, articles and extra whitespace."""

    def remove_articles(text):
        regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
        return re.sub(regex, " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def get_tokens(s):
    if not s:
        return []
    return normalize_answer(s).split()


def compute_exact(a_gold, a_pred):
    return int(normalize_answer(a_gold) == normalize_answer(a_pred))


def compute_f1(a_gold, a_pred):
    gold_toks = get_tokens(a_gold)
    pred_toks = get_tokens(a_pred)
    common = collections.Counter(gold_toks) & collections.Counter(pred_toks)
    num_same = sum(common.values())
    if len(gold_toks) == 0 or len(pred_toks) == 0:
        # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
        return int(gold_toks == pred_toks)
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(pred_toks)
    recall = 1.0 * num_same / len(gold_toks)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1


def calculate_squad_metrics(ground_truth: Dict[str, Tuple[bool, str]],
                            predictions: Dict[str, Tuple[bool, str]],
                            positive_weight: float,
                            negative_weight: float) -> Dict[str, float]:
    em = 0
    f1 = 0
    num = 0
    for key in ground_truth.keys():
        is_answerable, gt_prediction = ground_truth[key]
        _, pred_prediction = predictions[key]
        weight = positive_weight if is_answerable else negative_weight
        em += compute_exact(gt_prediction, pred_prediction) * weight
        f1 += compute_f1(gt_prediction, pred_prediction) * weight
        num += weight
    return {
        'exact-match': em / num,
        'f1': f1 / num,
        'num_examples': num
    }


def select_answerable_only(ground_truth: Dict[str, Tuple[bool, str]],
                           predictions: Dict[str, Tuple[bool, str]]) -> Dict[str, Tuple[bool, str]]:
    gt_answerable_only = {}
    predictions_answerable_only = {}
    for key, (gt_is_answerable, _) in ground_truth.items():
        if key in predictions and gt_is_answerable:
            pred_is_answerable, _ = predictions[key]
            if pred_is_answerable:
                gt_answerable_only[key] = ground_truth[key]
                predictions_answerable_only[key] = predictions[key]
    return gt_answerable_only, predictions_answerable_only


def main(args):
    ground_truth = load_answers(args.expert_answers_jsonl, args.summarizer_type)
    predictions = load_answers(args.model_answers_jsonl, args.summarizer_type)
    if len(ground_truth) != len(predictions):
        print(f'Warning: Different number of outputs. GT: {len(ground_truth)}, Pred: {len(predictions)}. '
              f'Evaluating on just the GT subset')

    gt_answerable_only, predictions_answerable_only = select_answerable_only(ground_truth, predictions)

    # Calculate the weights to treat both positive and negative evenly
    num_positive = 0
    num_negative = 0
    for (is_answerable, _) in ground_truth.values():
        if is_answerable:
            num_positive += 1
        else:
            num_negative += 1
    positive_weight = 1.0
    negative_weight = num_positive / num_negative

    metrics = {
        'is_answerable': {
            'unweighted': calculate_is_answerable_stats(ground_truth, predictions, 1.0, 1.0),
            'weighted': calculate_is_answerable_stats(ground_truth, predictions, positive_weight, negative_weight),
        },
        'squad': {
            'unweighted': calculate_squad_metrics(ground_truth, predictions, 1.0, 1.0),
            'weighted': calculate_squad_metrics(ground_truth, predictions, positive_weight, negative_weight)
        },
        'is-answerable-only': {
            'squad': calculate_squad_metrics(gt_answerable_only, predictions_answerable_only, 1.0, 1.0)
        }
    }

    dirname = os.path.dirname(args.output_json)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(args.output_json, 'w') as out:
        out.write(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('expert_answers_jsonl')
    argp.add_argument('model_answers_jsonl')
    argp.add_argument('output_json')
    argp.add_argument('--summarizer-type', choices=['peer', 'all', 'reference'])
    args = argp.parse_args()
    main(args)