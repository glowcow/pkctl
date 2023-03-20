#!/usr/bin/env python3

from kubernetes import client, config

class kube_api:
    config.load_kube_config()
    clnt = client.CoreV1Api()
    clnt_c = client.CustomObjectsApi()
