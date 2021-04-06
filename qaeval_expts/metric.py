import itertools
from collections import defaultdict, namedtuple
from sacrerouge.data import EvalInstance, MetricsDict
from sacrerouge.data.dataset_readers import DatasetReader
from sacrerouge.data.jackknifers import Jackknifer
from sacrerouge.data.fields import Fields, Field, SummaryField
from sacrerouge.data.types import SummaryType
from sacrerouge.io import JsonlReader
from sacrerouge.metrics import Metric, PythonRouge
from typing import Any, Dict, List, Tuple

AnsweredQuestion = namedtuple('AnsweredQuestion',
                              ['prompt_id', 'question_id', 'prediction_id', 'question', 'answer',
                               'prediction', 'probability', 'null_probability', 'group_id', 'is_correct'])


class AnsweredQuestionsField(Field):
    def __init__(self, answered_questions_list: List[List[AnsweredQuestion]]):
        self.answered_questions_list = answered_questions_list

    def __hash__(self) -> int:
        hashes = []
        for answered_questions in self.answered_questions_list:
            for answered_question in answered_questions:
                # The prediction_id is unique
                hashes.append(hash(answered_question.prediction_id))
        return hash(tuple(hashes))

    def __eq__(self, other: 'Field') -> bool:
        if len(self.answered_questions_list) != len(other.answered_questions_list):
            return False
        for answered_questions, other_answered_questions in zip(self.answered_questions_list, other.answered_questions_list):
            if len(answered_questions) != len(other_answered_questions):
                return False
            for aq1, aq2 in zip(answered_questions, other_answered_questions):
                if aq1.prediction_id != aq2.prediction_id:
                    return False
        return True

    def to_input(self) -> Any:
        """Returns what should be passed as input to the evaluation metric."""
        return self.answered_questions_list


@DatasetReader.register('qa-scoring')
class QAScoringDatasetReader(DatasetReader):
    def read(self, input_jsonl: str) -> List[EvalInstance]:
        eval_instances = []
        with JsonlReader(input_jsonl) as f:
            for instance in f:
                instance_id = instance['instance_id']
                summarizer_id = instance['summarizer_id']
                summarizer_type = instance['summarizer_type']
                summary = SummaryField(instance['summary']['text'])

                answered_questions_list = []
                for reference in instance['references']:
                    this_question_list = []
                    for question_dict in reference['questions']:
                        prompt_id = question_dict['prompt_id']
                        question_id = question_dict['question_id']
                        group_id = question_dict['group_id'] if 'group_id' in question_dict else None
                        question = question_dict['question']
                        answer = question_dict['answer']
                        for prediction_dict in question_dict['predictions']:
                            prediction_id = prediction_dict['prediction_id']
                            prediction = prediction_dict['answer']
                            probability = prediction_dict['probability']
                            null_probability = prediction_dict['null_probability']

                            if 'is_correct' in prediction_dict:
                                is_correct = prediction_dict['is_correct']
                            else:
                                # Dummy
                                is_correct = False

                            this_question_list.append(AnsweredQuestion(prompt_id, question_id, prediction_id, question, answer, prediction, probability, null_probability, group_id, is_correct))

                    if len(this_question_list) > 0:
                        answered_questions_list.append(this_question_list)

                if len(answered_questions_list) > 0:
                    fields = Fields({
                        'summary': summary,
                        'answered_questions': AnsweredQuestionsField(answered_questions_list)
                    })
                    eval_instances.append(EvalInstance(instance_id, summarizer_id, summarizer_type, fields))
        return eval_instances


class AnsweredQuestionsJackknifer(Jackknifer):
    def get_jackknifing_fields_list(self, fields: Fields) -> List[Fields]:
        field = fields['answered_questions']
        if len(field.answered_questions_list) == 1:
            # No jackknifing can be done, return `None` to indicate it cannot be done
            return None

        jk_fields_list = []
        for i in range(len(field.answered_questions_list)):
            jk_fields = Fields(fields)
            jk_fields['answered_questions'] = AnsweredQuestionsField(
                field.answered_questions_list[:i] + field.answered_questions_list[i + 1:])
            jk_fields_list.append(jk_fields)
        return jk_fields_list


