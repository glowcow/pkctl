#!/bin/python3
from main.colors import bc
from main.api import kube_api
from prettytable import PrettyTable
import re

class pod:
    def resources():
        try:
            field_selector = f'status.phase=Running'
            pods = kube_api.clnt.list_pod_for_all_namespaces(watch=False, field_selector=field_selector)
            t = PrettyTable(['Node', 'Namespace', 'Pod', 'CPU', 'CPU lim', 'Memory', 'Memory lim'])
            cpu_sum = []
            mem_sum = []
            for i in pods.items:
                if i.status.container_statuses[0].ready == True :
                    usage = kube_api.clnt_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
                    cpu_u = round(int(re.split("(\d+)", usage["containers"][0]["usage"]["cpu"])[1])/1000000000, 3)
                    cpu_sum.append(cpu_u)
                    mem_u = int(re.split("(\d+)", usage["containers"][0]["usage"]["memory"])[1])//1024
                    mem_sum.append(mem_u)
                    if i.spec.containers[0].resources.limits != None:
                        node = i.spec.node_name
                        cpu_l = i.spec.containers[0].resources.limits.get("cpu")
                        mem_l = i.spec.containers[0].resources.limits.get("memory")
                        t.add_row([node, i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_l}', f'{mem_u}Mi', f'{mem_l}'])
                    else:
                        t.add_row([node, i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{bc.RED}None{bc.ENDC}', f'{mem_u}Mi', f'{bc.RED}None{bc.ENDC}'])
            print(f'Listing all pods on all nodes\nOverall running pods count: {bc.GREEN}{len(pods.items)}{bc.ENDC}\nOverall Cluster CPU usage: {bc.GREEN}{round(sum(cpu_sum), 2)}{bc.ENDC}\nOverall Cluster Memory usage: {bc.GREEN}{sum(mem_sum)}Mi{bc.ENDC}')
            print(t.get_string(sortby="CPU", reversesort=True))
        except Exception as e:
            print(f'{bc.RED}ERROR:{bc.ENDC} {e}')