#!/usr/bin/env python3
"""
repair_aheui.py <in.aheui> <out.aheui>

Replaces the old one-row input block with the current two-row form.

The old block was 마밯 on a single row: a silent pop then an input push, both
with jungseong ㅏ, which moves right. After the push, control ran off the end
of the row, wrapped to column 0 of the same row, and did it again -- forever.
Any grid built before that fix hangs at its first prompt, having printed
everything up to it, which looks like a loading failure and is not one.

The current block is 무 then 붛 on two rows: the same two operations with
jungseong ㅜ, so the block is entered and left at column 0 moving down, like
every other leaf block.

Inserting a row is safe here. The loop scaffold's bypass lanes are vertical
columns that glide until they meet a landing row, so nothing downstream is
addressed by absolute row number -- which is the same property that lets the
streaming compiler emit a loop before it knows how tall the body is.
"""
import sys

import bf_to_aheui as C

OLD = C.compose(6, 0) + C.compose(7, 0, 27)         # 마밯: pop right, input right
NEW = [C.compose(6, 13), C.compose(7, 13, 27)]      # 무 / 붛: both downward


def repair(src, dst):
    fixed = rows_in = rows_out = 0
    with open(src, encoding='utf-8') as f, open(dst, 'w', encoding='utf-8') as o:
        for line in f:
            rows_in += 1
            if line.rstrip('\n') == OLD:
                o.write(NEW[0] + '\n' + NEW[1] + '\n')
                rows_out += 2
                fixed += 1
            else:
                o.write(line)
                rows_out += 1
    return fixed, rows_in, rows_out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    fixed, a, b = repair(argv[0], argv[1])
    print(f'{argv[0]} -> {argv[1]}')
    print(f'  input blocks repaired: {fixed}')
    print(f'  rows {a:,} -> {b:,}')
    if not fixed:
        print('  (nothing matched; this grid was already built with the current block)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
