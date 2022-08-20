#!/bin/python3
from main.node import node
import sys

version = '0.1.0'

if __name__ == "__main__" :
    if len(sys.argv) < 2:
        sys.stderr.write(f'ERROR[main]: please specify command\n')
    else:
        com = sys.argv[1]
        if com == 'node' :
            try:
                ci = node(sys.argv)
                ci.resources()
            except Exception as e:
                sys.stderr.write(f'ERROR[main]: {e}\n')
        elif com=='version':
            print(f'{25*"-"}\nPyKubeCtl vesrion: {version}\n{25*"-"}')
        else:
            sys.stderr.write(f'ERROR[main]: Unknown PyKubeCtl command: {com}\n')
