#!/usr/bin/env python3
class ezlist(list):
    def append_dedup(self, x, reindex=False):
        if x in self:
            if reindex:
                self.remove_all(x)
                self.append(x)
        else:
            self.append(x)

    def remove_all(self, x):
        i = 0
        while True:
            try:
                if self[i] == x:
                    del self[i]
                else:
                    i += 1
            except IndexError:
                break
