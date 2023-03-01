import heapq
from dataclasses import dataclass
from typing import Any, List, Optional
from jaspice.lang_parser import LangParser, ParsedLang

DEBUG = False
ZEROP = "[PHI]"


@dataclass
class SceneNode:
    """
    SceneNode represents a node in a SceneGraph.
    """
    text: str
    word: str
    pos: str
    kind: str  # "object", "attribute", "relation"
    id: int


@dataclass
class BunsetuToken:
    """
    BunsetuToken represents a bunsetu.
    """
    text: str
    tokens: Any
    head: int
    dep: str
    pos: str
    i: int


class SceneGraph:
    """
    Scene Graph is a directed acyclic graph that represents relationships between objects, attributes, and actions in a scene.
    """

    def __init__(self, zero_pronoun=True):
        """
        Initializes a SceneGraph instance.

        Args:
        zero_pronoun (bool): whether to consider zero pronouns in the graph or not. Default is True.
        """
        self.edges = {}  # edges[src] = dst
        self.inv_edges = {}
        self.nodes = []
        self.raw_nodes = []
        self.node_map = {}
        self.edge_set = set()
        self.has_build = False
        self.consider_zerop = zero_pronoun

    def add_node(self, text: str, lemma: str, pos: str, unique=False) -> int:
        """
        Adds a node to the graph.

        Args:
        text (str): text of the node.
        lemma (str): lemma of the node.
        pos (str): part-of-speech tag of the node.
        unique (bool): whether to add the node even if it is a duplicate of another node. Default is False.

        Returns:
        int: the index of the node in the graph.
        """
        if not unique and text in self.raw_nodes:
            return self.raw_nodes.index(text)

        idx = len(self.nodes)
        self.nodes.append(SceneNode(text, lemma, pos, "", idx))
        self.raw_nodes.append(text)

        self.node_map.setdefault(text, [])
        self.node_map[text].append(idx)
        return idx

    def add_edge(self, src_id: int, dst_id: int):
        """
        Adds an edge between two nodes in the graph.

        Args:
        src_id (int): the index of the source node.
        dst_id (int): the index of the destination node.
        """
        assert src_id is not None and src_id >= 0
        assert dst_id is not None and dst_id >= 0
        if (src_id, dst_id) in self.edge_set:
            return

        self.edges.setdefault(src_id, [])
        self.inv_edges.setdefault(dst_id, [])
        self.edges[src_id].append(dst_id)
        self.inv_edges[dst_id].append(src_id)
        self.edge_set.add((src_id, dst_id))

    def build(self):
        """
        Build the scene graph by assigning node kind, complementing nsubj, and complementing zero pronoun.
        """
        if self.has_build:
            return
        self._assign_node_kind()
        self._complement_nsubj()
        if self.consider_zerop:
            self._complement_zerop()

        self.has_build = True

    def _complement_zerop(self):
        """
        Complement the SceneGraph with zero pronouns.
        """
        for node_id in range(len(self.nodes)):
            self.edges.setdefault(node_id, [])
            self.inv_edges.setdefault(node_id, [])
            if self.nodes[node_id].kind != "relation":
                continue
            if len(self.inv_edges[node_id]) == 0:
                L = len(self.nodes)
                self.inv_edges[node_id].append(L)
                self.nodes.append(SceneNode(ZEROP, ZEROP, ZEROP, "object", L))
                self.edges[L] = [node_id]

    def _assign_node_kind(self):
        """
        Assign the kind of each node in the graph.
        """
        for node_id in range(len(self.nodes)):
            self.edges.setdefault(node_id, [])
            self.inv_edges.setdefault(node_id, [])
            o_deg = len(self.edges[node_id])
            if self.nodes[node_id].pos == "NP":
                self.nodes[node_id].kind = "object"
            else:
                self.nodes[node_id].kind = "attribute" if o_deg == 0 else "relation"

    def _complement_nsubj(self):
        """
        Complement the SceneGraph with subject information.
        (find this; node (relation) -> obj_node <- rel_node <- nsubj)
        """

        for node_id in range(len(self.nodes)):
            node = self.nodes[node_id]
            i_deg = len(self.inv_edges[node_id])
            if node.kind == "relation" and i_deg == 0:
                for obj_node_id in self.edges[node_id]:
                    if self.nodes[obj_node_id].pos != "NP" or node_id not in self.inv_edges:
                        continue
                    for rel_node_id in self.inv_edges[obj_node_id]:
                        if self.nodes[rel_node_id].kind != "relation" or self.nodes[rel_node_id].text == "の":
                            continue
                        nsubj = self.get_nsubj_node(self.nodes[rel_node_id].text)
                        if nsubj != -1:
                            self.add_edge(nsubj, node.id)
                            break

    def search_nodes(self, text: str) -> List[int]:
        """
        Search for nodes in the graph by text.

        Args:
        text (str): The text to search for in the graph.

        Returns:
        List[int]: A list of node IDs that match the text.
        """
        if text not in self.node_map:
            return []

        return self.node_map[text]

    def get_nsubj_node(self, text: str, allow_direct: bool = True) -> int:
        """
        Get the subject node for the given text.

        Args:
        text (str): The text to search for the subject node.
        allow_direct (bool): A flag to allow direct match or not. Defaults to True.

        Returns:
        int: The ID of the subject node or -1 if not found.
        """
        nodes = self.search_nodes(text)
        if len(nodes) == 0:
            return -1

        node_id = nodes[0]
        if node_id not in self.inv_edges:
            return -1

        INF = 1 << 20
        stack = [(0, node_id, False)]
        dists = [INF if i != node_id else 0 for i in range(len(self.nodes))]
        cand = (INF, -1)
        heapq.heapify(stack)
        while len(stack) > 0:
            dist, current, is_noun = heapq.heappop(stack)
            if is_noun and cand[0] > dist:
                if not allow_direct and dist <= 1:
                    pass
                else:
                    cand = (dist, current)

            if current not in self.inv_edges:
                continue
            for i in self.inv_edges[current]:
                if dists[i] > dist + 1:
                    heapq.heappush(stack, (dist + 1, i, self.nodes[i].pos == "NP"))
                    dists[i] = dist + 1

        return cand[-1]

    def get_connected_noun_nodes(self, target_id: int, direction: str = "in") -> int:
        """
        Get the connected noun node for the given node.

        Artgs:
        target_id (int): The ID of the target node.
        direction (str): The direction of the edge. Defaults to "in".

        Returns:
        int: node ID that are connected to the target node.
        """
        assert direction == "in" or direction == "out", "invalid direction"
        ref_table = self.edges if direction == "out" else self.inv_edges
        for node_id in ref_table[target_id]:
            node = self.nodes[node_id]
            if node.pos == "NP":
                return node_id
        return -1

    def inherit_inedge(self, src: int, dst: int) -> bool:
        """
        Inherit the inedge nodes for the given nodes.

        Args:
        src (int): The ID of the source node.
        dst (int): The ID of the destination node.

        Returns:
        bool: True if the inheritance is successful, False otherwise.
        """
        if src == -1 or dst == -1:
            return False

        nodes = [src, dst]
        inedge_nodes = [self.inv_edges[nodes[i]] for i in range(2)]
        for i in range(2):
            for inv_node_id in inedge_nodes[i]:
                self.add_edge(inv_node_id, nodes[i ^ 1])

        return True

    def get_objects(self) -> List[str]:
        """
        Get the object nodes in the graph.

        Returns:
        List[str]: A list of object nodes.
        """
        return [node.word for node in self.nodes if node.kind == "object"]

    def get_attribute(self) -> List[str]:
        """
        Get the attribute in the graph.

        Returns:
        List[str]: A list of nodes.
        """
        res = []
        for node_id in range(len(self.nodes)):
            self.edges.setdefault(node_id, [])
            if self.nodes[node_id].kind != "attribute":
                continue

            for dst_id in self.inv_edges[node_id]:
                node1 = self.nodes[node_id]
                node2 = self.nodes[dst_id]
                atrr = f"{node1.word}_{node2.word}"
                res.append(atrr)
        return res

    def get_relation(self) -> List[str]:
        """
        Get the relation in the graph.

        Returns:
        List[str]: A list of nodes.
        """
        res = []
        for node_id in range(len(self.nodes)):
            self.edges.setdefault(node_id, [])
            self.inv_edges.setdefault(node_id, [])
            if self.nodes[node_id].kind != "relation":
                continue

            for dst_id in self.edges[node_id]:
                for src_id in self.inv_edges[node_id]:
                    node1 = self.nodes[src_id]
                    node2 = self.nodes[node_id]
                    node3 = self.nodes[dst_id]
                    # rel = (node1.word, node2.word, node3.word)
                    rel = f"{node1.word}_{node2.word}_{node3.word}"
                    res.append(rel)
        return res

    def get_graph_tuple(self) -> List[str]:
        """
        Get the graph tuple.

        Returns:
        List[str]: a graph tuple.
        """
        self.build()
        res = []
        objs = self.get_objects()
        attrs = self.get_attribute()
        rels = self.get_relation()
        for t in [objs, attrs, rels]:
            res.extend(t)
        return res

    def print(self, word: bool = True):
        """
        Print the graph.

        Args:
        word (bool): A flag to print the word or text. Defaults to True.
        """
        self.build()
        for src_id in range(len(self.nodes)):
            for dst_id in self.edges[src_id]:
                src, dst = self.nodes[src_id], self.nodes[dst_id]
                if word:
                    print(f"{src.word}({src.kind}) ----> {dst.word}({dst.kind})")
                else:
                    print(f"{src.text}({src.kind}) ----> {dst.text}({dst.kind})")

    def draw(self):
        """
        Draw the graph.
        """
        # networkx
        import numpy as np
        import matplotlib.pyplot as plt
        try:
            import networkx as nx
        except ImportError as e:
            raise ImportError('Install networkx') from e

        def nudge(pos, x_shift, y_shift):
            return {n: (x + x_shift, y + y_shift) for n, (x, y) in pos.items()}

        dg = nx.DiGraph()
        obj, rel, attr = [], [], []
        for src_id in range(len(self.nodes)):
            src = self.nodes[src_id]
            if src.kind == "relation":
                rel.append(src_id)
            elif src.kind == "attribute":
                attr.append(src_id)
            else:
                obj.append(src_id)

        dg.add_nodes_from([idx for idx in range(len(self.nodes))])
        for src_id in range(len(self.nodes)):
            src = self.nodes[src_id]
            for dst_id in self.edges[src_id]:
                dg.add_edge(src_id, dst_id)

        labels = {idx: self.nodes[idx].word for idx in range(len(self.nodes))}
        pos = nx.circular_layout(dg)
        pos_nodes = nudge(pos, 0, 0.15)
        options = {"edgecolors": "tab:gray", "alpha": 0.9}
        node_colors = [(obj, "#ffaeb9"), (rel, "#bfefff"), (attr, "#a8dda8")]
        for node, color in node_colors:
            nx.draw_networkx_nodes(dg, pos, node, node_color=color, **options)
        nx.draw_networkx_edges(dg, pos, width=1.0, alpha=0.5)
        nx.draw_networkx_labels(dg, pos_nodes, labels, font_size=16, font_family='IPAexGothic')  # need: sudo apt install fonts-ipaexfont
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['bottom'].set_visible(False)
        plt.gca().spines['left'].set_visible(False)
        plt.savefig("graph.png")

        # graphviz
        try:
            from graphviz import Digraph
        except ImportError as e:
            raise ImportError('Install graphviz') from e

        dg = Digraph(format='png')
        dg.attr('node', shape='circle', fontname='IPA ゴシック')
        for src_id in range(len(self.nodes)):
            src = self.nodes[src_id]
            color = "#ffaeb9"
            if src.kind == "relation":
                color = "#bfefff"
            elif src.kind == "attribute":
                color = "#a8dda8"
            dg.node(str(src_id), src.word.replace(ZEROP, "φ"), style='filled', fillcolor=color, fontcolor='black')
            for dst_id in self.edges[src_id]:
                if src.kind != self.nodes[dst_id].kind:
                    dg.edge(str(src_id), str(dst_id))
        dg.view()


