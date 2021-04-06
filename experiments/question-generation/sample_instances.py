import argparse
import random
from collections import defaultdict
from sacrerouge.io import JsonlReader, JsonlWriter
from tqdm import tqdm


def main(args):
    random.seed(4)

    instances = JsonlReader(args.input_jsonl).read()
    instance_id_to_instances = defaultdict(list)
    for instance in instances:
        instance_id_to_instances[instance['instance_id']].append(instance)
    instance_ids = list(sorted(instance_id_to_instances.keys()))

    # Each point on the learning curve. Also make sure that the number of inputs isn't larger
    # than the number of instances and the max number of inputs is included.
    num_inputs_list = args.num_inputs
    while num_inputs_list[-1] >= len(instance_ids):
        num_inputs_list.pop()
    num_inputs_list.append(len(instance_ids))

    for num_inputs in tqdm(num_inputs_list):
        for sample_index in range(args.num_samples):
            with JsonlWriter(f'{args.output_dir}/{num_inputs}/{sample_index}.jsonl') as out:
                random.shuffle(instance_ids)
                sample = list(sorted(instance_ids[:num_inputs]))
                for instance_id in sample:
                    for instance in instance_id_to_instances[instance_id]:
                        out.write(instance)


if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('input_jsonl')
    argp.add_argument('num_samples', type=int)
    argp.add_argument('output_dir')
    argp.add_argument('--num-inputs', type=int, nargs='+')
    args = argp.parse_args()
    main(args)