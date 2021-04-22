import argparse
from sacrerouge.io import JsonlReader, JsonlWriter


def main(args):
    seen = set()
    num_duplicates = 0
    num_non_duplicates = 0
    with JsonlWriter(args.output_file) as out:
        for file_path in args.input_files:
            for prompt in JsonlReader(file_path).read():
                if prompt['prompt_id'] in seen:
                    num_duplicates += 1
                    continue
                num_non_duplicates += 1
                seen.add(prompt['prompt_id'])
                out.write(prompt)

    print(f'Deduplicated {num_duplicates} prompts')
    print(f'Wrote {num_non_duplicates} prompts')


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('--input-files', nargs='+')
    argp.add_argument('--output-file')
    args = argp.parse_args()
    main(args)