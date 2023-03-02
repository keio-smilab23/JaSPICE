import pytest
from typing import List, Dict
from jaspice.api import JaSPICE


def test_compute_score():
    ref: Dict[str, List[str]] = {}
    cap: Dict[str, List[str]] = {}
    ref["0"] = ['川の中で黒い熊が取っ組み合いをしている', '湖の中で取っ組み合っている黒い熊である', '湖の中で喧嘩をする二頭の熊と湖の端っこで水に浸かっている熊', '川でじゃれ合う2匹の熊と川に浸かる熊', '熊が二匹水の中で取っ組み合いをしている']
    cap["0"] = ["川の中で熊が喧嘩している"]
    ref["1"] = ['店の厨房の中をTシャツを着た女性が動いている', '女性がフライヤーで何かを揚げている', 'グレーのTシャツの女性が電気に照らされているボールのほうを向いている', '揚げ物をしている女性が揚げ具合を見ている', '厨房で揚げ物があがるのを確認してる店員']
    cap["1"] = ["キッチンの服を男性がキッチンを火れているを中を見ている"]
    ref["2"] = ['黒いウェアの人がスノーボードで大きくジャンプしている', '雪の上をスノーボードでジャンプしてる人', 'スノーボーダーが大きくジャンプをした瞬間', '雪山に太陽がさんさんと輝き、スノーボーダーが空を飛んでいる', 'スノーボードでジャンプしている']
    cap["2"] = ['スノーボードでジャンプする少年']

    jaspice = JaSPICE(server_mode=False)
    score, scores = jaspice.compute_score(ref, cap)
    assert len(scores) == 3
    assert score == pytest.approx(0.108, 1e-2)
    assert scores[0] == pytest.approx(0.182, 1e-3)
    assert scores[1] == pytest.approx(0.0556, 1e-3)
    assert scores[2] == pytest.approx(0.0870, 1e-3)
