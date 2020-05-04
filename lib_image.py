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
from lib_basic import percentage

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
DEFAULT_IMAGEHASH_METHOD = DHASH
DEFAULT_IMAGEHASH_SIZE = 16
IMAGEHASH_FILENAME = 'imagehash.json'
SIMILAR_IMAGE_FOLDER = '__similar__'


def ist2hd(
        similarity_threshold: float,
        hash_size: int = DEFAULT_IMAGEHASH_SIZE,
        **kwargs
):
    """image similarity threshold to hamming distance"""
    return int(hash_size * hash_size * (1 - similarity_threshold))


def list_all_image_files():
    listdir = os.listdir(os.curdir)
    return [i for i in listdir if os.path.splitext(i)[-1] in IMAGE_FILE_EXTENSION]


def open_image_file(path: str) -> Image.Image:
    return Image.open(path)


def hash_image_file(
        image_path: str,
        hash_m: str = DEFAULT_IMAGEHASH_METHOD,
        hash_db: dict = None,
        hash_size: int = DEFAULT_IMAGEHASH_SIZE,
        trans: bool = True,
        **kwargs
):
    if hash_db:
        try:
            return hash_db[hash_m + str(hash_size)][image_path]
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
    return [HASH_FUNC[hash_m](v, hash_size=hash_size, **kwargs) for v in variants_l]


def write_imagehash_file(hash_db: dict = None, path: str = IMAGEHASH_FILENAME):
    d = copy.deepcopy(hash_db) if hash_db else dict()
    with open(path, 'w') as fp:
        for m in d:  # m is hash_method
            for i in d[m]:  # i is image_path
                d[m][i] = [str(h) for h in d[m][i]]  # h is single hash in the `d[m][i]` list
        json.dump(d, fp, indent=4, sort_keys=True)


def read_imagehash_file(path: str = IMAGEHASH_FILENAME):
    try:
        with open(path, 'r') as fp:
            d = json.load(fp) or dict()
            for m in d:  # m is hash_method
                for i in list(d[m]):  # i is image_path
                    if os.path.isfile(i):
                        d[m][i] = [hex_to_hash(h) for h in d[m][i]]  # h is single hash in the `d[m][i]` list
                    else:
                        del d[m][i]
            return d
    except FileNotFoundError:
        return dict()


def hash_all_image_files(
        hash_db: dict = None,
        hash_m: str = DEFAULT_IMAGEHASH_METHOD,
        hash_size: int = DEFAULT_IMAGEHASH_SIZE,
        trans: bool = True,
        stat: bool = True,
        **kwargs
):
    m = hash_m + str(hash_size)
    d = hash_db or {m: {}}
    dm = d[m]
    images_l = list_all_image_files()
    effect_cnt, round_cnt = 0, 0
    total_cnt = len(images_l)
    for f in images_l:
        if f not in dm:
            dm[f] = hash_image_file(f, hash_m=hash_m, hash_size=hash_size, trans=trans, **kwargs)
            if stat:
                effect_cnt += 1
        if stat:
            round_cnt += 1
            print(percentage(round_cnt / total_cnt), total_cnt, round_cnt, effect_cnt, end='\r')
    if stat:
        print()
    return d


def diff_image_hash_list(hash_list1: list, hash_list2: list):
    diff = min([hash1 - hash2 for hash1 in hash_list1 for hash2 in hash_list2])
    return diff


def pair_similar_images(
        hash_db: dict,
        threshold: float = 0.8,
        hash_m: str = DEFAULT_IMAGEHASH_METHOD,
        hash_size: int = DEFAULT_IMAGEHASH_SIZE,
        stat: bool = True,
        **kwargs
):
    max_diff = ist2hd(threshold, hash_size=hash_size)
    diff_pairs_ll = []
    dm = hash_db[hash_m + str(hash_size)]
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
            print(percentage(round_cnt / total_cnt), total_cnt, round_cnt, effect_cnt, end='\r')
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
            print(percentage(round_cnt / total_cnt), total_cnt, round_cnt, len(list(groups_ds.itersets())), end='\r')
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
        hash_m: str = DEFAULT_IMAGEHASH_METHOD,
        hash_size: int = DEFAULT_IMAGEHASH_SIZE,
        trans: bool = True,
        stat: bool = True,
        **kwargs
):
    if not thresholds:
        thresholds = [0.95, 0.8, 0.65, 0.5]
    common_kwargs = {'hash_m': hash_m, 'hash_size': hash_size, 'trans': trans, 'stat': stat}
    db = hash_all_image_files(hash_db=read_imagehash_file(), **common_kwargs)
    write_imagehash_file(db)
    similar_pairs_ll = pair_similar_images(db, min(thresholds), **common_kwargs)
    hd_l = [ist2hd(th, hash_size=hash_size) for th in thresholds]
    hd_l.sort()
    gs = DisjointSet()
    last_hd = 0
    for hd in hd_l:
        sp_ll = similar_pairs_ll[last_hd:hd + 1]
        last_hd = hd + 1
        gs = group_similar_images(sp_ll, groups_ds=gs, **common_kwargs)
        view_similar_image_groups(gs)


def view_similar_images(
        basic_thres: float = 0.8,
        extend: bool = False,
        extend_thres: float = 0.5,
        hash_m: str = DEFAULT_IMAGEHASH_METHOD,
        hash_size: int = DEFAULT_IMAGEHASH_SIZE,
        verbose: bool = True,
        **kwargs
):
    cmd = 'call "{}"' if os.name == 'nt' else '"{}"'
    basic_max_diff = ist2hd(basic_thres, hash_size=hash_size)
    db = read_imagehash_file()
    db = hash_all_image_files(hash_db=db, hash_m=hash_m, hash_size=hash_size, stat=verbose)
    write_imagehash_file(db)
    if extend:
        similar_pairs_ll = pair_similar_images(db, extend_thres, hash_m=hash_m, hash_size=hash_size, stat=verbose)
        basic_similar_pairs_ll = similar_pairs_ll[:basic_max_diff + 1]
    else:
        basic_similar_pairs_ll = \
            similar_pairs_ll = pair_similar_images(db, basic_thres, hash_m=hash_m, hash_size=hash_size)
    groups_ds = group_similar_images(basic_similar_pairs_ll, stat=verbose)
    groups_l = list(groups_ds.itersets())
    if extend:
        for diff_pairs_l in similar_pairs_ll[basic_max_diff + 1:]:
            for pair in diff_pairs_l:
                x, y = pair
                if max([len(g) for g in groups_l if x in g or y in g] + [0]) <= 5:
                    groups_ds.union(x, y)
                    groups_l = list(groups_ds.itersets())
    folder = SIMILAR_IMAGE_FOLDER
    if not os.path.isdir(folder):
        os.mkdir(folder)
    for g in groups_l:
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


def view_similar_images_twice():
    view_similar_images(extend=False)
    view_similar_images(extend=True)
