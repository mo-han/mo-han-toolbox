#!/usr/bin/env python3
# encoding=utf8
import copy
import json
import os
import shutil
from itertools import combinations

from PIL import Image
from disjoint_set import DisjointSet
from imagehash import average_hash, dhash, phash, whash, hex_to_hash
from lib_misc import percentage

AHASH = 'ahash'
DHASH = 'dhash'
PHASH = 'phash'
WHASH = 'whash'
HASH_FUNC = {
    AHASH: average_hash,
    DHASH: dhash,
    PHASH: phash,
    WHASH: whash,
}

IMAGE_FILE_EXTENSION = ['.webp', '.jpg', '.bmp', '.jpeg', '.png']
DEFAULT_IMAGE_HASHTYPE = DHASH
DEFAULT_IMAGE_HASHSIZE = 16
IMAGEHASH_FILENAME = 'imagehash.json'
SIMILAR_IMAGE_FOLDER = '__similar__'


def ist2hd(
        similarity_threshold: float,
        hashsize: int = DEFAULT_IMAGE_HASHSIZE,
        **kwargs
):
    """image similarity threshold to hamming distance"""
    return int(hashsize * hashsize * (1 - similarity_threshold))


def list_all_image_files():
    listdir = os.listdir(os.curdir)
    return [i for i in listdir if os.path.splitext(i)[-1] in IMAGE_FILE_EXTENSION]


def open_image_file(path: str) -> Image.Image:
    return Image.open(path)


def hash_image_file(
        image_path: str,
        hashtype: str = DEFAULT_IMAGE_HASHTYPE,
        hash_db: dict = None,
        hashsize: int = DEFAULT_IMAGE_HASHSIZE,
        trans: bool = True,
        **kwargs
):
    if hash_db:
        try:
            return hash_db[hashtype + str(hashsize)][image_path]
        except KeyError:
            pass
    image_o = open_image_file(image_path)
    variants_l = [image_o]
    if trans:
        variants_l += [
            image_o.transpose(Image.ROTATE_90),
            image_o.transpose(Image.ROTATE_180),
            image_o.transpose(Image.ROTATE_270),
            image_o.transpose(Image.FLIP_LEFT_RIGHT),
            image_o.transpose(Image.FLIP_TOP_BOTTOM),
        ]
    return [HASH_FUNC[hashtype](v, hash_size=hashsize, **kwargs) for v in variants_l]


def write_imagehash_file(hash_db: dict = None, path: str = IMAGEHASH_FILENAME):
    d = copy.deepcopy(hash_db) if hash_db else dict()
    with open(path, 'w') as fp:
        for m in d:  # m is hashtype
            for i in d[m]:  # i is image_path
                d[m][i] = [str(h) for h in d[m][i]]  # h is single hash in the `d[m][i]` list
        json.dump(d, fp, indent=4, sort_keys=True)


def read_imagehash_file(path: str = IMAGEHASH_FILENAME):
    try:
        with open(path, 'r') as fp:
            db = json.load(fp) or dict()
            for key in db:  # key is hashtype & hashsize
                for i in list(db[key]):  # i is image_path
                    if os.path.isfile(i):
                        db[key][i] = [hex_to_hash(h) for h in db[key][i]]  # h is single hash in the `db[key][i]` list
                    else:
                        del db[key][i]
            return db
    except FileNotFoundError:
        return dict()


def hash_all_image_files(
        hash_db: dict = None,
        hashtype: str = DEFAULT_IMAGE_HASHTYPE,
        hashsize: int = DEFAULT_IMAGE_HASHSIZE,
        trans: bool = True,
        stat: bool = True,
        **kwargs
):
    key = hashtype + str(hashsize)
    db = hash_db or {key: {}}
    dk = db[key]
    images_l = list_all_image_files()
    effect_cnt, round_cnt = 0, 0
    total_cnt = len(images_l)
    for f in images_l:
        if f not in dk:
            dk[f] = hash_image_file(f, hashtype=hashtype, hashsize=hashsize, trans=trans, **kwargs)
            if stat:
                effect_cnt += 1
        if stat:
            round_cnt += 1
            print('hash:', percentage(round_cnt / total_cnt), total_cnt, round_cnt, effect_cnt, end='\r')
    if stat:
        print()
    return db


