"""Shared readers for tools/export_site_data.py and tools/check_numbers.py (no GROVE imports, standard library only)."""
import re
NUMRE = re.compile(r'[-+]?\d+(?:\.\d+)?')
def jget(o, path):
    for k in path: o = o[k]
    return o
def md_table_cell(path, heading, row_key, col, nth=0):
    """Cell of a Markdown table: the block that starts at the line equal to `heading` and ends at the next heading of the
    same or a higher level; the first table in it with a column named `col`; the nth row whose first cells equal
    row_key (a list; '**' is ignored)."""
    L = open(path, encoding='utf-8').read().split('\n')
    i = next(k for k, l in enumerate(L) if l.strip() == heading); lvl = len(heading) - len(heading.lstrip('#'))
    k = i + 1; tabs = []
    while k < len(L):
        s = L[k]
        if s.startswith('#'):
            l2 = len(s) - len(s.lstrip('#'))
            if l2 <= lvl: break
        if s.startswith('|'):
            t = []
            while k < len(L) and L[k].startswith('|'): t.append([c.strip() for c in L[k].strip().strip('|').split('|')]); k += 1
            tabs.append(t); continue
        k += 1
    for t in tabs:
        head = [h.replace('**', '') for h in t[0]]
        if col not in head: continue
        for r in t[2:]:
            if [c.replace('**', '') for c in r[:len(row_key)]] == list(row_key):
                if nth == 0: return r[head.index(col)]
                nth -= 1
    raise KeyError((heading, row_key, col))
