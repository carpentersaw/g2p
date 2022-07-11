import os
import pickle
import timeit
from copy import deepcopy
from pathlib import Path

import yaml
from networkx import DiGraph, read_gpickle, shortest_path, write_gpickle

from g2p.exceptions import MappingMissing, MalformedMapping
from g2p.mappings.utils import find_mapping, load_mapping_from_path

LANGS_DIR = os.path.dirname(__file__)
LANGS_PKL = os.path.join(LANGS_DIR, "langs.pkl")
LANGS_NWORK_PATH = os.path.join(LANGS_DIR, "network.pkl")


def cache_langs():
    """Read in all files and save as pickle"""
    langs = {}
    dir_path = Path(LANGS_DIR)
    # Sort by language code
    paths = sorted(dir_path.glob("./*/config.y*ml"), key=lambda x: x.parent.stem)
    mappings_legal_pairs = []
    for path in paths:
        code = path.parent.stem
        with open(path, encoding="utf8") as f:
            data = yaml.safe_load(f)
        # If there is a mappings key, there is more than one mapping
        # TODO: should put in some measure to prioritize non-generated mappings and warn when they override
        if "mappings" in data:
            for index, mapping in enumerate(data["mappings"]):
                mappings_legal_pairs.append(
                    (
                        data["mappings"][index]["in_lang"],
                        data["mappings"][index]["out_lang"],
                    )
                )
                data["mappings"][index] = load_mapping_from_path(path, index)
        else:
            data = load_mapping_from_path(path)
        langs[code] = data

    # Save as a Directional Graph
    lang_network = DiGraph()
    lang_network.add_edges_from(mappings_legal_pairs)

    with open(LANGS_NWORK_PATH, "wb") as f:
        write_gpickle(lang_network, f, protocol=4)

    with open(LANGS_PKL, "wb") as f:
        pickle.dump(langs, f, protocol=4)

    return langs


# Cache mappings as pickle file for quick loading
with open(LANGS_PKL, "rb") as f:
    LANGS = pickle.load(f)

LANGS_NETWORK = read_gpickle(LANGS_NWORK_PATH)
for k, v in LANGS.items():
    if k in ["generated", "font-encodings"]:
        continue
    if "mappings" in v:
        for vv in v["mappings"]:
            if "language_name" not in vv:
                raise MalformedMapping("language_name missing from mapping for " + k);
LANGS_AVAILABLE = []
for k, v in LANGS.items():
    if k in ["generated", "font-encodings"]:
        continue
    if "mappings" in v:
        LANGS_AVAILABLE.extend(vv["language_name"] for vv in v["mappings"])
    else:
        LANGS_AVAILABLE.append(v["language_name"])
MAPPINGS_AVAILABLE = []
for k, v in LANGS.items():
    if "mappings" in v:
        MAPPINGS_AVAILABLE.extend(v["mappings"])
    else:
        MAPPINGS_AVAILABLE.append(v)

if __name__ == "__main__":
    cache_langs()
