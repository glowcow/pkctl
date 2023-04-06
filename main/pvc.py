#!/usr/bin/env python3

from prettytable import PrettyTable
import concurrent.futures
from main.colors import bc
from main.api import KubeApi
import json, re

class KubernetesPVCUsage:

    def __init__(self, namespace=None):
        self.ns = namespace
        self.pvc_sum = []
        self.num_threads = 16
        self.k8s = KubeApi()
        self.k_client = self.k8s.kube_client_core()
        self.k_client_a = self.k8s.kube_client_apic()
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

    def list_pods(self):
        if self.ns:
            pods = self.k_client.list_namespaced_pod(namespace=self.ns)
            return pods
        else:
            pods = self.k_client.list_pod_for_all_namespaces()
            return pods

    def node_stats(self, node):
        base_url = self.k_client_a.configuration.host
        api_endpoint = f"/api/v1/nodes/{node}/proxy/stats/summary"
        out = self.k_client_a.request("GET", base_url + api_endpoint,)
        node_stats = json.loads(out.data)
        return node_stats

    def pvc_usage(self, pvc, pods):
        pvc_name = pvc["name"]
        node_name = None
        pod_name = None
        for pod in pods.items:
            for volume in pod.spec.volumes:
                if volume.persistent_volume_claim and volume.persistent_volume_claim.claim_name == pvc_name:
                    pod_name = pod.metadata.name
                    node_name = pod.spec.node_name
                    break
        if node_name:
            node_stats = self.node_stats(node_name)
            used_bytes = 0
            capacity_bytes = 0
            for pod in node_stats["pods"]:
                if pod["podRef"]["name"] == pod_name:
                    for volume in pod["volume"]:
                        if "pvcRef" in volume and volume["pvcRef"]["name"] == pvc_name:
                            used_bytes = volume["usedBytes"]
                            capacity_bytes = volume["capacityBytes"]
                            usage_percent = f'{((used_bytes/capacity_bytes)*100):.2f}'
                            self.pvc_sum.append(pvc["size"])
                            if round(float((usage_percent))) > 80:
                                self.t.add_row([pvc["name"], pvc["volume"], pvc["namespace"], pvc["status"], pvc["sc"], pvc["size"], f'{bc.YELLOW}{usage_percent}%{bc.ENDC}'])
                            elif round(float((usage_percent))) > 90:
                                self.t.add_row([pvc["name"], pvc["volume"], pvc["namespace"], pvc["status"], pvc["sc"], pvc["size"], f'{bc.RED}{usage_percent}%{bc.ENDC}'])
                            else:
                                self.t.add_row([pvc["name"], pvc["volume"], pvc["namespace"], pvc["status"], pvc["sc"], pvc["size"], f'{bc.GREEN}{usage_percent}%{bc.ENDC}'])

    def get_usage(self):
        pvcs = self.list_pvc()
        pods = self.list_pods()
        if pvcs:
            if self.ns:
                print(f"* {bc.BOLD}Listing PVC usage in namespace: {bc.CYAN}{self.ns}{bc.ENDC}")
            else:
                print(f"* {bc.BOLD}Listing PVC usage in namespace: {bc.CYAN}All{bc.ENDC}")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.pvc_usage, pvc, pods) for pvc in pvcs]
                for future in concurrent.futures.as_completed(futures):
                    continue
            size_usg = f'{round(self.list_sum(self.pvc_sum)/1024, 2)}Gb'
            print(f'| Summary PVC size: {bc.GREEN}{size_usg}{bc.ENDC}\n| Summary PVC count: {bc.GREEN}{len(pvcs)}{bc.ENDC}')
            print(self.t.get_string(sortby='Namespace'))
        else:
            print(f'{bc.RED}No PVC resources found!{bc.ENDC}')
