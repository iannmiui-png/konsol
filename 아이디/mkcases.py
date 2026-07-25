#!/usr/bin/env python3
"""
mkcases.py [n] [seed]

Builds jstest/cases.json: random Brainfuck programs, each compiled all the way
to a PNG by bf_to_png, paired with the output of a reference BF interpreter.
batchtest.js then replays them through the console page's own JS, so the whole
chain -- compiler, encoder, PNG, decoder, VM -- is what gets tested, not just
the compiler.
"""
import json
import os
import random
import sys
from collections import defaultdict

import bf_to_png as P


def ref(code, inp, limit=200000):
    t = defaultdict(int); p = 0; out = []; st = []; jm = {}
    for i, c in enumerate(code):
        if c == '[':
            st.append(i)
        elif c == ']':
            j = st.pop(); jm[j] = i; jm[i] = j
    inp = list(inp); cp = n = 0
    while cp < len(code):
        c = code[cp]
        if   c == '+': t[p] = (t[p] + 1) % 256
        elif c == '-': t[p] = (t[p] - 1) % 256
        elif c == '>': p += 1
        elif c == '<': p -= 1
        elif c == '.': out.append(chr(t[p]))
        elif c == ',': t[p] = ord(inp.pop(0)) if inp else 0
        elif c == '[' and not t[p]: cp = jm[cp]
        elif c == ']' and t[p]:     cp = jm[cp]
        cp += 1; n += 1
        if n > limit:
            return None
    return ''.join(out)


def gen(rng, depth=0):
    o = []
    for _ in range(rng.randint(1, 7)):
        r = rng.random()
        if   r < 0.24: o.append('+' * rng.randint(1, 6))
        elif r < 0.38: o.append('-' * rng.randint(1, 3))
        elif r < 0.52: o.append('>' * rng.randint(1, 3))
        elif r < 0.64: o.append('<' * rng.randint(1, 3))
        elif r < 0.76: o.append('.')
        elif r < 0.88: o.append(',')
        elif depth < 3: o.append('[' + '-' + gen(rng, depth + 1) + ']')
    return ''.join(o)


def main(n=60, seed=1234):
    rng = random.Random(seed)
    os.makedirs('jstest', exist_ok=True)
    alpha = P.alphabet()
    cases = []
    while len(cases) < n:
        prog = gen(rng)
        if prog.count('[') != prog.count(']'):
            continue
        inp = ''.join(rng.choice('AByz19 ') for _ in range(prog.count(',') + 2))
        expect = ref(prog, inp)
        if expect is None:
            continue
        k = len(cases)
        bf = f'jstest/c{k:03d}.b'
        png = f'jstest/c{k:03d}.png'
        open(bf, 'w').write(prog)
        grid = f'jstest/c{k:03d}.aheui'
        P.compile_grid(bf, grid)
        P.encode(grid, png, alpha, width=64)
        os.unlink(grid)
        # bfFile lets batchpage.js feed the SOURCE to the page, so both the
        # Python path (batchtest.js) and the in-page path can use one corpus
        cases.append({'bf': prog, 'bfFile': bf, 'input': inp,
                      'expect': expect, 'png': png})
    json.dump(cases, open('jstest/cases.json', 'w'))
    print(f'{len(cases)} cases -> jstest/cases.json')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60,
         int(sys.argv[2]) if len(sys.argv) > 2 else 1234)
