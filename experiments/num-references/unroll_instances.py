import argparse
from sacrerouge.io import JsonlReader, JsonlWriter
from tqdm import tqdm


def main(args):
    with JsonlWriter(args.output_jsonl) as out:
        with JsonlReader(args.input_jsonl) as f:
            for instance in tqdm(f):
                references = instance['references']
                summarizer_id = instance['summarizer_id']
                summarizer_type = instance['summarizer_type']
                if args.remove_references and summarizer_type == 'reference':
                    continue

                for reference in references:
                    # Create a copy of the instance
                    copy = dict(instance)
                    # Put the information about the reference in the ID
                    reference_id = reference['summarizer_id']
                    copy['summarizer_id'] = f'{summarizer_id}_{reference_id}'
                    copy['references'] = [reference]
                    out.write(copy)



if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('output_jsonl')
    argp.add_argument('--remove-references', action='store_true')
    args = argp.parse_args()
    main(args)