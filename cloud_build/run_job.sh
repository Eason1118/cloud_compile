#! /bin/bash 
set -ex

TARGET="${TARGET}"
namespace="${NAMESPACE}"
chart_repo=${chart_repo:-"cloud-cmpile"}
chart_name=${chart_name:-"ro-server"}
helm_release=${helm_release:-"server"}
client_pod_name="${helm_release}-client"
timeout=${timeout:-600}  # 超时时间10分钟
# 编译节点数
cloud_worker_num=${CLOUD_WORKER_NUM:-"10"}
# make任务数
MAKE_NUM=${MAKE_NUM:-"128"}
# 定义Job名称
JOB_NAME="jobs/${client_pod_name}"
NAS_SERVER=${NFS_SERVER}

if [ "${TARGET}" == "config" ]; then
  echo "配置包不需要编译环境,跳过..."
  exit 0
fi

cd $WORK_DIR/${chart_repo}

# 生成 values.yaml 文件
env_file="${chart_name}/client_env.yaml"
cat <<EOF > ${env_file}
worker:
  replicas: ${cloud_worker_num}
client:
  running: True
  nfs:
    host: "${NAS_SERVER}"
  env:
    - name: BRANCH
      value: "${BRANCH}"
    - name: BINARY_NAME
      value: "${BINARY_NAME}"
    - name: VERSION_ID
      value: "${FLOW_ID}"
    - name: COMPILE
      value: "${COMPILE}"
    - name: TCMALLOC
      value: "${TCMALLOC}"
    - name: ASAN
      value: "${ASAN}"
    - name: TARGET
      value: "${TARGET}"
    - name: LOCATION
      value: "${LOCATION}"
    - name: RUN_PATH
      value: "${RUN_PATH}"
    - name: DIYSER_BACKUP_PATH
      value: "${DIYSER_BACKUP_PATH}"
    - name: SCRIPTS_PATH
      value: "${WORK_DIR}/${GLOBAL_SCRIPTS_PATH}"
    - name: MAKE_NUM
      value: ${MAKE_NUM}
EOF

function check_job_status() {

  # 检查 Pod 状态是否符合预期
  start_time=$(date +%s)
  while true; do
    sleep 10
    kubectl get pods -n "$namespace"
    STATUS=$(kubectl get job "${client_pod_name}" -n "$namespace" -o jsonpath='{.status}')
    # 提取相关状态信息
    READY=$(echo "$STATUS" | jq '.ready // 0')
    FAILED=$(echo "$STATUS" | jq '.failed // 0')
    ACTIVE=$(echo "$STATUS" | jq '.active // 0')

    # 判断状态
    if [[ "$READY" -gt 0 ]]; then
      echo "任务正在运行中..."
      break
    elif [[ "$FAILED" -gt 0 ]]; then
      echo "任务失败，请检查 Job 日志。"
      exit 1
    elif [[ "$ACTIVE" -eq 0 && "$READY" -eq 0 ]]; then
      echo "任务未运行，可能尚未启动或调度失败。"
      kubectl get job "${client_pod_name}" -n "$namespace"
    else 
      echo "等待任务运行..."
    fi

    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    if (( elapsed_time > timeout )); then
        echo "Pod 启动超时 ($timeout 秒)."
        exit 1
    fi
  done

  # pod正常运行，开始获取日志信息
  kubectl -n "$namespace" get job
  kubectl -n "$namespace" logs -f "$JOB_NAME" 
  echo "========LOG=END========"
  kubectl -n "$namespace" get pod
  sleep 10

  # 获取Job的succeeded状态
  RET_STATUS=$(kubectl get job "${client_pod_name}" -n "$namespace" -o jsonpath='{.status}')
  # 提取相关状态信息
  FAILED=$(echo "$RET_STATUS" | jq '.failed // 0')
  # 判断状态
  if [[ "$FAILED" -gt 0 ]]; then
    echo "任务失败，请检查 Job 日志。"
    exit 1
  else
    echo "任务已成功完成。"
  fi
}

# k8s API
chmod 400 "${CODOvke_ro_server_builder}"
export KUBECONFIG="${CODOvke_ro_server_builder}"
kubectl config use-context "ccrkfr5c9s3ub33bt6nu0@19460168-kcrki5v0qrrkk94f1iprg"

if ! kubectl get namespace "$namespace" > /dev/null 2>&1; then
  echo "命名空间 $namespace 不存在 ..."
  exit 1
fi

# 如果已存在job先删除
if kubectl -n "$namespace" get ${JOB_NAME} > /dev/null 2>&1; then
  kubectl -n "$namespace" delete ${JOB_NAME}
fi

# 安装或升级 Helm release
helm upgrade --install -n "$namespace" "$helm_release" "$chart_name" -f "${chart_name}/values.yaml" -f "${env_file}"

check_job_status 

