import argparse
import json
import matplotlib
import numpy as np
import os
import scipy.stats
from collections import defaultdict
from glob import glob
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from typing import List

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # Must come after the `matplotlib.use('Agg')` line


def load_correlations(input_dir: str):
    correlations = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for file_path in glob(f'{input_dir}/*/*.json'):
        path = file_path.split('/')
        num_references = int(path[-2])
        data = json.load(open(file_path, 'r'))
        for level in ['summary_level', 'system_level']:
            for coef, symbol in zip(['pearson', 'spearman', 'kendall'], ['r', 'rho', 'tau']):
                correlations[num_references][level][coef].append(data[level][coef][symbol])
    return correlations


# https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
def get_confidence_interval_delta(data: List[float], confidence: float) -> float:
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n - 1)
    return h


def get_points(correlations_dict, coefficient: str):
    x = []
    y_summary = []
    y_system = []
    err_summary = []
    err_system = []

    for num_references in sorted(correlations_dict.keys()):
        x.append(num_references)
        mean_summary = np.mean(correlations_dict[num_references]['summary_level'][coefficient])
        mean_system = np.mean(correlations_dict[num_references]['system_level'][coefficient])
        delta_summary = get_confidence_interval_delta(correlations_dict[num_references]['summary_level'][coefficient], 0.95)
        delta_system = get_confidence_interval_delta(correlations_dict[num_references]['system_level'][coefficient], 0.95)

        y_summary.append(mean_summary)
        y_system.append(mean_system)
        err_summary.append(delta_summary)
        err_system.append(delta_system)

    return x, y_summary, y_system, err_summary, err_system



