#!/usr/bin/env python3

from kubernetes import client, config

class KubeApi:

    def __init__(self):
        config.load_kube_config()

    def kube_client_core(self):
        kube_client = client.CoreV1Api()
        return kube_client

    def kube_client_cobj(self):
        kube_client = client.CustomObjectsApi()
        return kube_client

    def kube_client_apic(self):
        kube_client = client.ApiClient()
        return kube_client
