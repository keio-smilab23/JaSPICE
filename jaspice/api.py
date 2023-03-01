import requests
import json
import numpy as np
from typing import List, Tuple, Dict
from tqdm import tqdm
from jaspice.metrics import BatchJaSPICE


class JaSPICE:
    def __init__(self, batch_size: int=16, server_mode: bool=True) -> None:
        """
        Args:
            batch_size (int, optional): batch_size. Defaults to 16.
            server_mode (bool, optional): server mode. Defaults to True.
        """
        self.batch_size = batch_size
        self.server_mode=server_mode

    def compute_score(self, references: Dict[str,List[str]], candidates: Dict[str,List[str]])-> Tuple[float,List[float]]:
        """
        compute JaSPICE score

        Args:
            references (Dict[str,List[str]]): references
            candidates (Dict[str,List[str]]): candidates
            server_mode (bool, optional): server mode. Defaults to True.

        Returns:
            Tuple[float,List[float]]: JaSPICE scores
        """
        if not self.server_mode:
            bspice = BatchJaSPICE(size=self.batch_size)

        spice, N = [], len(candidates.items())
        batch_cand, batch_refs = [], []
        for i, (k, v) in enumerate(tqdm(candidates.items())):
            candidate = v[0].replace(" ", "")
            refs = list(map(lambda x: x.replace(" ", ""), references[k]))
            batch_cand.append(candidate)
            batch_refs.append(refs)
            if (i + 1) % self.batch_size == 0 or i == N - 1:
                if self.server_mode:
                    results = self._compute_via_server(batch_refs, batch_cand)
                else:
                    results = bspice(batch_candidate=batch_cand,
                                      batch_references=batch_refs)
                spice.extend(results)
                batch_cand, batch_refs = [], []

        return float(np.mean(spice)), spice

    def _compute_via_server(self, references: List[List[str]], candidates: List[str])-> List[float]:
        """
        compute JaSPICE score on server mode

        Args:
            references (List[List[str]]): references
            candidates (List[str]): candidates

        Returns:
            List[float]: JaSPICE scores
        """
        data = {"references": references, "candidates": candidates}
        response = requests.post('http://localhost:2115', json=data)
        jaspice = json.loads(response.text)
        return jaspice


if __name__ == "__main__":
    ref: Dict[str,List[str]] = {}
    cap: Dict[str,List[str]] = {}
    ref["0"] = ['川の中で黒い熊が取っ組み合いをしている', '湖の中で取っ組み合っている黒い熊である', '湖の中で喧嘩をする二頭の熊と湖の端っこで水に浸かっている熊', '川でじゃれ合う2匹の熊と川に浸かる熊', '熊が二匹水の中で取っ組み合いをしている']
    cap["0"] = ["川の中で熊が喧嘩している"]
    ref["1"] = ['店の厨房の中をTシャツを着た女性が動いている', '女性がフライヤーで何かを揚げている', 'グレーのTシャツの女性が電気に照らされているボールのほうを向いている', '揚げ物をしている女性が揚げ具合を見ている', '厨房で揚げ物があがるのを確認してる店員']
    cap["1"] = ["キッチンの服を男性がキッチンを火れているを中を見ている"]
    ref["2"] = ['黒いウェアの人がスノーボードで大きくジャンプしている', '雪の上をスノーボードでジャンプしてる人', 'スノーボーダーが大きくジャンプをした瞬間', '雪山に太陽がさんさんと輝き、スノーボーダーが空を飛んでいる', 'スノーボードでジャンプしている']
    cap["2"] = ['スノーボードでジャンプする少年']
    js = JaSPICE(server_mode=True)
    jaspice, jaspices = js.compute_score(ref, cap)
    print("mean:",jaspice)
    print("list:",jaspices)
