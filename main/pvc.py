#!/usr/bin/env python3

from kubernetes import client, config
from prettytable import PrettyTable
from main.colors import bc
from main.api import kube_api
import json, subprocess

class KubernetesPVCUsage:
    def __init__(self, namespace=None):
        self.ns = namespace

    def list_pvc(self):
        pvc_list = []
        if self.ns:
            pvcs = kube_api.clnt.list_namespaced_persistent_volume_claim(self.ns)
        else:
            pvcs = kube_api.clnt.list_persistent_volume_claim_for_all_namespaces()
        for pvc in pvcs.items:
            pvc_list.append({'name': pvc.metadata.name, 'namespace':pvc.metadata.namespace, 'status': pvc.status.phase, 'sc': pvc.spec.storage_class_name, 'size': pvc.spec.resources.requests["storage"], 'volume': pvc.spec.volume_name})
        return pvc_list

    def pvc_usage(self, pvc_name):
        node_name = None
        pod_name = None
        if self.ns:
            pods = kube_api.clnt.list_namespaced_pod(namespace=self.ns)
        else:
            pods = kube_api.clnt.list_pod_for_all_namespaces()
        for pod in pods.items:
            for volume in pod.spec.volumes:
                if volume.persistent_volume_claim and volume.persistent_volume_claim.claim_name == pvc_name:
                    pod_name = pod.metadata.name
                    node_name = pod.spec.node_name
                    break
        if not node_name:
            return 0

        command = f"kubectl get --raw /api/v1/nodes/{node_name}/proxy/stats/summary"
        node_stats = json.loads(subprocess.check_output(command, shell=True, text=True))
        used_bytes = 0
        capacity_bytes = 0
        for pod in node_stats["pods"]:
            if pod["podRef"]["name"] == pod_name:
                for volume in pod["volume"]:
                    if "pvcRef" in volume and volume["pvcRef"]["name"] == pvc_name:
                        used_bytes = volume["usedBytes"]
                        capacity_bytes = volume["capacityBytes"]
                        usage_percent = (used_bytes / capacity_bytes) * 100
                        return usage_percent
        return None

    def get_usage(self):
        t = PrettyTable(['PVC', 'Volume', 'Namespace', 'Status', 'SC', 'Size', 'Usage'])
        a = self.list_pvc()
        if a is not None:
            if self.ns is not None:
                print(f"* {bc.BOLD}Listing PVC usage in namespace:  {bc.CYAN}{self.ns}{bc.ENDC}")
            else:
                print(f"* {bc.BOLD}Listing PVC usage in namespace:  {bc.CYAN}All{bc.ENDC}")
            for b in a:
                prcnt_usg = f'{self.pvc_usage(b["name"]):.2f}'
                t.add_row([b["name"], b["volume"], b["namespace"], b["status"], b["sc"], b["size"], f'{prcnt_usg}%'])
        print(t.get_string())
