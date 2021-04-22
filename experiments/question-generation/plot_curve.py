import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.stats
from collections import defaultdict
from glob import glob
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from typing import List


def load_correlations(input_dir: str, level: str):
    correlations = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for file_path in glob(f'{input_dir}/*/*.json'):
        path = file_path.split('/')
        num_inputs = int(path[-2])
        data = json.load(open(file_path, 'r'))
        for coef, symbol in zip(['pearson', 'spearman', 'kendall'], ['r', 'rho', 'tau']):
            correlations[num_inputs][level][coef].append(data[level][coef][symbol])
    return correlations


# https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
def get_confidence_interval_delta(data: List[float], confidence: float) -> float:
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n - 1)
    return h


def get_points(correlations_dict, coefficient: str, level: str):
    x = []
    y = []
    err = []

    for num_inputs in sorted(correlations_dict.keys()):
        x.append(num_inputs)
        mean = np.mean(correlations_dict[num_inputs][level][coefficient])
        delta = get_confidence_interval_delta(correlations_dict[num_inputs][level][coefficient], 0.95)
        y.append(mean)
        err.append(delta)

    return x, y, err


def main(args):
    system_expert_correlations = load_correlations(args.expert_input_dir, 'system_level')
    system_model_correlations = load_correlations(args.model_input_dir, 'system_level')

    summary_expert_correlations = load_correlations(args.expert_input_dir, 'summary_level')
    summary_model_correlations = load_correlations(args.model_input_dir, 'summary_level')

    os.makedirs(args.output_dir, exist_ok=True)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for coefficient in ['pearson', 'spearman', 'kendall']:
        output_file = f'{args.output_dir}/{coefficient}.pdf'

        fig = plt.figure()
        linewidth = 2.5
        plt.xlabel('Number of Input Instances', fontsize=16)
        plt.ylabel(f'{coefficient[0].upper() + coefficient[1:]} Coefficient', fontsize=16)

        x, y, err = get_points(system_expert_correlations, coefficient, 'system_level')
        plt.errorbar(x, y, yerr=err, linestyle='-', color=colors[0], linewidth=linewidth)

        x, y, err = get_points(system_model_correlations, coefficient, 'system_level')
        plt.errorbar(x, y, yerr=err, linestyle='-', color=colors[1], linewidth=linewidth)

        x, y, err = get_points(summary_expert_correlations, coefficient, 'summary_level')
        plt.errorbar(x, y, yerr=err, linestyle='--', color=colors[0], linewidth=linewidth)

        x, y, err = get_points(summary_model_correlations, coefficient, 'summary_level')
        plt.errorbar(x, y, yerr=err, linestyle='--', color=colors[1], linewidth=linewidth)

        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        handles = [
            Patch(facecolor=colors[0], label='Expert Questions'),
            Patch(facecolor=colors[1], label='Model Questions'),
            Line2D([0], [0], color='k', linestyle='-', label='System-Level'),
            Line2D([0], [0], color='k', linestyle='--', label='Summary-Level')
        ]
        plt.legend(handles=handles, prop={'size': 12}, loc='upper left')
        plt.grid()
        plt.tight_layout()
        fig.savefig(output_file)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('expert_input_dir')
    argp.add_argument('model_input_dir')
    argp.add_argument('output_dir')
    args = argp.parse_args()
    main(args)
