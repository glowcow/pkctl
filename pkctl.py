#!/usr/bin/env python3

import argparse
from main.node import Node
from main.colors import bc
from main.pvc import KubernetesPVCUsage

version = '0.1.0'

def main():
    parser = argparse.ArgumentParser(description=f"{25 * '-'}\nPyKubeCtl version: {version}\n{25 * '-'}")
    subparsers = parser.add_subparsers(dest="command")

    node_parser = subparsers.add_parser("node", help="Get usage resources of kubernetes nodes")
    node_parser.add_argument("node", help="'node name', 'all' or 'brief'")
    node_parser.add_argument("-s", "--sort", choices=["cpu", "mem"], default="cpu",
                             help="Sort output by 'cpu' (default, cpu usage) or 'mem' (memory usage)")

    pvc_parser = subparsers.add_parser("pvc", help="Get kubernetes PVC usage statistics")
    pvc_parser.add_argument("-n", "--namespace", help="List PVC in specific namespace")

    version_parser = subparsers.add_parser("version", help="Display PyKubeCtl version")

    args = parser.parse_args()

    if args.command == "node":
        try:
            node = Node(args.node, args.sort)
            node.resources()
        except Exception as e:
            print(f"{bc.RED}ERROR[main]: {e}{bc.ENDC}")
    elif args.command == "pvc":
        try:
            k8s_pvc = KubernetesPVCUsage(args.namespace)
            k8s_pvc.get_usage()
        except Exception as e:
            print(f"{bc.RED}ERROR[main]: {e}{bc.ENDC}")
    elif args.command == "version":
        print(f"{25 * '-'}\nPyKubeCtl version: {version}\n{25 * '-'}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
