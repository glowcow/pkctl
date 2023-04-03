#!/usr/bin/env python3

from main.colors import bc
from main.api import KubeApi
from prettytable import PrettyTable
import re, sys

class Node:

    def __init__(self, node, sort):
        self.node = node
        self.sort = "CPU" if sort == "CPU" else "Mem(Mi)"
        self.k8s = KubeApi()
        self.k_client = self.k8s.kube_client_core()
        self.k_client_c = self.k8s.kube_client_cobj()

    def list_sum(self, lst): #summary various metrics
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

    def res_comp1(self, nodes, f_selector): #compute resource for each nodes with pods
        n_cpu_a_l = []
        n_mem_a_l = []
        n_cpu_u_l = []
        n_mem_u_l = []

        for a in nodes:
            node_i = self.k_client.read_node(name=a)
            n_cpu_a_ = node_i.status.allocatable.get("cpu")
            n_cpu_a_l.append(n_cpu_a_)
            n_mem_a_ = node_i.status.allocatable.get("memory")
            n_mem_a_l.append(n_mem_a_)

        cpu_rl = [] #CPU request list
        mem_rl = [] #Memory request list
        err_pods = []

        pods = self.k_client.list_pod_for_all_namespaces(watch=False, field_selector=f_selector)
        print(f"* {bc.BOLD}Listing usage resources on node:  {bc.CYAN}{self.node}{bc.ENDC}")
        t = PrettyTable(['Namespace', 'Pod', 'CPU', 'CPU req', 'CPU lim', 'Mem(Mi)', 'Mem req', 'Mem lim'])

        for i in pods.items:
            if i.status.container_statuses[0].ready == True :
                try:
                    usage = self.k_client_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
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

    def res_comp2(self, nodes): #compute resource cluster wide
        t_pods_l = []
        t_err_pods_l = []
        t_ncpu_a_l = []
        t_ncpu_u_l = []
        t_ncpu_r_l = []
        t_nmem_a_l = []
        t_nmem_u_l = []
        t_nmem_r_l = []

        print(f"* {bc.BOLD}Kubernetes cluster brief resources usage")
        t = PrettyTable(['Node', 'Pods', 'Err Pods', 'CPU', 'CPU usg', 'CPU req', 'Mem', 'Mem usg', 'Mem req'])

        for a in nodes:
            n_cpu_u_l = [] # node usage memory list
            n_mem_u_l = [] # node usage memory list
            cpu_rl = [] # CPU request list
            mem_rl = [] # Memory request list
            err_pods = [] # Pods in error state list

            node_i = self.k_client.read_node(name=a)
            n_cpu_a_ = node_i.status.allocatable.get("cpu")
            n_mem_a_ = node_i.status.allocatable.get("memory")

            f_selector = f'spec.nodeName={a},status.phase=Running'
            pods = self.k_client.list_pod_for_all_namespaces(watch=False, field_selector=f_selector)
            t_pods_l.append(len(pods.items))

            for i in pods.items:
                if i.status.container_statuses[0].ready == True :
                    try:
                        usage = self.k_client_c.get_namespaced_custom_object(group="metrics.k8s.io",version="v1beta1", namespace=i.metadata.namespace, plural="pods", name=i.metadata.name)
                    except Exception as e:
                        #print(f'{bc.RED}ERROR:{bc.ENDC} {e}')
                        err_pods.append(i.metadata.name)
                        continue
                    cpu_u = round(int(re.split("(\d+)", usage["containers"][0]["usage"]["cpu"])[1])/1000000000, 3)
                    n_cpu_u_l.append(cpu_u)
                    mem_u = int(re.split("(\d+)", usage["containers"][0]["usage"]["memory"])[1])//1024
                    n_mem_u_l.append(mem_u)
                    if i.spec.containers[0].resources.requests != None :
                        cpu_r = i.spec.containers[0].resources.requests.get("cpu")
                        if cpu_r != None :
                            cpu_rl.append(cpu_r)
                        mem_r = i.spec.containers[0].resources.requests.get("memory")
                        if mem_r != None :
                            mem_rl.append(mem_r)

            n_cpu_u = round(self.list_sum(n_cpu_u_l), 2)
            n_mem_u = self.list_sum(n_mem_u_l)
            n_mem_a = round(int(n_mem_a_.split('Ki')[0])/1024)
            cpu_tnr = round(self.list_sum(cpu_rl), 2) #CPU total node request
            mem_tnr = self.list_sum(mem_rl) #Memory total node request
            pc_cpu_r = round((float(cpu_tnr)/float(n_cpu_a_))*100)
            pc_mem_r = round((mem_tnr/n_mem_a)*100)
            pc_cpu = round((float(n_cpu_u)/float(n_cpu_a_))*100)
            pc_mem = round((n_mem_u/n_mem_a)*100)
            t.add_row([a, len(pods.items), len(err_pods), n_cpu_a_, f'{n_cpu_u} ({pc_cpu}%)', f'{cpu_tnr} ({pc_cpu_r}%)', f'{n_mem_a}Mi', f'{n_mem_u}Mi ({pc_mem}%)', f'{mem_tnr}Mi ({pc_mem_r}%)'])

            t_err_pods_l.append(len(err_pods))
            t_ncpu_a_l.append(n_cpu_a_)
            t_ncpu_u_l.append(n_cpu_u)
            t_ncpu_r_l.append(cpu_tnr)
            t_nmem_a_l.append(n_mem_a)
            t_nmem_u_l.append(n_mem_u)
            t_nmem_r_l.append(mem_tnr)

        t_pods = self.list_sum(t_pods_l)
        t_err_pods = self.list_sum(t_err_pods_l)
        n_cpu_a = self.list_sum(t_ncpu_a_l)
        n_mem_a = round(self.list_sum(t_nmem_a_l))
        n_cpu_u = round(self.list_sum(t_ncpu_u_l), 2)
        n_mem_u = self.list_sum(t_nmem_u_l)
        pc_cpu = round((float(n_cpu_u)/float(n_cpu_a))*100)
        pc_mem = round((n_mem_u/n_mem_a)*100)
        cpu_tr = round(self.list_sum(t_ncpu_r_l), 2) #CPU total request
        mem_tr = self.list_sum(t_nmem_r_l) #Memory total request
        pc_cpu_r = round((float(cpu_tr)/float(n_cpu_a))*100)
        pc_mem_r = round((mem_tr/n_mem_a)*100)

        print(f'| Overall running pods count: {bc.GREEN}{t_pods}{bc.ENDC} (Err: {bc.RED}{t_err_pods}{bc.ENDC})\n| Overall CPU usage: {bc.GREEN}{n_cpu_u}/{n_cpu_a} ({pc_cpu}%){bc.ENDC}\n| Total CPU Requests: {bc.YELLOW}{cpu_tr}/{n_cpu_a} ({pc_cpu_r}%){bc.ENDC}\n| Overall Memory usage: {bc.GREEN}{n_mem_u}Mi/{n_mem_a}Mi ({pc_mem}%){bc.ENDC}\n| Total Memory Requests: {bc.YELLOW}{mem_tr}Mi/{n_mem_a}Mi ({pc_mem_r}%){bc.ENDC}')
        print(t.get_string())

    def resources(self):
        try:
            if self.node == "all" :
                f_selector = f'status.phase=Running'
                node_list = self.k_client.list_node()
                nodes = []
                for a in node_list.items:
                    n = a.metadata.name
                    nodes.append(n)
                self.res_comp1(nodes, f_selector)
            elif self.node == "brief" :
                node_list = self.k_client.list_node()
                nodes = []
                for a in node_list.items:
                    n = a.metadata.name
                    nodes.append(n)
                self.res_comp2(nodes)
            else:
                f_selector = f'spec.nodeName={self.node},status.phase=Running'
                nodes = [self.node]
                self.res_comp1(nodes, f_selector)

        except Exception as e:
            sys.stderr.write(f'ERROR[node]: {e}')
