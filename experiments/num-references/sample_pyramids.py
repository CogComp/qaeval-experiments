import argparse
import random
from sacrerouge.data import Pyramid
from sacrerouge.io import JsonlReader, JsonlWriter


def main(args):
    random.seed(args.random_seed)

    with JsonlWriter(args.output_file) as out:
        for pyramid in JsonlReader(args.pyramid_jsonl, Pyramid).read():
            indices = [i for i in range(len(pyramid.summarizer_ids))]
            random.shuffle(indices)
            indices_to_remove = indices[args.num_references:]

            # Remove all of references in reverse order so the index remains consistent
            reduced_pyramid = pyramid
            for index in sorted(indices_to_remove, reverse=True):
                reduced_pyramid = reduced_pyramid.remove_summary(index)

            out.write(reduced_pyramid)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('pyramid_jsonl')
    argp.add_argument('num_references', type=int)
    argp.add_argument('random_seed', type=int)
    argp.add_argument('output_file')
    args = argp.parse_args()
    main(args)