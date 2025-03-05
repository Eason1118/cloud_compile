#!/bin/bash 
set -ex
# TODO： 编译任务执行完，可以对资源进行回收

namespace="${NAMESPACE}"
# k8s API
chmod 400 "${CODOvke_ro_server_builder}"
export KUBECONFIG="${CODOvke_ro_server_builder}"
kubectl config use-context "xxxxxxx"

# 初始化编译环境，检查命名空间是否存在
if ! kubectl get namespace "$namespace" > /dev/null 2>&1; then
    echo "命名空间 $namespace 不存在"
else 
    echo "准备回收命名空间：$namespace 相关资源"
    kubectl -n $namespace get all
    echo "命名空间-开始清理"
    kubectl delete ns $namespace
    echo "清理完成"
fi