class JaSceneGraphParser:
    """
    Scene graph parser for Japanese language.
    """

    def __init__(self, lparser: Optional[LangParser] = None, verbose: bool = False) -> None:
        """
        Initializes a new instance of JaSceneGraphParser.

        Args:
            lparser (Optional[LangParser], optional): The language parser instance. Defaults to None.
            verbose (bool, optional): Whether to enable verbose output. Defaults to False.
        """
        self.ja_parser = lparser or LangParser(verbose=verbose)
        self.verbose = verbose
        # self.loc_table = ["上", "下", "前", "後ろ", "右", "左", "中", "外", "隣", "近く", "間", "上部", "下部"]
        self.loc_table = ["上", "下", "前", "後ろ", "右", "左", "中", "外", "隣", "近く", "間", "上部", "下部", "右下", "右上", "左下", "左上"]
        self.attr_categories = ["動物-部位", "植物-部位", "場所-施設部位", "形・模様", "色", "数量", "時間"]

    def _parse(self, graph: SceneGraph, lparsed: ParsedLang):
        """
        Parse the scene graph.

        Args:
            graph (SceneGraph): graph to be parsed
            lparsed (ParsedLang): parsed language information.
        """
        self._parse_predicate_argument_structure(graph, lparsed)
        self._parse_dependencies(graph, lparsed)

    def _parse_predicate_argument_structure(self, graph: SceneGraph, lparsed: ParsedLang):
        """
        Parse predicate-argument structure.
        Args:
            graph (SceneGraph): graph to be parsed
            lparsed (ParsedLang): parsed language information.
        """
        des, timeframe = [], []
        # 述語項構造情報
        for (tag, cargs) in lparsed.case_args:
            if "ヨリ" in [c.case for c in cargs]:
                tag.text = f"ヨリ{tag.text}"

            for carg in cargs:
                src, dst, mid = -1, -1, None
                if carg.case[0] == "ガ":  # ガ or ガ２ or ...
                    src = graph.add_node(carg.arg, carg.arg, "NP")
                    dst = graph.add_node(tag.text, tag.text, "OTHER")
                elif carg.case == "ヲ":
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "ニ":
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "カラ":
                    # mid = graph.add_node("カラ", "カラ", "OTHER", unique=True)
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "ヨリ":
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "ト":
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "ヘ":
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "時間":
                    timeframe.append((tag.text, carg.arg))
                elif carg.case == "外の関係":
                    src = graph.add_node(tag.text, tag.text, "OTHER")
                    dst = graph.add_node(carg.arg, carg.arg, "NP")
                elif carg.case == "デ":
                    des.append((tag.text, carg.arg))
                else:
                    continue

                if src != -1 and dst != -1:
                    if not mid:
                        graph.add_edge(src, dst)
                        continue

                    graph.add_edge(src, mid)
                    graph.add_edge(mid, dst)

        # 時間
        for tag, arg in timeframe:
            src = graph.get_nsubj_node(tag)
            dst = graph.add_node(arg, arg, "ATTR")
            if src != -1 and dst != -1:
                graph.add_edge(src, dst)

        # デ格
        for tag, arg in des:
            src = graph.add_node(tag, tag, "NP")
            dst = graph.add_node(arg, arg, "OTHER")
            if src != -1 and dst != -1:
                graph.add_edge(src, dst)

    def _parse_dependencies(self, graph: SceneGraph, lparsed: ParsedLang):
        """
        Parse dependencies.
        Args:
            graph (SceneGraph): graph to be parsed
            lparsed (ParsedLang): parsed language information.
        """
        # 係り受けによるノードの接続
        for bnst in lparsed.bnsts:
            parent = bnst.parent
            if parent is None:
                continue

            if self.verbose:
                print(bnst.kind, parent.kind)
                print(bnst.raw_text, "->", parent.raw_text)
                print(f"{bnst.text}({bnst.raw_text}) -> {parent.text}({parent.raw_text})")

            if bnst.kind == parent.kind == "VP":
                nsubj: int = -1
                cand: List[int] = []
                S = [parent.text, bnst.text]
                for f in range(2):
                    if nsubj != -1 and len(cand) > 0:
                        continue
                    nsubj = graph.get_nsubj_node(S[f])
                    cand = graph.search_nodes(S[f ^ 1])

                if len(cand) > 0 and nsubj != -1:
                    dst = cand[0]
                    graph.add_edge(nsubj, dst)
            elif bnst.kind == parent.kind == "NP":
                if bnst.raw_text[-1] == "の":
                    if parent.text in self.loc_table:
                        src = graph.add_node(bnst.text, bnst.text, "NP")
                        dst = graph.add_node(parent.text, parent.text, "OTHER")

                        if src != -1 and dst != -1:
                            graph.add_edge(src, dst)
                    elif bnst.text in self.loc_table:
                        src = graph.add_node(bnst.text, bnst.text, "OTHER")
                        dst = graph.add_node(parent.text, parent.text, "NP")

                        if src != -1 and dst != -1:
                            graph.add_edge(src, dst)
                    else:
                        is_attr = bnst.have_subcategory_mrph(self.attr_categories)
                        if not is_attr:
                            src = graph.add_node(bnst.text, bnst.text, "NP")
                            dst = graph.add_node(parent.text, parent.text, "NP")
                            mid = graph.add_node("の", "の", "OTHER", unique=True)
                            if src != -1 and mid != -1 and dst != -1:
                                graph.add_edge(src, mid)
                                graph.add_edge(mid, dst)
                        else:
                            dst = graph.add_node(bnst.text, bnst.text, "ATTR")
                            src = graph.add_node(parent.text, parent.text, "NP")
                            if src != -1 and dst != -1:
                                graph.add_edge(src, dst)

                elif bnst.raw_text[-1] == "と":
                    node1 = graph.add_node(bnst.text, bnst.text, "NP")
                    node2 = graph.add_node(parent.text, parent.text, "NP")
                    graph.inherit_inedge(node1, node2)

    def run(self, text: str) -> SceneGraph:
        """
        Run parser.

        Args:
            text (str): text to be parsed.

        Returns:
            SceneGraph: parsed scene graph.
        """
        graph = SceneGraph()
        try:
            lparsed = self.ja_parser(text)
            self._parse(graph, lparsed)
            return graph
        except BaseException:
            return graph


if __name__ == "__main__":
    text = "人通りの少なくなった道路で青いズボンを着た男の子がオレンジ色のヘルメットを被りスケートボードに乗っている"
    parser = JaSceneGraphParser(verbose=True)
    graph = parser.run(text)
    graph.print()
    graph.draw()
    print("tuple:", graph.get_graph_tuple())
