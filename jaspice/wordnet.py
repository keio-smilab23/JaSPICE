import sqlite3
import os
import requests
import gzip
import shutil
from tqdm import tqdm

PATH = "wnjpn.db"


class JaWordNet:
    def _download_db(self):
        # download
        print("Download wordnet database ... ")
        url = "https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz"
        res = requests.get(url, stream=True)
        size = int(res.headers.get('content-length', 0))
        pbar = tqdm(total=size, unit="B", unit_scale=True)
        with open("wnjpn.db.gz", 'wb') as file:
            for chunk in res.iter_content(chunk_size=1024):
                file.write(chunk)
                pbar.update(len(chunk))
            pbar.close()

        # extract
        with gzip.open("wnjpn.db.gz", mode="rb") as gzip_file:
            with open(PATH, mode="wb") as decompressed_file:
                shutil.copyfileobj(gzip_file, decompressed_file)

    def _get_wordid(self, db, lemma):
        cur = db.execute("select wordid from word where lemma='%s'" % lemma)
        for row in cur:
            wordid = row[0]
        return wordid

    def _get_synsets(self, db, wordid):
        synsets = []
        cur = db.execute("select synset from sense where wordid='%s'" % wordid)
        for row in cur:
            synsets.append(row[0])
        return synsets

    def get_synonyms(self, query):
        if not os.path.exists(PATH):
            self._download_db()
        db = sqlite3.connect(PATH)
        try:
            wordid = self._get_wordid(db, query)
        except BaseException:
            db.close()
            return []

        synsets = self._get_synsets(db, wordid)
        synonyms = []
        for synset in synsets:
            cur1 = db.execute("select wordid from sense where (synset='%s' and wordid!='%s' and lang='jpn')" % (synset, wordid))
            for row1 in cur1:
                tg_wordid = row1[0]
                cur2 = db.execute("select lemma from word where wordid=%s" % tg_wordid)
                synonyms.extend([c[0] for c in cur2])

        db.close()
        return synonyms