def main(args):
    metric_correlations = load_correlations(args.metric_sample_dir)
    rouge_correlations = load_correlations(args.rouge_sample_dir)
    pyramid_correlations = load_correlations(args.pyramid_sample_dir)
    pyreval_correlations = load_correlations(args.pyreval_sample_dir)
    moverscore_correlations = load_correlations(args.moverscore_sample_dir)
    apes_correlations = load_correlations(args.apes_sample_dir)

    os.makedirs(args.output_dir, exist_ok=True)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for coefficient in ['pearson', 'spearman', 'kendall']:
        print(coefficient)
        output_file = f'{args.output_dir}/{coefficient}.pdf'

        fig = plt.figure()
        linewidth = 2.5

        x, y_summary, y_system, err_summary, err_system = get_points(metric_correlations, coefficient)
        print(f'QA (summary): {y_summary}')
        print(f'QA (system): {y_system}')
        plt.xticks(x)
        plt.errorbar(x, y_summary, yerr=err_summary, label='Metric-Summary-Level', color=colors[0], linestyle='--', linewidth=linewidth)
        plt.errorbar(x, y_system, yerr=err_system, label='Metric-System-Level', color=colors[0], linestyle='-', linewidth=linewidth)

        x, y_summary, y_system, err_summary, err_system = get_points(rouge_correlations, coefficient)
        print(f'ROUGE (summary): {y_summary}')
        print(f'ROUGE (system): {y_system}')
        plt.errorbar(x, y_summary, yerr=err_summary, label='ROUGE-Summary-Level', color=colors[1], linestyle='--', linewidth=linewidth)
        plt.errorbar(x, y_system, yerr=err_system, label='ROUGE-System-Level', color=colors[1], linestyle='-', linewidth=linewidth)

        x, y_summary, y_system, err_summary, err_system = get_points(pyramid_correlations, coefficient)
        print(f'Pyramid (summary): {y_summary}')
        print(f'Pyramid (system): {y_system}')
        plt.errorbar(x, y_summary, yerr=err_summary, label='Pyramid-Summary-Level', color=colors[2], linestyle='--', linewidth=linewidth)
        plt.errorbar(x, y_system, yerr=err_system, label='Pyramid-System-Level', color=colors[2], linestyle='-', linewidth=linewidth)

        x, y_summary, y_system, err_summary, err_system = get_points(pyreval_correlations, coefficient)
        print(f'PyrEval (summary): {y_summary}')
        print(f'PyrEval (system): {y_system}')
        plt.errorbar(x, y_summary, yerr=err_summary, label='PyrEval-Summary-Level', color=colors[3], linestyle='--', linewidth=linewidth)
        plt.errorbar(x, y_system, yerr=err_system, label='PyrEval-System-Level', color=colors[3], linestyle='-', linewidth=linewidth)

        x, y_summary, y_system, err_summary, err_system = get_points(moverscore_correlations, coefficient)
        print(f'MoverScore (summary): {y_summary}')
        print(f'MoverScore (system): {y_system}')
        plt.errorbar(x, y_summary, yerr=err_summary, label='MoverScore-Summary-Level', color=colors[4], linestyle='--',
                     linewidth=linewidth)
        plt.errorbar(x, y_system, yerr=err_system, label='MoverScore-System-Level', color=colors[4], linestyle='-',
                     linewidth=linewidth)

        x, y_summary, y_system, err_summary, err_system = get_points(apes_correlations, coefficient)
        print(f'APES (summary): {y_summary}')
        print(f'APES (system): {y_system}')
        plt.errorbar(x, y_summary, yerr=err_summary, label='APES-Summary-Level', color=colors[5], linestyle='--',
                     linewidth=linewidth)
        plt.errorbar(x, y_system, yerr=err_system, label='APES-System-Level', color=colors[5], linestyle='-',
                     linewidth=linewidth)

        if args.metric_name == 'qa-eval_f1':
            # This is the paper figure
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            plt.xlabel('Number of Reference Summaries', fontsize=16)
            plt.ylabel(f'{coefficient[0].upper() + coefficient[1:]} Coefficient', fontsize=16)
            # https://stackoverflow.com/questions/4700614/how-to-put-the-legend-out-of-the-plot/43439132#43439132
            plt.legend(handles=[
                Patch(facecolor=colors[0], label='QAEval-F1'),
                Patch(facecolor=colors[1], label='ROUGE-1'),
                Patch(facecolor=colors[2], label='Pyramid Score'),
                Patch(facecolor=colors[3], label='PyrEval'),
                Patch(facecolor=colors[4], label='MoverScore'),
                Patch(facecolor=colors[5], label='APES'),
                Line2D([0], [0], color='k', linestyle='-', label='System-Level'),
                Line2D([0], [0], color='k', linestyle='--', label='Summary-Level'),
            ], prop={'size': 12}, bbox_to_anchor=(0, 1.02, 1, 0.2), loc='lower left', ncol=3, mode='expand', columnspacing=30)
        else:
            plt.xlabel('Number of Reference Summaries')
            plt.ylabel(f'{coefficient} coefficient')
            plt.legend(handles=[
                Patch(facecolor=colors[0], label=args.metric_name),
                Patch(facecolor=colors[1], label=args.rouge_metric),
                Patch(facecolor=colors[2], label=args.pyramid_metric),
                Patch(facecolor=colors[3], label=args.pyreval_metric),
                Patch(facecolor=colors[4], label=args.moverscore_metric),
                Patch(facecolor=colors[5], label=args.apes_metric),
                Line2D([0], [0], color='k', linestyle='-', label='System-Level'),
                Line2D([0], [0], color='k', linestyle='--', label='Summary-Level'),
            ])

        plt.tight_layout()
        fig.savefig(output_file)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('summarizer_type')
    argp.add_argument('metric_name')
    argp.add_argument('rouge_metric')
    argp.add_argument('pyramid_metric')
    argp.add_argument('pyreval_metric')
    argp.add_argument('moverscore_metric')
    argp.add_argument('apes_metric')
    argp.add_argument('metric_sample_dir')
    argp.add_argument('rouge_sample_dir')
    argp.add_argument('pyramid_sample_dir')
    argp.add_argument('pyreval_sample_dir')
    argp.add_argument('moverscore_sample_dir')
    argp.add_argument('apes_sample_dir')
    argp.add_argument('output_dir')
    args = argp.parse_args()
    main(args)
