import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
from typing import List


def plot_heatmap(matrix: np.array, labels: List[str], output_file: str) -> None:
    sns.set(font_scale=1.4)
    fig = plt.figure()
    sns.heatmap(matrix, annot=True, fmt='.2f', cmap='Blues', xticklabels=labels, yticklabels=labels) #, annot_kws={'size': 16})
    fig.tight_layout()
    fig.savefig(output_file)


def main(args):
    summary_pearson = np.zeros((len(args.metrics), len(args.metrics)))
    summary_spearman = np.zeros((len(args.metrics), len(args.metrics)))
    summary_kendall = np.zeros((len(args.metrics), len(args.metrics)))

    system_pearson = np.zeros((len(args.metrics), len(args.metrics)))
    system_spearman = np.zeros((len(args.metrics), len(args.metrics)))
    system_kendall = np.zeros((len(args.metrics), len(args.metrics)))

    global_pearson = np.zeros((len(args.metrics), len(args.metrics)))
    global_spearman = np.zeros((len(args.metrics), len(args.metrics)))
    global_kendall = np.zeros((len(args.metrics), len(args.metrics)))

    for i, metric1 in enumerate(args.metrics):
        for j, metric2 in enumerate(args.metrics):
            data = json.load(open(f'{args.input_dir}/{metric1}/{metric2}.json', 'r'))
            summary_pearson[i, j] = data['summary_level']['pearson']['r']
            system_pearson[i, j] = data['system_level']['pearson']['r']
            global_pearson[i, j] = data['global']['pearson']['r']

            summary_spearman[i, j] = data['summary_level']['spearman']['rho']
            system_spearman[i, j] = data['system_level']['spearman']['rho']
            global_spearman[i, j] = data['global']['spearman']['rho']

            summary_kendall[i, j] = data['summary_level']['kendall']['tau']
            system_kendall[i, j] = data['system_level']['kendall']['tau']
            global_kendall[i, j] = data['global']['kendall']['tau']

    os.makedirs(args.output_dir, exist_ok=True)
    plot_heatmap(summary_pearson, args.names, f'{args.output_dir}/summary-pearson.pdf')
    plot_heatmap(summary_spearman, args.names, f'{args.output_dir}/summary-spearman.pdf')
    plot_heatmap(summary_kendall, args.names, f'{args.output_dir}/summary-kendall.pdf')
    plot_heatmap(system_pearson, args.names, f'{args.output_dir}/system-pearson.pdf')
    plot_heatmap(system_spearman, args.names, f'{args.output_dir}/system-spearman.pdf')
    plot_heatmap(system_kendall, args.names, f'{args.output_dir}/system-kendall.pdf')
    plot_heatmap(global_pearson, args.names, f'{args.output_dir}/global-pearson.pdf')
    plot_heatmap(global_spearman, args.names, f'{args.output_dir}/global-spearman.pdf')
    plot_heatmap(global_kendall, args.names, f'{args.output_dir}/global-kendall.pdf')


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_dir')
    argp.add_argument('output_dir')
    argp.add_argument('--metrics', nargs='+')
    argp.add_argument('--names', nargs='+')
    args = argp.parse_args()
    main(args)