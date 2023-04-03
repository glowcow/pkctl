#!/usr/bin/env python3

from prettytable import PrettyTable
from main.colors import bc
from main.api import KubeApi
import json, subprocess, re

class KubernetesPVCUsage:
    def __init__(self, namespace=None):
        self.ns = namespace
        self.k8s = KubeApi()
        self.k_client = self.k8s.kube_client_core()
        self.t = PrettyTable(['PVC', 'Volume', 'Namespace', 'Status', 'SC', 'Size', 'Usage'])

    def list_sum(self, lst): #summary various metrics
        v_list = []
        for a in lst:
            if re.findall('Gi', a):
                v_list.append(int(a.split('Gi')[0])*1024)
            elif re.findall('Mi', a):
                v_list.append(int(a.split('Mi')[0]))
            elif re.findall('Ki', a):
                v_list.append(int(a.split('Ki')[0])/1024)
        if len(v_list) != 0 :
            out = int(sum(v_list)) # in megabytes
        else:
            out = None
        return out

    def list_pvc(self):
        pvc_list = []
        if self.ns:
            pvcs = self.k_client.list_namespaced_persistent_volume_claim(self.ns)
        else:
            pvcs = self.k_client.list_persistent_volume_claim_for_all_namespaces()
        for pvc in pvcs.items:
            pvc_list.append({'name': pvc.metadata.name, 'namespace':pvc.metadata.namespace, 'status': pvc.status.phase, 'sc': pvc.spec.storage_class_name, 'size': pvc.spec.resources.requests["storage"], 'volume': pvc.spec.volume_name})
        return pvc_list

    def pvc_usage(self, pvc_name):
        node_name = None
        pod_name = None
        if self.ns:
            pods = self.k_client.list_namespaced_pod(namespace=self.ns)
        else:
            pods = self.k_client.list_pod_for_all_namespaces()
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
        a = self.list_pvc()
        pvc_sum = []
        if a is not None:
            if self.ns is not None:
                print(f"* {bc.BOLD}Listing PVC usage in namespace: {bc.CYAN}{self.ns}{bc.ENDC}")
            else:
                print(f"* {bc.BOLD}Listing PVC usage in namespace: {bc.CYAN}All{bc.ENDC}")
            for b in a:
                pvc_sum.append(b["size"])
                prcnt_usg = f'{self.pvc_usage(b["name"]):.2f}'
                if round(float((prcnt_usg))) > 80:
                    self.t.add_row([b["name"], b["volume"], b["namespace"], b["status"], b["sc"], b["size"], f'{bc.YELLOW}{prcnt_usg}%{bc.ENDC}'])
                elif round(float((prcnt_usg))) > 90:
                    self.t.add_row([b["name"], b["volume"], b["namespace"], b["status"], b["sc"], b["size"], f'{bc.RED}{prcnt_usg}%{bc.ENDC}'])
                else:
                    self.t.add_row([b["name"], b["volume"], b["namespace"], b["status"], b["sc"], b["size"], f'{bc.GREEN}{prcnt_usg}%{bc.ENDC}'])
        size_usg = f'{round(self.list_sum(pvc_sum)/1024, 2)}Gb'
        print(f'| Summary PVC size: {bc.GREEN}{size_usg}{bc.ENDC}')
        print(self.t.get_string())