@Metric.register('qa-scoring')
class QAScoringMetric(Metric):
    def __init__(self) -> None:
        super().__init__(['summary'], ['answered_questions'], jackknifer=AnsweredQuestionsJackknifer())
        self.rouge = PythonRouge(ngram_orders=[1], remove_stopwords=True, use_porter_stemmer=True)

    def _calculate_exact_match(self,
                               answer: str,
                               prediction: str,
                               probability: float,
                               null_probability: float) -> Dict[str, float]:
        if prediction is None:
            em_null = 0.0
        else:
            em = int(prediction == answer)
            em_null = 0
            if probability > null_probability:
                em_null = em

        return {
            'exact-match': em_null,
        }

    def _calculate_f1(self,
                      answer: str,
                      prediction: str,
                      probability: float,
                      null_probability: float) -> Dict[str, float]:
        if prediction is None:
            f1_null = 0.0
        else:
            f1 = self.rouge.score(prediction, [answer])['python-rouge-1']['f1']
            f1_null = 0
            if probability > null_probability:
                f1_null = f1

        return {
            'f1': f1_null,
        }

    def _calculate_is_answerable(self, probability: float, null_probability: float) -> Dict[str, float]:
        return {'is-answerable': int(probability > null_probability)}

    def _calculate_human_is_correct(self, is_correct: bool):
        return {'human-is-correct': int(is_correct)}

    def _score_question(self, answered_questions: List[AnsweredQuestion]) -> MetricsDict:
        # Average over answers
        metrics = []
        for aq in answered_questions:
            em = self._calculate_exact_match(aq.answer, aq.prediction, aq.probability, aq.null_probability)
            f1 = self._calculate_f1(aq.answer, aq.prediction, aq.probability, aq.null_probability)
            is_answerable = self._calculate_is_answerable(aq.probability, aq.null_probability)
            human_is_correct = self._calculate_human_is_correct(aq.is_correct)
            metrics.append(MetricsDict(dict(**em, **f1, **is_answerable, **human_is_correct)))
        return sum(metrics) / len(metrics)

    def _score_prompt(self, answered_questions: List[AnsweredQuestion]) -> MetricsDict:
        # Average over questions
        metrics = []
        for _, aqs in itertools.groupby(answered_questions, key=lambda aq: aq.question_id):
            metrics.append(self._score_question(list(aqs)))
        return sum(metrics) / len(metrics)

    def _score_reference(self, answered_questions: List[AnsweredQuestion]) -> MetricsDict:
        # Sort over the prompts then questions in one shot to setup the groupbys
        answered_questions.sort(key=lambda aq: (aq.prompt_id, aq.question_id))

        # Average over prompts
        metrics = []
        group_to_metrics = defaultdict(list)
        for _, aqs in itertools.groupby(answered_questions, key=lambda aq: aq.prompt_id):
            aqs = list(aqs)
            prompt_metrics = self._score_prompt(aqs)
            metrics.append(prompt_metrics)

            # All questions of the same prompt should be in the same group, so we can just take
            # the first one
            if aqs[0].group_id is not None:
                group_to_metrics[aqs[0].group_id].append(prompt_metrics)

        metrics = sum(metrics) / len(metrics)
        return metrics

    def _score(self, answered_questions_list: List[List[AnsweredQuestion]]) -> MetricsDict:
        # Average over references
        metrics = []
        for answered_questions in answered_questions_list:
            metrics.append(self._score_reference(answered_questions))
        final_metrics = sum(metrics) / len(metrics)
        return MetricsDict({'qa-eval': final_metrics})

    def score_multi_all(self,
                        summaries_list: List[List[SummaryType]],
                        answered_questions_lists: List[List[List[AnsweredQuestion]]]) -> List[List[MetricsDict]]:
        metrics_list = []
        for summaries, answered_questions_list in zip(summaries_list, answered_questions_lists):
            metrics_list.append([])
            for _ in summaries:
                metrics_list[-1].append(self._score(answered_questions_list))
        return metrics_list
