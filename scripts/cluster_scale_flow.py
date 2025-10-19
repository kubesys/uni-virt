#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础云平台集群资源扩缩容程序（elastic 节点版）
默认启用轻量模式（Pod 0.1 核 CPU / 32Mi 内存），可通过参数关闭
节点前缀、IP前缀自定义
在 KeyboardInterrupt 时会清理 Pod 和节点
"""

import argparse
import sys
import time
import threading
import random
from datetime import datetime, timezone
from kubernetes import client, config
from kubernetes.client.rest import ApiException

stop_threads = False

# ---------- 辅助函数 ----------
def iso_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simulate_resource_usage(current_usage):
    """模拟资源占用率，带随机波动，更自然"""
    delta = random.randint(1, 6)
    current_usage += delta
    fluctuation = random.randint(-3, 3)
    current_usage += fluctuation
    current_usage = max(0, min(100, current_usage))
    return current_usage

# ---------- Pod/Node 操作 ----------
def create_elastic_node(core_v1, name, ip, cpu_capacity, mem_capacity):
    meta = client.V1ObjectMeta(name=name, labels={"elastic-node": "true"})
    node = client.V1Node(metadata=meta)
    try:
        core_v1.create_node(body=node)
        print(f"[{iso_now()}] 创建节点成功：{name}")
    except ApiException as e:
        if e.status == 409:
            print(f"[{iso_now()}] 节点 {name} 已存在，将更新状态")
        else:
            print(f"[{iso_now()}] 创建节点失败：{e}")
            raise
    now_rfc3339 = datetime.now(timezone.utc).isoformat()
    status = client.V1NodeStatus(
        capacity={"cpu": str(int(cpu_capacity)), "memory": str(mem_capacity)},
        allocatable={"cpu": str(int(cpu_capacity)), "memory": str(mem_capacity)},
        addresses=[
            client.V1NodeAddress(type="InternalIP", address=ip),
            client.V1NodeAddress(type="Hostname", address=name),
        ],
        conditions=[
            client.V1NodeCondition(
                type="Ready",
                status="True",
                reason="Elastic",
                message="节点已就绪",
                last_heartbeat_time=now_rfc3339,
                last_transition_time=now_rfc3339
            )
        ]
    )
    try:
        core_v1.patch_node_status(name=name, body=client.V1Node(status=status))
        print(f"[{iso_now()}] 节点 {name} 状态已更新（Ready + capacity）")
    except ApiException as e:
        print(f"[{iso_now()}] 警告：无法更新节点状态 {name}：{e}")

def maintain_node_heartbeat(core_v1, name, ip, cpu_capacity, mem_capacity, interval=10):
    while not stop_threads:
        try:
            now_rfc3339 = datetime.now(timezone.utc).isoformat()
            status = client.V1NodeStatus(
                capacity={"cpu": str(int(cpu_capacity)), "memory": str(mem_capacity)},
                allocatable={"cpu": str(int(cpu_capacity)), "memory": str(mem_capacity)},
                addresses=[
                    client.V1NodeAddress(type="InternalIP", address=ip),
                    client.V1NodeAddress(type="Hostname", address=name),
                ],
                conditions=[
                    client.V1NodeCondition(
                        type="Ready",
                        status="True",
                        reason="ElasticHeartbeat",
                        message="节点心跳",
                        last_heartbeat_time=now_rfc3339,
                        last_transition_time=now_rfc3339
                    )
                ]
            )
            core_v1.patch_node_status(name=name, body=client.V1Node(status=status))
        except ApiException as e:
            print(f"[{iso_now()}] 节点心跳更新失败 {name}：{e}")
        time.sleep(interval)

def delete_elastic_node(core_v1, name):
    try:
        core_v1.delete_node(name)
        print(f"[{iso_now()}] 删除节点成功：{name}")
    except ApiException as e:
        if e.status == 404:
            print(f"[{iso_now()}] 节点 {name} 不存在")
        else:
            print(f"[{iso_now()}] 删除节点失败 {name}：{e}")

def delete_pods(core_v1, pod_names, namespace):
    for name in pod_names:
        try:
            core_v1.delete_namespaced_pod(name=name, namespace=namespace, body=client.V1DeleteOptions())
            print(f"[{iso_now()}] 删除 Pod 成功：{name}")
        except ApiException as e:
            if e.status == 404:
                print(f"[{iso_now()}] Pod {name} 不存在")
            else:
                print(f"[{iso_now()}] 删除 Pod 失败 {name}：{e}")

# ---------- 主程序 ----------
def main():
    parser = argparse.ArgumentParser(description="基础云平台集群节点资源扩缩容程序")
    parser.add_argument("--num-pods", type=int, default=50, help="Pod 总数量")
    parser.add_argument("--namespace", type=str, default="default", help="命名空间")
    parser.add_argument("--pod-cpu", type=str, default="2", help="每个 Pod CPU")
    parser.add_argument("--pod-mem", type=str, default="2Gi", help="每个 Pod 内存")
    parser.add_argument("--group1-prefix", type=str, default="hongshan-ai-", help="第一组 Pod 前缀")
    parser.add_argument("--group2-prefix", type=str, default="hongshan-bq-", help="第二组 Pod 前缀")
    parser.add_argument("--group3-prefix", type=str, default="hongshan-fz-", help="第三组 Pod 前缀")
    parser.add_argument("--node-count", type=int, default=2, help="新增节点数量")
    parser.add_argument("--node-cpu", type=str, default="16", help="节点 CPU")
    parser.add_argument("--node-mem", type=str, default="32Gi", help="节点内存")
    parser.add_argument("--node-name-prefix", type=str, default="elastic-", help="节点名称前缀")
    parser.add_argument("--node-ip-prefix", type=str, default="10.10.10.", help="节点 IP 前缀")
    parser.add_argument("--image", type=str, default="registry.cn-hangzhou.aliyuncs.com/google-containers/busybox:latest", help="Pod 镜像")
    parser.add_argument("--duration", type=int, default=120, help="Pod 运行时长（秒）")
    parser.add_argument("--threshold", type=int, default=80, help="资源使用率阈值（百分比）")
    parser.add_argument("--disable-light-mode", action="store_true", help="关闭轻量模式")
    args = parser.parse_args()

    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    if not args.disable_light_mode:
        print(f"[{iso_now()}] 开启轻量模式，Pod 使用 0.1 核 CPU / 32Mi 内存")
        args.pod_cpu = "100m"
        args.pod_mem = "32Mi"

    created_pods = []
    node_names = []
    heartbeat_threads = []

    try:
        # ---------- 1. 创建 Pod 三组 ----------
        group_sizes = [args.num_pods // 3] * 3
        remainder = args.num_pods % 3
        for i in range(remainder):
            group_sizes[i] += 1

        group_prefixes = [args.group1_prefix, args.group2_prefix, args.group3_prefix]
        pod_index = 1

        for group_id, size in enumerate(group_sizes):
            prefix = group_prefixes[group_id]
            for i in range(size):
                pod_name = f"{prefix}{i+1}"
                pod = client.V1Pod(
                    metadata=client.V1ObjectMeta(name=pod_name, labels={"app": "elastic"}),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name="main",
                            image=args.image,
                            resources=client.V1ResourceRequirements(
                                requests={"cpu": args.pod_cpu, "memory": args.pod_mem},
                                limits={"cpu": args.pod_cpu, "memory": args.pod_mem},
                            ),
                            command=["/bin/sh"],
                            args=["-c", "sleep 3600"]
                        )],
                        restart_policy="Never"
                    )
                )
                try:
                    core_v1.create_namespaced_pod(namespace=args.namespace, body=pod)
                    created_pods.append(pod_name)
                    print(f"[{iso_now()}] 创建 Pod {pod_name}")
                except ApiException as e:
                    if e.status == 409:
                        print(f"[{iso_now()}] Pod {pod_name} 已存在，跳过创建")
                    else:
                        print(f"[{iso_now()}] 创建 Pod 失败 {pod_name}：{e}")
                pod_index += 1
                time.sleep(0.05)

        # ---------- 2. 模拟资源监测 ----------
        print(f"[{iso_now()}] 开始资源监测...")
        usage = 5
        while usage < args.threshold:
            usage = simulate_resource_usage(usage)
            print(f"[{iso_now()}] 当前资源使用率：{usage}%")
            time.sleep(1 + random.random())

        # ---------- 3. 扩容节点 ----------
        print(f"[{iso_now()}] 资源使用率超过 {args.threshold}%，触发集群扩容")
        for i in range(args.node_count):
            ip = args.node_ip_prefix + str(10 + i)
            name = f"{args.node_name_prefix}{i+1}"
            create_elastic_node(core_v1, name, ip, args.node_cpu, args.node_mem)
            node_names.append(name)
            t = threading.Thread(target=maintain_node_heartbeat, args=(core_v1, name, ip, args.node_cpu, args.node_mem, 10), daemon=True)
            t.start()
            heartbeat_threads.append(t)

        # ---------- 4. 模拟 Pod 运行 ----------
        print(f"[{iso_now()}] Pods 正在运行（持续 {args.duration} 秒）...")
        time.sleep(args.duration)

        # ---------- 5. 回收资源 ----------
        ans = input(f"[{iso_now()}] 是否回收资源？(yes/no): ").strip().lower()
        if ans == "yes":
            stop_threads = True
            delete_pods(core_v1, created_pods, args.namespace)
            for name in node_names:
                delete_elastic_node(core_v1, name)
            print(f"[{iso_now()}] 集群资源缩容完成")
        else:
            print(f"[{iso_now()}] 保留当前节点，程序退出")

    except KeyboardInterrupt:
        print(f"\n[{iso_now()}] 用户中断，正在清理资源...")
        stop_threads = True
        delete_pods(core_v1, created_pods, args.namespace)
        for name in node_names:
            delete_elastic_node(core_v1, name)
        print(f"[{iso_now()}] 集群资源缩容完成，程序退出")


if __name__ == "__main__":
    main()
