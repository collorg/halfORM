#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--num', dest='num', type=int, default=10,
                    help='number of loops ')
parser.add_argument('--test-dir', dest='testdir',
                    const=sum, default=os.path.dirname(__file__),
                    nargs='?',
                    help='Test to profile. Default to all.')

args = parser.parse_args()

min = 9999
max = 0
sum = 0
dir = args.testdir
count = 0
for i in range(args.num):
    if count and count % 10 == 0:
        print()
    count += 1
    print(".", end="", flush=True)
    out = subprocess.check_output(
        ["nosetests3", "-q", dir], stderr=subprocess.STDOUT)
    out = float(out.decode('utf-8').split()[-2].replace('s', ''))
    if out < min:
        min = out
    if out > max:
        max = out
    sum += out
print()
print(min, max, sum/args.num)
