#!/bin/bash 
set -ex

# 设置变量的默认值以提高容错性
RUN_PATH=${RUN_PATH:-"/default/path"}
TARGET="${TARGET}"
namespace="${NAMESPACE}"
# 编译节点数
cloud_worker_num=${CLOUD_WORKER_NUM:-"10"}
chart_repo=${chart_repo:-"cloud-cmpile"}
chart_branch=${chart_branch:-"master"}
chart_name=${chart_name:-"ro-server"}
helm_release=${helm_release:-"server"}
timeout=${timeout:-600}  # 超时时间5分钟

if [ "${TARGET}" == "config" ]; then
  echo "配置包不需要编译环境,跳过..."
  exit 0
fi

# 拉取 Helm Chart 仓库
cd "$WORK_DIR"
if [ ! -d "${chart_repo}" ]; then
    git clone -b "${chart_branch}" git@git-intra.123u.com:sa/${chart_repo}.git
fi
cd ${chart_repo}

# k8s API
chmod 400 "${CODOvke_ro_server_builder}"
export KUBECONFIG="${CODOvke_ro_server_builder}"
kubectl config use-context "xxxxxxx"

# 初始化编译环境，检查命名空间是否存在
if ! kubectl get namespace "$namespace" > /dev/null 2>&1; then
    echo "命名空间 $namespace 不存在，正在创建."
    kubectl create ns "$namespace"
else 
    echo "命名空间 $namespace 已存在."
fi

# 安装或升级 Helm release
echo "安装 Helm release: $helm_release worker.replicas=${cloud_worker_num}"
helm upgrade --install -n "$namespace" "$helm_release" "$chart_name" -f "${chart_name}/values.yaml" --set worker.replicas=${cloud_worker_num}

# 检查 Pod 状态，设定超时
start_time=$(date +%s)
while true; do
    kubectl get pods -n "$namespace"
    pod_status=$(kubectl get pods -n "$namespace" -o jsonpath='{.items[*].status.phase}')
    if echo "$pod_status" | grep -q "ERROR"; then
        echo "pod初始化运行失败" && exit 1
    elif echo "$pod_status" | grep -q "Failed"; then
        echo "pod初始化失败" && exit 1
    elif echo "$pod_status" | grep -q "CrashLoopBackOff"; then
        echo "Pod不断崩溃重启" && exit 1
    elif echo "$pod_status" | grep -q "Pending"; then
        echo "等待资源分配...." 
    elif echo "$pod_status" | grep -q "ContainerCreating"; then
        echo "pod正在创建中...." 
    else
        echo "初始化完成"
        break
    fi

    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    if (( elapsed_time > timeout )); then
        echo "Pod 启动超时 ($timeout 秒)."
        exit 1
    fi
    sleep 10  # 间隔检查
done
