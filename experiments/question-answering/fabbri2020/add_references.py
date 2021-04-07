import argparse

from sacrerouge.io import JsonlReader, JsonlWriter


def main(args):
    seen = set()
    with JsonlWriter(args.output_jsonl) as out:
        with JsonlReader(args.input_jsonl) as f:
            for instance in f:
                instance_id = instance['instance_id']
                if instance_id not in seen:
                    seen.add(instance_id)
                    for reference in instance['references']:
                        out.write({
                            'instance_id': instance_id,
                            'summarizer_id': reference['summarizer_id'],
                            'summarizer_type': reference['summarizer_type'],
                            'summary': {'text': reference['text']},
                            'references': []
                        })
                out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('output_jsonl')
    args = argp.parse_args()
    main(args)