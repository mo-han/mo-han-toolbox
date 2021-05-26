import sys
from glob import glob

from mylib.sites.bilibili.__to_be_deprecated__ import jijidown_rename_alpha

if __name__ == '__main__':
    # _, base = os.path.split(sys.argv[1])
    if sys.argv[1][-1] == '*':
        args = glob(sys.argv[1])
    else:
        args = sys.argv[1:]
    for i in args:
        jijidown_rename_alpha(i)
