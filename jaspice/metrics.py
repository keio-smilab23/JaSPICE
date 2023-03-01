import ray
import itertools
from typing import List, Tuple, Set, Optional
from jaspice.graph_parser import JaSceneGraphParser, SceneGraph, ZEROP
from jaspice.lang_parser import LangParser
from jaspice.wordnet import JaWordNet


class JaSPICE:
    def __init__(self, lparser: Optional[LangParser] = None, verbose: bool = False):
        """
        Args:
            lparser (Optional[LangParser], optional): LangParser. Defaults to None.
            verbose (bool, optional): verbose mode. Defaults to False.
        """
        self.parser = JaSceneGraphParser(lparser, verbose=verbose)
        self.verbose = verbose
        self.wordnet: Optional[JaWordNet] = None

    def __call__(self, references: List[str], candidate: str) -> float:
        """
        compute JaSPICE score
        Args:
            references (List[str]): references
            candidate (str): candidate

        Returns:
            float: JaSPICE
        """
        targets = references + [candidate]
        graphs = [self.parser.run(t) for t in targets]
        cand_graph, ref_graphs = graphs[-1], graphs[:-1]

        cand_tuple, ref_tuple = self._get_tuple_sets(cand_graph, ref_graphs)
        match = self._compute_matching(cand_tuple, ref_tuple)
        precision = match / len(cand_tuple) if len(cand_tuple) > 0 else 0.
        recall = match / len(ref_tuple) if len(ref_tuple) > 0 else 0.
        F = self._compute_F(precision, recall)
        if self.verbose:
            print("references:", references)
            print("candidate:", candidate)
            print("match:", match)
            print("P:", precision)
            print("R:", recall)
            print("JaSPICE:", F, "\n\n\n")
        return F

    def _get_tuple_sets(self, cand_graph: SceneGraph, ref_graphs: List[SceneGraph]) -> Tuple[Set[str], Set[str]]:
        """
        Convert scene graphs to tuple sets

        Args:
            cand_graph (SceneGraph): scene graph of candidate
            ref_graphs (List[SceneGraph]): scene graph of references

        Returns:
            Tuple[Set[str],Set[str]]: tuple sets
        """
        ref_tuple = []
        for graph in ref_graphs:
            tp = graph.get_graph_tuple()
            ref_tuple.extend(tp)

        cand_tuple = cand_graph.get_graph_tuple()
        cand_set = self._delete_zero_pronoun(set(cand_tuple))
        ref_set = self._delete_zero_pronoun(set(ref_tuple))
        if self.verbose:
            print(f"cand: {cand_set}\nref: {ref_set}")
        return cand_set, ref_set

    def _delete_zero_pronoun(self, tuple_set: Set[str]) -> Set[str]:
        """
        delete zero pronouns

        Args:
            tuple_set (Set[str]): tuple set

        Returns:
            Set[str]: tuple set without zero pronouns
        """
        if ZEROP in tuple_set:
            tuple_set.remove(ZEROP)
        return tuple_set

    def _compute_matching(self, query_tuple: Set[str], target_tuple: Set[str]) -> float:
        """
        binary matching

        Args:
            query_tuple (Set[str]): query tuple
            target_tuple (Set[str]): target tuple

        Returns:
            float: matching score
        """
        if len(query_tuple) > len(target_tuple):
            query_tuple, target_tuple = target_tuple, query_tuple

        cnt = 0
        for query in query_tuple:
            dec = query.split("_")
            tp = []
            for i in range(len(dec)):
                tp.append(self._get_synonyms(dec[i]) + [dec[i]])

            for x in itertools.product(*tp):
                cand = "_".join(list(x))
                if cand in target_tuple:
                    cnt += 1
                    break

        return float(cnt)

    def _get_synonyms(self, query: str) -> List[str]:
        """
        get synonyms

        Args:
            query (str): query string

        Returns:
            List[str]: synonyms of query
        """
        if self.wordnet is None:  # for parallel
            self.wordnet = JaWordNet()
        return self.wordnet.get_synonyms(query)

    def _compute_F(self, precision: float, recall: float) -> float:
        """
        compute F score

        Args:
            precision (float): precision
            recall (float): recall

        Returns:
            float: F score
        """
        P, R = precision, recall
        F = (2 * P * R) / (P + R) if P + R != 0 else 0.
        return F


class BatchJaSPICE():
    def __init__(self, size: int = 8, num_cpus: Optional[int] = None):
        """
        Args:
            size (int, optional): batch size. Defaults to 8.
            num_cpus (Optional[int], optional): cpu size. Defaults to None.
        """
        ray.init(num_cpus=num_cpus or size, ignore_reinit_error=True)
        lparsers = [LangParser(verbose=False) for _ in range(size)]
        self.jaspice = [JaSPICE(lparsers[i], verbose=False) for i in range(size)]
        self.jaspice_id = [ray.put(self.jaspice[i]) for i in range(size)]
        self.size = size

    def __call__(self, batch_references: List[List[str]], batch_candidate: List[str]) -> List[float]:
        """
        compute JaSPICE score

        Args:
            batch_references (List[List[str]]): references
            batch_candidate (List[str]): candidates

        Returns:
            List[float]: JaSPICE scores
        """
        assert len(batch_references) == len(batch_candidate)
        assert len(batch_references) <= self.size

        @ray.remote
        def run(jaspice, references, candidate):
            return jaspice(references, candidate)

        process = [run.remote(self.jaspice_id[i], batch_references[i], batch_candidate[i]) for i in range(len(batch_references))]
        batch_results = ray.get(process)
        # print(batch_results)
        return batch_results


if __name__ == "__main__":
    import numpy as np
    from tqdm import tqdm
    cap = "赤い傘をさした人がベンチに座っている"
    ref = [
        "赤い傘をさして座って海を見ている",
        "海岸のベンチに赤い傘を差した人が座っている",
        "海の公園のベンチに赤い折りたたみ傘を差した人が座っている",
        "ベンチに座って赤い傘をさした人が海を見ている",
        "海の見えるベンチで赤い傘を差した人が一人座っている"
    ]

    single = 1
    if single:
        lparser = LangParser(verbose=True)
        jaspice = JaSPICE(lparser, verbose=True)
        value = jaspice(ref, cap)
        print(f"JaSPICE: {value:.3}")
    else:
        size = 16
        bjaspice = BatchJaSPICE(size)
        values = []
        for i in tqdm(range(101260 // size)):
            b_ref = [ref for _ in range(size)]
            b_cap = [cap for _ in range(size)]
            values += bjaspice(b_ref, b_cap)
        value = float(np.mean(values))
        print(value)
