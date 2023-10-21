# [CoNLL23] JaSPICE: Automatic Evaluation Metric Using Predicate-Argument Structures for Image Captioning Models
[![Lint](https://github.com/keio-smilab23/JaSPICE/actions/workflows/lint.yaml/badge.svg)](https://github.com/keio-smilab23/JaSPICE/actions/workflows/lint.yaml)
[![Test](https://github.com/keio-smilab23/JaSPICE/actions/workflows/test.yaml/badge.svg)](https://github.com/keio-smilab23/JaSPICE/actions/workflows/test.yaml)

Evaluation code for machine-generated image captions in Japanese.

This code also implemented a scene-graph parser for Japanese.

<img width="1448" alt="system" src="https://user-images.githubusercontent.com/51681991/210318651-1d5f85b2-8fb9-459a-9cc4-10f1eb41d815.png">


## Instructions (using Docker)

### Clone & Install

```
pip install jaspice
```

or

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
wget 'https://github.com/keio-smilab23/JaSPICE/releases/download/0.0.1/jumanpp.tar.xz'

# JUMAN
wget 'https://github.com/keio-smilab23/JaSPICE/releases/download/0.0.1/juman.tar.bz2'

# KNP
wget 'https://github.com/keio-smilab23/JaSPICE/releases/download/0.0.1/knp.tar.bz2'
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
@inproceedings{wada2023,
   title     = {{JaSPICE: Automatic Evaluation Metric Using Predicate-Argument Structures for Image Captioning Models}},
   author    = {Wada, Yuiga  and Kaneda, Kanta  and Sugiura, Komei},
   year      = 2023,
   booktitle = {Proceedings of the 27th Conference on Computational Natural Language Learning (CoNLL)}
}
```

## Others

### Licenses

This work is licensed under the BSD-3-Clause-Clear license. To view a copy of this license, see [LICENSE](LICENSE).

- [JUMAN](https://github.com/keio-smilab23/JaSPICE/releases/download/0.0.1/JUMAN_COPYING.txt)
- [JUMANPP](https://github.com/keio-smilab23/JaSPICE/releases/download/0.0.1/JUMANPP_LICENSE.txt)
- [KNP](https://github.com/keio-smilab23/JaSPICE/releases/download/0.0.1/KNP_COPYING.txt)
