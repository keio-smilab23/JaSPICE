import pytest
from jaspice.graph_parser import JaSceneGraphParser

text = "人通りの少なくなった道路で青いズボンを着た男の子がオレンジ色のヘルメットを被りスケートボードに乗っている"


def test_parse_graph():
    expected = sorted(['人通り', '道路', 'ズボン', '男の子', 'ヘルメット', 'ボード', '青い_ズボン', 'オレンジ色_ヘルメット', '人通り_少ない_道路', '男の子_着る_ズボン', '男の子_被る_ヘルメット', '男の子_乗る_ボード', '男の子_乗る_道路'])
    parser = JaSceneGraphParser()
    graph = parser.run(text)
    graph_tuple = graph.get_graph_tuple()
    graph_tuple_list = sorted(list(graph_tuple))
    assert graph_tuple_list == expected


# def test_draw_graph():
#     parser = JaSceneGraphParser()
#     graph = parser.run(text)
#     graph.draw()


def test_print_graph():
    parser = JaSceneGraphParser()
    graph = parser.run(text)
    graph.print()
