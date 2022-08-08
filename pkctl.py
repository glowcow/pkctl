#!/bin/python3
from main.node import node
from main.pod import pod
import sys

com = sys.argv[1]
version = '0.1.0'

if __name__ == "__main__":
    if com=='node':
        r = node(sys.argv[2])
        r.resources()
    elif com=='pods':
        pod.resources()
    elif com=='version':
        print(f'{25*"-"}\nPyKubeCtl vesrion: {version}\n{25*"-"}')
    else:
        print(f'Unknown PyKubeCtl command: {com}')
