#!/bin/python3
from main.colors import bc
from main.api import kube_api
from prettytable import PrettyTable
import re, sys

class node:

    def __init__(self, argv):
        if len(argv) == 3:
            self.node = argv[2]
            self.sort = "CPU"
        elif len(argv) == 4:
            self.node = argv[2]
            if argv[3] == "mu" :
                self.sort = "Mem(Mi)"
            else:
                raise NameError(f'Unknown PyKubeCtl sort mode: {argv[3]}')

    def list_sum(self, lst):
        _list = []
        cpu_list = []
        mem_list = []
        for a in lst:
            if isinstance(a, float) :
                _list.append(a)
            elif isinstance(a, int) :
                _list.append(a)
            elif a.isnumeric():
                d = int(a)
                cpu_list.append(d)
            elif re.findall('m', a):
                cpu_list.append(int(a.split('m')[0])/1000)
            elif re.findall('Gi', a):
                mem_list.append(int(a.split('Gi')[0])*1024)
            elif re.findall('Mi', a):
                mem_list.append(int(a.split('Mi')[0]))
            elif re.findall('Ki', a):
                mem_list.append(int(a.split('Ki')[0])/1024)
        if len(cpu_list) != 0 :
            out = sum(cpu_list)
        elif len(mem_list) != 0 :
            out = sum(mem_list)
        elif len(_list) != 0 :
            out = sum(_list)
        return out

    def resources(self):
        try:
            if self.node == "all" :
                f_selector = f'status.phase=Running'
                node_list = kube_api.clnt.list_node()
                nodes = []
                for a in node_list.items:
                    n = a.metadata.name
                    nodes.append(n)
            else:
                f_selector = f'spec.nodeName={self.node},status.phase=Running'
                nodes = [self.node]
            n_cpu_a_l = []
            n_mem_a_l = []
            n_cpu_u_l = []
            n_mem_u_l = []
            for b in nodes:
                node_i = kube_api.clnt.read_node(name=b)
                n_cpu_a_ = node_i.status.allocatable.get("cpu")
                n_cpu_a_l.append(n_cpu_a_)
                n_mem_a_ = node_i.status.allocatable.get("memory")
                n_mem_a_l.append(n_mem_a_)
            cpu_rl = [] #CPU request list
            mem_rl = [] #Memory request list
            err_pods = []
            print(f"* {bc.BOLD}Listing usage resources on node:  {bc.CYAN}{self.node}{bc.ENDC}")
            t = PrettyTable(['Namespace', 'Pod', 'CPU', 'CPU_req', 'CPU_lim', 'Mem(Mi)', 'Mem_req', 'Mem_lim'])
            pods = kube_api.clnt.list_pod_for_all_namespaces(watch=False, field_selector=f_selector)
            for i in pods.items:
                if i.status.container_statuses[0].ready == True :
                    try:
                        usage = kube_api.clnt_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
                    except Exception as e:
                        #print(f'{bc.RED}ERROR:{bc.ENDC} {e}')
                        err_pods.append(i.metadata.name)
                        continue
                    cpu_u = round(int(re.split("(\d+)", usage["containers"][0]["usage"]["cpu"])[1])/1000000000, 3)
                    n_cpu_u_l.append(cpu_u)
                    mem_u = int(re.split("(\d+)", usage["containers"][0]["usage"]["memory"])[1])//1024
                    n_mem_u_l.append(mem_u)
                    if i.spec.containers[0].resources.limits != None and i.spec.containers[0].resources.requests != None :
                        cpu_l = i.spec.containers[0].resources.limits.get("cpu")
                        cpu_r = i.spec.containers[0].resources.requests.get("cpu")
                        cpu_rl.append(cpu_r)
                        mem_l = i.spec.containers[0].resources.limits.get("memory")
                        mem_r = i.spec.containers[0].resources.requests.get("memory")
                        mem_rl.append(mem_r)
                        if mem_l == None :
                            t.add_row([i.metadata.namespace, i.metadata.name, cpu_u, f'{cpu_r}', f'{cpu_l}', mem_u, f'{mem_r}', f'{bc.YELLOW}{mem_l}{bc.ENDC}'])
                        elif cpu_l == None:
                            t.add_row([i.metadata.namespace, i.metadata.name, cpu_u, f'{cpu_r}', f'{bc.YELLOW}{cpu_l}{bc.ENDC}', mem_u, f'{mem_r}', f'{mem_l}'])
                        else:
                            t.add_row([i.metadata.namespace, i.metadata.name, cpu_u, f'{cpu_r}', f'{cpu_l}', mem_u, f'{mem_r}', f'{mem_l}'])
                    else:
                        t.add_row([i.metadata.namespace, i.metadata.name, cpu_u, f'{bc.RED}None{bc.ENDC}', f'{bc.RED}None{bc.ENDC}', mem_u, f'{bc.RED}None{bc.ENDC}', f'{bc.RED}None{bc.ENDC}'])
            n_cpu_a = self.list_sum(n_cpu_a_l)
            n_mem_a = round(self.list_sum(n_mem_a_l))
            n_cpu_u = round(self.list_sum(n_cpu_u_l), 2)
            n_mem_u = self.list_sum(n_mem_u_l)
            pc_cpu = round((float(n_cpu_u)/float(n_cpu_a))*100)
            pc_mem = round((n_mem_u/n_mem_a)*100)
            cpu_tr = round(self.list_sum(cpu_rl), 2) #CPU total request
            mem_tr = self.list_sum(mem_rl) #Memory total request
            pc_cpu_r = round((float(cpu_tr)/float(n_cpu_a))*100)
            pc_mem_r = round((mem_tr/n_mem_a)*100)
            print(f'| Overall running pods count: {bc.GREEN}{len(pods.items)}{bc.ENDC} (Err: {bc.RED}{len(err_pods)}{bc.ENDC})\n| Overall CPU usage: {bc.GREEN}{n_cpu_u}/{n_cpu_a} ({pc_cpu}%){bc.ENDC}\n| Total CPU Requests: {bc.YELLOW}{cpu_tr}/{n_cpu_a} ({pc_cpu_r}%){bc.ENDC}\n| Overall Memory usage: {bc.GREEN}{n_mem_u}Mi/{n_mem_a}Mi ({pc_mem}%){bc.ENDC}\n| Total Memory Requests: {bc.YELLOW}{mem_tr}Mi/{n_mem_a}Mi ({pc_mem_r}%){bc.ENDC}')
            print(t.get_string(sortby=self.sort, reversesort=True))
        except Exception as e:
            sys.stderr.write(f'ERROR[node]: {e}')
