#!/bin/python3
from main.colors import bc
from main.api import kube_api
from prettytable import PrettyTable
import re

class pod:

    def __init__(self):
        pass

    def list_sum(self, lst):
        cpu_list = []
        mem_list = []
        for a in lst:
            if a.isnumeric():
                d = int(a)
                cpu_list.append(d)
            elif re.findall('m', a):
                cpu_list.append(int(a.split('m')[0])/1000)
            elif re.findall('Mi', a):
                mem_list.append(int(a.split('Mi')[0]))
        if len(cpu_list) != 0 :
            out = round(float(sum(cpu_list)), 2)
        elif len(mem_list) != 0 :
            out = sum(mem_list)
        return out

    def resources(self):
        try:
            print(f'* {bc.BOLD}Listing all pods on all nodes{bc.ENDC}')
            field_selector = f'status.phase=Running'
            pods = kube_api.clnt.list_pod_for_all_namespaces(watch=False, field_selector=field_selector)
            t = PrettyTable(['Node', 'Namespace', 'Pod', 'CPU', 'CPU req', 'CPU lim', 'Memory', 'Memory req', 'Memory lim'])
            cpu_sum = []
            mem_sum = []
            cpu_rl = []
            mem_rl = []
            for i in pods.items:
                if i.status.container_statuses[0].ready == True :
                    #print(i.spec.node_name)
                    usage = kube_api.clnt_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
                    cpu_u = round(int(re.split("(\d+)", usage["containers"][0]["usage"]["cpu"])[1])/1000000000, 3)
                    cpu_sum.append(cpu_u)
                    mem_u = int(re.split("(\d+)", usage["containers"][0]["usage"]["memory"])[1])//1024
                    mem_sum.append(mem_u)
                    if i.spec.containers[0].resources.limits != None and i.spec.containers[0].resources.requests != None :
                        cpu_l = i.spec.containers[0].resources.limits.get("cpu")
                        cpu_r = i.spec.containers[0].resources.requests.get("cpu")
                        cpu_rl.append(cpu_r)
                        mem_l = i.spec.containers[0].resources.limits.get("memory")
                        mem_r = i.spec.containers[0].resources.requests.get("memory")
                        mem_rl.append(mem_r)
                        if mem_l == None :
                            t.add_row([i.spec.node_name, i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_r}', f'{cpu_l}', f'{mem_u}Mi', f'{mem_r}', f'{bc.YELLOW}{mem_l}{bc.ENDC}'])
                        elif cpu_l == None:
                            t.add_row([i.spec.node_name, i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_r}', f'{bc.YELLOW}{cpu_l}{bc.ENDC}', f'{mem_u}Mi', f'{mem_r}', f'{mem_l}'])
                        else:
                            t.add_row([i.spec.node_name, i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_r}', f'{cpu_l}', f'{mem_u}Mi', f'{mem_r}', f'{mem_l}'])
                    else:
                        t.add_row([i.spec.node_name, i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{bc.RED}None{bc.ENDC}', f'{bc.RED}None{bc.ENDC}', f'{mem_u}Mi', f'{bc.RED}None{bc.ENDC}', f'{bc.RED}None{bc.ENDC}'])
            cpu_tr = self.list_sum(cpu_rl)
            mem_tr = self.list_sum(mem_rl)
            #pc_cpu_r = round((float(cpu_tr)/float(n_cpu_a))*100)
            #pc_mem_r = round((mem_tr/n_mem_a)*100)
            print(f'| Overall running pods count: {bc.GREEN}{len(pods.items)}{bc.ENDC}\n| Overall Cluster CPU usage: {bc.GREEN}{round(sum(cpu_sum), 2)}{bc.ENDC}\n| Overall Cluster Memory usage: {bc.GREEN}{sum(mem_sum)}Mi{bc.ENDC}')
            print(t.get_string(sortby="CPU", reversesort=True))
        except Exception as e:
            print(f'{bc.RED}ERROR:{bc.ENDC} {e}')