def diff_image_hash_list(hash_list1: list, hash_list2: list):
    diff = min([hash1 - hash2 for hash1 in hash_list1 for hash2 in hash_list2])
    return diff


def pair_similar_images(
        hash_db: dict,
        threshold: float = 0.8,
        hashtype: str = DEFAULT_IMAGE_HASHTYPE,
        hashsize: int = DEFAULT_IMAGE_HASHSIZE,
        stat: bool = True,
        **kwargs
):
    max_diff = ist2hd(threshold, hashsize=hashsize)
    diff_pairs_ll = []
    dm = hash_db[hashtype + str(hashsize)]
    for _ in range(max_diff + 1):
        diff_pairs_ll += [list()]
    image_pairs_l = [c for c in combinations(dm, 2)]
    effect_cnt, round_cnt = 0, 0
    total_cnt = len(image_pairs_l)
    for img1, img2 in image_pairs_l:
        diff = diff_image_hash_list(dm[img1], dm[img2])
        if diff <= max_diff:
            diff_pairs_ll[diff].append((img1, img2))
            if stat:
                effect_cnt += 1
        if stat:
            round_cnt += 1
            print('diff:', percentage(round_cnt / total_cnt), total_cnt, round_cnt, effect_cnt, end='\r')
    if stat:
        print()
    return diff_pairs_ll


def group_similar_images(
        similar_pairs_ll: list,
        groups_ds: DisjointSet = None,
        stat: bool = True,
        **kwargs
) -> DisjointSet:
    if not groups_ds:
        groups_ds = DisjointSet()
    pairs_l = [pair for pairs in similar_pairs_ll for pair in pairs]
    round_cnt, total_cnt = 0, len(pairs_l)
    for pair in pairs_l:
        groups_ds.union(*pair)
        if stat:
            round_cnt += 1
            print('group:', percentage(round_cnt / total_cnt), total_cnt, round_cnt, len(list(groups_ds.itersets())),
                  end='\r')
    if stat:
        print()
    return groups_ds


def view_similar_image_groups(similar_groups: DisjointSet):
    cmd = 'call "{}"' if os.name == 'nt' else '"{}"'
    folder = SIMILAR_IMAGE_FOLDER
    if not os.path.isdir(folder):
        os.mkdir(folder)
    for g in list(similar_groups.itersets()):
        real_files = []
        for f in g:
            if os.path.isfile(f):
                real_files.append(f)
        if len(real_files) < 2:
            continue
        for f in real_files:
            shutil.move(f, folder)
        os.system(cmd.format(os.path.join(folder, real_files[0])))
        for f in real_files:
            try:
                shutil.move(os.path.join(folder, f), '.')
            except (FileNotFoundError, shutil.Error):
                pass
    os.removedirs(folder)


def view_similar_images_auto(
        thresholds: list = None,
        hashtype: str = None,
        hashsize: int = None,
        trans: bool = True,
        stat: bool = True,
        dryrun: bool = False,
        **kwargs
):
    thresholds = thresholds or [0.95, 0.8, 0.65]
    thresholds.sort(reverse=True)
    hashtype = hashtype or DEFAULT_IMAGE_HASHTYPE
    hashsize = hashsize or DEFAULT_IMAGE_HASHSIZE
    common_kwargs = {'hashtype': hashtype, 'hashsize': hashsize, 'trans': trans, 'stat': stat}
    db = hash_all_image_files(hash_db=read_imagehash_file(), **common_kwargs)
    write_imagehash_file(db)
    similar_pairs_ll = pair_similar_images(db, min(thresholds), **common_kwargs)
    hd_l = [ist2hd(th, hashsize=hashsize) for th in thresholds]
    hd_l.sort()
    last_hd = 0
    for hd in hd_l:
        gs = DisjointSet()
        sp_ll = similar_pairs_ll[last_hd:hd + 1]
        last_hd = hd + 1
        gs = group_similar_images(sp_ll, groups_ds=gs, **common_kwargs)
        if not dryrun:
            if stat:
                print('hamming distance:', hd)
            view_similar_image_groups(gs)
