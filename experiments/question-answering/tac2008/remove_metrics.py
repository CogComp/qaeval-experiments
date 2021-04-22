# Removes all metrics from a metrics.jsonl file except for pyramid and responsiveness.
import argparse
from sacrerouge.io import JsonlReader, JsonlWriter

METRICS_TO_KEEP = {
    'modified_pyramid_score',
    'modified_pyramid_score_jk',
    'overall_responsiveness',
    'content_responsiveness',
    'responsiveness'
}

PYRAMID_METRICS = {
    'modified_pyramid_score',
    'modified_pyramid_score_jk'
}


def main(args):
    with JsonlWriter(args.output_jsonl) as out:
        with JsonlReader(args.input_jsonl) as f:
            for instance in f:
                metrics = instance['metrics']
                names = list(metrics.keys())
                for name in names:
                    if name not in METRICS_TO_KEEP or (args.remove_pyramid and name in PYRAMID_METRICS):
                        del metrics[name]
                out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('output_jsonl')
    argp.add_argument('--remove-pyramid', action='store_true')
    args = argp.parse_args()
    main(args)