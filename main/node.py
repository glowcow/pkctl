#!/bin/python3
from main.colors import bc
from main.api import kube_api
from prettytable import PrettyTable
import re

class node:
    def pods(node):
        try:
            print(f"Listing pods on node:  {bc.CYAN}{node}{bc.ENDC}")
            node_usage = kube_api.clnt_c.get_cluster_custom_object(group="metrics.k8s.io", version="v1beta1", plural="nodes", name=node)
            n_cpu_u = round(int(re.split("(\d+)", node_usage["usage"]["cpu"])[1])/1000000000, 3)
            n_mem_u = int(re.split("(\d+)", node_usage["usage"]["memory"])[1])//1024
            print(f'Overall node CPU usage: {bc.GREEN}{n_cpu_u}{bc.ENDC}\nOverall node Memory usage: {bc.GREEN}{n_mem_u}Mi{bc.ENDC}')
            field_selector = f'spec.nodeName={node},status.phase=Running'
            ret = kube_api.clnt.list_pod_for_all_namespaces(watch=False, field_selector=field_selector)
            t = PrettyTable(['Namespace', 'Pod', 'CPU', 'CPU lim', 'Memory', 'Memory lim'])
            for i in ret.items:
                if i.status.container_statuses[0].ready == True :
                    usage = kube_api.clnt_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
                    cpu_u = round(int(re.split("(\d+)", usage["containers"][0]["usage"]["cpu"])[1])/1000000000, 3)
                    mem_u = int(re.split("(\d+)", usage["containers"][0]["usage"]["memory"])[1])//1024
                    if i.spec.containers[0].resources.limits != None:
                        cpu_l = i.spec.containers[0].resources.limits.get("cpu")
                        mem_l = i.spec.containers[0].resources.limits.get("memory")
                        t.add_row([i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_l}', f'{mem_u}Mi', f'{mem_l}'])
                    else:
                        t.add_row([i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{bc.RED}None{bc.ENDC}', f'{mem_u}Mi', f'{bc.RED}None{bc.ENDC}'])
            print(t.get_string(sortby="CPU", reversesort=True))
        except Exception as e:
            print(f'{bc.RED}ERROR:{bc.ENDC} {e}')