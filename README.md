# JaSPICE - Japanese SPICE

Evaluation code for machine-generated image captions in Japanese.

This code also implemented a scene-graph parser for Japanese.

<img width="1448" alt="system" src="https://user-images.githubusercontent.com/51681991/210318651-1d5f85b2-8fb9-459a-9cc4-10f1eb41d815.png">


## Instructions (using Docker)

### Clone & Install

```
git clone git@github.com:keio-smilab23/JaSPICE.git
cd JaSPICE
pip install -e .
```

### Build

```
docker build -t jaspice .
```

Run the docker container.

```
docker run -d -p 2115:2115 jaspice
```

### Usage

```python
from jaspice.api import JaSPICE

batch_size = 16
jaspice = JaSPICE(batch_size,server_mode=True)
_, score = jaspice.compute_score(references, candidates)
```


## Instructions (without Docker)

### Clone & Install

```
git clone git@github.com:keio-smilab23/JaSPICE.git
cd JaSPICE
pip install -e .
```

### Install JUMAN, JUMAN++, KNP

- juman : v7.01
- juman++ : v1.02
- knp : v4.20

```
# JUMAN++
wget 'http://nlp.ist.i.kyoto-u.ac.jp/DLcounter/lime.cgi?down=http://lotus.kuee.kyoto-u.ac.jp/nl-resource/jumanpp/jumanpp-1.02.tar.xz&name=jumanpp-1.02.tar.xz' 

# JUMAN
wget 'http://nlp.ist.i.kyoto-u.ac.jp/nl-resource/juman/juman-7.01.tar.bz2' -O /tmp/juman.tar.bz2 

# KNP
wget 'https://nlp.ist.i.kyoto-u.ac.jp/DLcounter/lime.cgi?down=https://nlp.ist.i.kyoto-u.ac.jp/nl-resource/knp/knp-4.20.tar.bz2&name=knp-4.20.tar.bz2'
```

## Usage

```python
from jaspice.api import JaSPICE

batch_size = 16
jaspice = JaSPICE(batch_size,server_mode=False)
_, score = jaspice.compute_score(references, candidates)
```



## Scene Graph Example

- 「人通りの少なくなった道路で青いズボンを着た男の子がオレンジ色のヘルメットを被りスケートボードに乗っている．」

<img src="https://user-images.githubusercontent.com/51681991/222105941-e170a4e2-6acb-4a5c-931e-b5c9f2eb18be.png" width="40%"><img src="https://user-images.githubusercontent.com/51681991/222106064-ac1575e3-bbf4-4417-9d93-290948bc8943.png" width="49%">


## BibTex

```
@InProceedings{jaspice,
    title     = {JaSPICE: 日本語における述語項構造に基づく画像キャプション生成モデルの自動評価尺度},
    author = {和田唯我 and 兼田寛大 and 杉浦孔明},
    year      = {2023},
    booktitle = {言語処理学会第29回年次大会}
}
```

