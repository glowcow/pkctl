#!/bin/python3
from main.node import node
import sys

com = sys.argv[1]
version = '0.1.0'

if __name__ == "__main__":
    if com=='node':
        node.pods(sys.argv[2])
    elif com=='version':
        print(f'{25*"-"}\nPyKubeCtl vesrion: {version}\n{25*"-"}')
    else:
        print(f'Unknown PyKubeCtl command: {com}')
