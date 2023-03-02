import pytest
from jaspice.metrics import JaSPICE, BatchJaSPICE


def test_jaspice():
    cap = "赤い傘をさした人がベンチに座っている"
    ref = [
        "赤い傘をさして座って海を見ている",
        "海岸のベンチに赤い傘を差した人が座っている",
        "海の公園のベンチに赤い折りたたみ傘を差した人が座っている",
        "ベンチに座って赤い傘をさした人が海を見ている",
        "海の見えるベンチで赤い傘を差した人が一人座っている"
    ]
    jaspice = JaSPICE()
    res = jaspice(ref, cap)
    assert res == pytest.approx(0.545, 1e-3)

    jaspice = JaSPICE(verbose=True)
    res = jaspice(ref, cap)
    assert res == pytest.approx(0.545, 1e-3)


def test_compute_F():
    jaspice = JaSPICE()
    P, R = 0.5, 0.5
    assert jaspice._compute_F(P, R) == 0.5

    P, R = 1.0, 0.0
    assert jaspice._compute_F(P, R) == 0.0

    P, R = 0.0, 1.0
    assert jaspice._compute_F(P, R) == 0.0


def test_batch_jaspice():
    refs, caps = [], []
    refs.append(['川の中で黒い熊が取っ組み合いをしている', '湖の中で取っ組み合っている黒い熊である', '湖の中で喧嘩をする二頭の熊と湖の端っこで水に浸かっている熊', '川でじゃれ合う2匹の熊と川に浸かる熊', '熊が二匹水の中で取っ組み合いをしている'])
    caps.append("川の中で熊が喧嘩している")
    refs.append(['店の厨房の中をTシャツを着た女性が動いている', '女性がフライヤーで何かを揚げている', 'グレーのTシャツの女性が電気に照らされているボールのほうを向いている', '揚げ物をしている女性が揚げ具合を見ている', '厨房で揚げ物があがるのを確認してる店員'])
    caps.append("キッチンの服を男性がキッチンを火れているを中を見ている")
    refs.append(['黒いウェアの人がスノーボードで大きくジャンプしている', '雪の上をスノーボードでジャンプしてる人', 'スノーボーダーが大きくジャンプをした瞬間', '雪山に太陽がさんさんと輝き、スノーボーダーが空を飛んでいる', 'スノーボードでジャンプしている'])
    caps.append('スノーボードでジャンプする少年')

    jaspice = BatchJaSPICE()
    res = jaspice(refs, caps)
    assert len(res) == 3
    assert res[0] == pytest.approx(0.182, 1e-3)
    assert res[1] == pytest.approx(0.0556, 1e-3)
    assert res[2] == pytest.approx(0.0870, 1e-3)

    jaspice = BatchJaSPICE(num_cpus=16)
    res = jaspice(refs, caps)
    assert len(res) == 3
    assert res[0] == pytest.approx(0.182, 1e-3)
    assert res[1] == pytest.approx(0.0556, 1e-3)
    assert res[2] == pytest.approx(0.0870, 1e-3)
