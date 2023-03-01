import sqlite3
import hashlib
import re
from dataclasses import dataclass
from typing import Any, List, Tuple
from pyknp import KNP
from jaspice.knp_wrapper import ServerKNP, PexpectKNP, ServerKNP2

subcategory_pattern = re.compile(r'.*カテゴリ:([^\s]+).*')
wiki_pattern = re.compile(r'.*Wikipediaエントリ:([^\s]+):.*')


class LinguisticUnit:
    def __init__(self) -> None:
        self.phrase_table = {"<用言:動>": "VP", "<用言:形>": "AD", "<体言>": "NP"}
        self.subcategories = ["人", "組織・団体", "動物", "植物", "動物-部位", "植物-部位", "人工物-食べ物", "人工物-衣類", "人工物-乗り物", "人工物-金銭", "人工物-その他", "自然物", "場所-施設", "場所-施設部位", "場所-自然", "場所-機能", "場所-その他", "抽象物", "形・模様", "色", "数量", "時間"]

    def is_suffix(self, text):
        return "接尾辞" in text


class Bnst(LinguisticUnit):
    def __init__(self, knp_bnst) -> None:
        super().__init__()
        knp_mrphs = knp_bnst.mrph_list()
        knp_parent = knp_bnst.parent
        morphemes = [Morpheme(mrph) for mrph in knp_mrphs]
        kind = self.get_kind(knp_bnst.fstring)

        self.morphemes = morphemes
        self.parent = Bnst(knp_parent) if knp_parent is not None else None
        self.text = ''.join([mrph.repname for mrph in morphemes if not self.is_suffix(mrph.category)])
        self.raw_text = ''.join([mrph.morpheme for mrph in morphemes])
        self.kind = kind

    def get_kind(self, knp_fstring):
        for k, v in self.phrase_table.items():
            if k in knp_fstring:
                return v

        return None

    def have_subcategory_mrph(self, subcategories):
        matched = [mrph for mrph in self.morphemes for sub in mrph.subcategories if sub in subcategories]
        return len(matched) > 0


class Morpheme(LinguisticUnit):
    def __init__(self, knp_mrph) -> None:
        super().__init__()
        base = knp_mrph.genkei
        category = knp_mrph.bunrui
        subcategories = self._get_subcategories(knp_mrph)
        repname = self.get_repname(knp_mrph)
        spl = base.split('/')

        self.morpheme = spl[0] if len(spl) > 0 else None
        self.pronounce = spl[1] if len(spl) > 1 else None
        self.category = category
        self.repname = repname
        self.subcategories = subcategories

    def _get_subcategories(self, knp_mrph):
        imis = knp_mrph.imis
        matched = subcategory_pattern.match(imis)
        if not matched:
            return []

        sub = matched.group(1)
        return sub.split(';')

    def get_repname(self, knp_mrph):
        use_wiki_pattern = False
        if not use_wiki_pattern:
            return knp_mrph.repname.split('/')[0]

        fstring = knp_mrph.fstring
        matched = wiki_pattern.match(fstring)
        if not matched:
            return knp_mrph.repname.split('/')[0]

        sub = matched.group(1)
        return sub


class Tag(LinguisticUnit):
    def __init__(self, knp_tag) -> None:
        super().__init__()
        knp_mrphs = knp_tag.mrph_list()
        morphemes = [Morpheme(mrph) for mrph in knp_mrphs]
        text = ''.join([mrph.repname for mrph in morphemes if not self.is_suffix(mrph.category)])

        self.pas = knp_tag.pas
        self.morphemes = morphemes
        self.text = text


@dataclass
class CaseArg:
    tag: Any
    case: Any
    arg: Any


class ParsedLang:
    def __init__(self, parsed, verbose=False) -> None:
        knp_tags = parsed.tag_list()
        knp_bnsts = parsed.bnst_list()
        knp_morhs = parsed.mrph_list()
        # morh < tag < bnst

        self.tags = [Tag(tag) for tag in knp_tags]
        self.bnsts = [Bnst(bnst) for bnst in knp_bnsts]
        self.morhs = [Morpheme(morh) for morh in knp_morhs]
        self.verbose = verbose
        self.case_args = self.get_case_args(knp_tags)

    def get_case_args(self, knp_tags):
        cargs = []
        for i, knp_tag in enumerate(knp_tags):
            if knp_tag.pas is None:
                continue

            _cargs = []
            tag = self.tags[i]
            if self.verbose:
                print(f"target: {tag.text}")
            for case, args in knp_tag.pas.arguments.items():
                for arg in args:
                    if self.verbose:
                        print('\t格: %s,  項: %s  (項の基本句ID: %d)' % (case, arg.midasi, arg.tid))
                        print('\t', list(map(lambda x: x.text, self.tags)))

                    carg = CaseArg(tag, case, self.tags[arg.tid].text)
                    _cargs.append(carg)
            cargs.append((tag, _cargs))
        return cargs


class _LangParser:
    def __init__(self, knp_instance, verbose=False) -> None:
        self.knp = knp_instance
        self.verbose = verbose
        db = self._connect_db()
        self._create_table(db)
        db.close()

    def __call__(self, text) -> ParsedLang:
        db = self._connect_db()
        cached = self._fetch_from_table(text, db)
        if cached:
            parsed = self.knp.result(cached)
        else:
            parsed = self.knp_parse(text, db)

        db.close()
        return ParsedLang(parsed, verbose=self.verbose)

    def knp_parse(self, text, db):
        juman_lines = self.knp.juman.juman_lines(text)
        juman_str = "%s%s" % (juman_lines, self.knp.pattern)
        knp_lines = self.knp.analyzer.query(juman_str, pattern=r'^%s$' % self.knp.pattern)
        self._save_to_table(text, knp_lines, db)
        return self.knp.result(knp_lines)

    def _connect_db(self):
        DEBUG = False
        dbname = "parsed.db" if not DEBUG else ":memory:"
        db = sqlite3.connect(dbname, check_same_thread=False)
        return db

    def _create_table(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('CREATE TABLE parsed(id STRING PRIMARY KEY, result STRING)')
            db.commit()
        except sqlite3.OperationalError:
            pass
        cursor.close()

    def _save_to_table(self, text, parsed, db):
        cursor = db.cursor()
        key = self._hash(text)
        cursor.execute(f"INSERT INTO parsed values('{key}','{parsed}')")
        db.commit()
        cursor.close()

    def _fetch_from_table(self, text, db):
        cursor = db.cursor()
        key = self._hash(text)
        cursor.execute(f"SELECT result FROM parsed WHERE id = '{key}'")
        results = cursor.fetchall()
        cursor.close()
        fetched = results[0] if len(results) > 0 else [None]
        return fetched[0] if len(fetched) > 0 else None

    def _hash(self, text):
        hex = hashlib.sha256(text.encode('UTF-8')).hexdigest()
        return hex


class LangParser(_LangParser):
    def __init__(self, verbose=False) -> None:
        super().__init__(KNP(), verbose)


class LangParserWithServer(_LangParser):
    def __init__(self, port, verbose=False) -> None:
        super().__init__(ServerKNP(port=port), verbose)


class LangParserWithServer2(_LangParser):
    def __init__(self, port, verbose=False) -> None:
        super().__init__(ServerKNP2(port=port), verbose)


class LangParserWithPexpect(_LangParser):
    def __init__(self, verbose=False) -> None:
        super().__init__(PexpectKNP(), verbose)
