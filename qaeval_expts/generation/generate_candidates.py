import allennlp_models.coref
import argparse
import hashlib
import spacy
from allennlp.predictors import Predictor
from sacrerouge.io import JsonlReader, JsonlWriter
from spacy.tokens import Span
from tqdm import tqdm
from typing import Any, Dict, List, Tuple


PRONOUNS = {
    'i', 'we',
    'he', 'she',
    'him', 'her',
    'his', 'hers',
    'it', 'its',
    'they', 'them',
    'their', 'theirs'
}


class EmptySummaryException(Exception):
    pass


def get_prompts_all(sentence: Span) -> List[Span]:
    all_prompts = []
    all_prompts.extend(get_prompts_all_nps(sentence))
    all_prompts.extend(get_prompts_top_nps(sentence))
    all_prompts.extend(get_prompts_ner(sentence))

    offsets_to_prompt = {}
    for prompt in all_prompts:
        offsets_to_prompt[(prompt.start_char, prompt.end_char)] = prompt
    return list(offsets_to_prompt.values())


def get_prompts_all_nps(sentence: Span) -> List[Span]:
    return list(sentence.noun_chunks)


def get_prompts_top_nps(sentence: Span) -> List[Span]:
    root = sentence.root
    nodes = [root]
    nps = []

    while len(nodes) > 0:
        node = nodes.pop()

        # If the node is a noun, collect all of the tokens
        # which are descendants of this node
        recurse = True
        if node.pos_ in ['NOUN', 'PROPN']:
            min_index = node.i
            max_index = node.i
            stack = [node]
            while len(stack) > 0:
                current = stack.pop()
                min_index = min(min_index, current.i)
                max_index = max(max_index, current.i)
                for child in current.children:
                    stack.append(child)

            sent_start_index = sentence[0].i

            # Because of parsing issues, we only take NPs if they are shorter than a given length
            num_tokens = max_index - min_index + 1
            if num_tokens <= 7:
                recurse = False
                nps.append(sentence[min_index - sent_start_index:max_index + 1 - sent_start_index])

        if recurse:
            # Otherwise, process all of this node's children
            for child in node.children:
                nodes.append(child)

    # Sort in order of appearance
    nps.sort(key=lambda np: np[0].i)
    return nps


def get_prompts_ner(sentence: Span) -> List[Span]:
    nps = []
    for entity in sentence.ents:
        if entity.label_ in ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'EVENT', 'WORK_OF_ART']:
            nps.append(entity)
    return nps


def get_prompts(method: str, sentence: Span) -> List[Span]:
    if method == 'all-nps':
        return get_prompts_all_nps(sentence)
    elif method == 'top-nps':
        return get_prompts_top_nps(sentence)
    elif method == 'ner':
        return get_prompts_ner(sentence)
    elif method == 'all':
        return get_prompts_all(sentence)
    else:
        raise Exception(f'Unknown method: {method}')


def find_cluster(clusters: List[List[Tuple[int, int]]],
                 tokens: List[str],
                 start: int,
                 end: int) -> List[str]:
    """
    Find the coreference cluster that corresponds to the phrase that corresponds
    to the token span (start, end]. It will return the first cluster that contains
    a phrase that subsumes the tokens.
    """
    for cluster in clusters:
        is_in_cluster = False
        for i, j in cluster:
            # [i, j] is inclusive, [start, end) is exclusive
            if i <= start <= j and i <= (end - 1) <= j:
                # This cluster span subsumes the NP, so we say
                # it belongs to this cluster
                is_in_cluster = True

        if is_in_cluster:
            cluster_phrases = set()
            for i, j in cluster:
                phrase = ' '.join(tokens[i:j + 1])
                if phrase.lower() not in PRONOUNS:
                    cluster_phrases.add(phrase)
            return list(sorted(cluster_phrases))
    return []


def get_candidate_id(text: str, start: int, end: int) -> str:
    m = hashlib.md5()
    m.update(text.encode())
    m.update(str(start).encode())
    m.update(str(end).encode())
    return m.hexdigest()


def get_group_id(text: str, start: int, end: int) -> str:
    return get_candidate_id(text, start, end)


def process_instance(nlp, coref_predictor, instance: Dict[str, Any], method: str):
    original_summary = instance['summary']['text']
    if isinstance(original_summary, list):
        original_summary = ' '.join(original_summary)
    if len(original_summary.strip()) == 0:
        raise EmptySummaryException()

    coref_result = coref_predictor.predict(document=original_summary)
    tokens = coref_result['document']
    clusters = coref_result['clusters']

    text = ' '.join(tokens)
    doc = nlp(tokens)
    assert len(doc) == len(tokens)

    # Replace the summary's text with the preprocessed version
    instance['summary']['text'] = text

    candidates = []
    for sent in doc.sents:
        group_id = get_group_id(text, sent.start_char, sent.end_char)
        for np in get_prompts(method, sent):
            np_cluster = find_cluster(clusters, tokens, np.start, np.end)
            candidate_id = get_candidate_id(text, np.start_char, np.end_char)
            candidates.append({
                'candidate_id': candidate_id,
                'group_id': group_id,
                'candidate': str(np),
                'candidate_start': np.start_char,
                'candidate_end': np.end_char,
                'sent_start': sent.start_char,
                'sent_end': sent.end_char,
                'coreference_cluster': np_cluster
            })
    instance['summary']['candidates'] = candidates


def main(args):
    nlp = spacy.load('en_core_web_sm')
    nlp.tokenizer = nlp.tokenizer.tokens_from_list

    coref_predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2020.02.27.tar.gz", cuda_device=0)

    with JsonlWriter(args.output_jsonl) as out:
        for instance in tqdm(JsonlReader(args.summaries_jsonl).read()):
            try:
                process_instance(nlp, coref_predictor, instance, args.method)
                out.write(instance)
            except EmptySummaryException:
                pass



if __name__ == '__main__':
    argp = argparse.ArgumentParser()
    argp.add_argument('summaries_jsonl')
    argp.add_argument('output_jsonl')
    argp.add_argument('--method', choices=['all-nps', 'top-nps', 'ner', 'all'])
    args = argp.parse_args()
    main(args)