#!/bin/python3
from main.colors import bc
from main.api import kube_api
from prettytable import PrettyTable
import re

class node:

    def __init__(self, node):
        self.node = node

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
            print(f"* {bc.BOLD}Listing pods on node:  {bc.CYAN}{self.node}{bc.ENDC}")
            field_selector = f'spec.nodeName={self.node},status.phase=Running'
            pod = kube_api.clnt.list_pod_for_all_namespaces(watch=False, field_selector=field_selector)
            node_i = kube_api.clnt.read_node(name=self.node)
            node_usage = kube_api.clnt_c.get_cluster_custom_object(group="metrics.k8s.io", version="v1beta1", plural="nodes", name=self.node)
            n_cpu_a = node_i.status.allocatable.get("cpu")
            n_mem_a = int(re.split("(\d+)", node_i.status.allocatable.get("memory"))[1])//1024
            n_cpu_u = round(int(re.split("(\d+)", node_usage["usage"]["cpu"])[1])/1000000000, 3)
            n_mem_u = int(re.split("(\d+)", node_usage["usage"]["memory"])[1])//1024
            pc_cpu = round((float(n_cpu_u)/float(n_cpu_a))*100)
            pc_mem = round((n_mem_u/n_mem_a)*100)
            cpu_rl = []
            mem_rl = []
            t = PrettyTable(['Namespace', 'Pod', 'CPU', 'CPU req', 'CPU lim', 'Memory', 'Memory req', 'Memory lim'])
            for i in pod.items:
                if i.status.container_statuses[0].ready == True :
                    usage = kube_api.clnt_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
                    cpu_u = round(int(re.split("(\d+)", usage["containers"][0]["usage"]["cpu"])[1])/1000000000, 3)
                    mem_u = int(re.split("(\d+)", usage["containers"][0]["usage"]["memory"])[1])//1024
                    if i.spec.containers[0].resources.limits != None and i.spec.containers[0].resources.requests != None :
                        cpu_l = i.spec.containers[0].resources.limits.get("cpu")
                        cpu_r = i.spec.containers[0].resources.requests.get("cpu")
                        cpu_rl.append(cpu_r)
                        mem_l = i.spec.containers[0].resources.limits.get("memory")
                        mem_r = i.spec.containers[0].resources.requests.get("memory")
                        mem_rl.append(mem_r)
                        if mem_l == None :
                            t.add_row([i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_r}', f'{cpu_l}', f'{mem_u}Mi', f'{mem_r}', f'{bc.YELLOW}{mem_l}{bc.ENDC}'])
                        elif cpu_l == None:
                            t.add_row([i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_r}', f'{bc.YELLOW}{cpu_l}{bc.ENDC}', f'{mem_u}Mi', f'{mem_r}', f'{mem_l}'])
                        else:
                            t.add_row([i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{cpu_r}', f'{cpu_l}', f'{mem_u}Mi', f'{mem_r}', f'{mem_l}'])
                    else:
                        t.add_row([i.metadata.namespace, i.metadata.name, f'{cpu_u}', f'{bc.RED}None{bc.ENDC}', f'{bc.RED}None{bc.ENDC}', f'{mem_u}Mi', f'{bc.RED}None{bc.ENDC}', f'{bc.RED}None{bc.ENDC}'])
            cpu_tr = self.list_sum(cpu_rl)
            mem_tr = self.list_sum(mem_rl)
            pc_cpu_r = round((float(cpu_tr)/float(n_cpu_a))*100)
            pc_mem_r = round((mem_tr/n_mem_a)*100)
            print(f'| Overall node CPU usage: {bc.GREEN}{n_cpu_u}/{n_cpu_a} ({pc_cpu}%){bc.ENDC}\n| Total CPU Requests: {bc.YELLOW}{cpu_tr}/{n_cpu_a} ({pc_cpu_r}%){bc.ENDC}\n| Overall node Memory usage: {bc.GREEN}{n_mem_u}Mi/{n_mem_a}Mi ({pc_mem}%){bc.ENDC}\n| Total Memory Requests: {bc.YELLOW}{mem_tr}Mi/{n_mem_a}Mi ({pc_mem_r}%){bc.ENDC}')
            print(t.get_string(sortby="CPU", reversesort=True))
        except Exception as e:
            print(f'{bc.RED}ERROR:{bc.ENDC} {e}')