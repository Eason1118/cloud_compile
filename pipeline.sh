#! /bin/bash 
#set -x

# ==============global Parameter=================
# Job名称
STAGE=${1}
# 任务ID
FLOW_ID=${FLOW_ID}
# 分支名
branch_temp=${codo_branch:-develop}
commit_id=`echo $branch_temp |jq -r '.commit_id'`
BRANCH=`echo $branch_temp |jq -r '.ref_name'`
# 脚本分支
script_branch_temp=${codo_script_branch:-master}
script_commit_id=`echo $script_branch_temp |jq -r '.commit_id'`
SCRIPT_BRANCH=`echo $script_branch_temp |jq -r '.ref_name'`
if [ -z ${SCRIPT_BRANCH} ]; then
	SCRIPT_BRANCH=master
fi
# 指定包类型； ['all', 'server', 'config', 'init', 'diysvr']
TARGET=${codotarget-"all"}
# 语言地区
LOCATION=${codolocation-"inner"}
# 编译参数
COMPILE=${codocompile-"Release"}
# 编译参数
TCMALLOC=${codotcmalloc-"On"}
# 编译参数
ASAN=${codoasan-"Off"}
# 选择编译的二进制文件
BINARY_NAME=$(echo "$codobinary_name" | jq -r 'join(",")')
if [ -z ${BINARY_NAME} ]; then
	BINARY_NAME=All
fi
# 指定打包的config文件
CONFIG_SELECT=${codoconfig_select-"all"}
# GMT回调地址
CALLBACK=${codocallback-"None"}
# 是否触发自动更新；0：否； 1：是
IS_INSTALL=${codois_install-"0"}
# 是否备份到备份机；0：否； 1：是
IS_BACKUP=${codois_backup:-0}
# 地区
AREA=${codoarea-"None"}
# 平台
UPDATE_PLATFORMS=${codoupdate_platforms-"None"}
# 用户ID
USER_ID=${codouser_id-"None"}
# 任务的工作目录
DEPLOY_DIR="/cloud_data/worker_space/cloud_ci"
# 默认执行路径
RUN_PATH="/cloud_data/build_ro_server"
# 自选服二进制默认执行路径
DIYSER_BACKUP_PATH="/cloud_data/local_server"
# 仓库名
REPO="ro_builder"
# 云编译脚本目录
CLOUD_SCRIPTS_PATH="${REPO}/cloud_build"
# 全球编译脚本目录
GLOBAL_SCRIPTS_PATH="${REPO}/global_build"
# 集群命名空间
NAMESPACE="ro-ci-${FLOW_ID:-"default"}"

# ==============INIT=================
WORK_DIR=$DEPLOY_DIR/$FLOW_ID
[ -e ${WORK_DIR} ] || mkdir -p ${WORK_DIR}
cd ${WORK_DIR}

# ==============ENV=================
chmod 400 ${CODOops_gitlab} ${CODO_row_sync_diysvr_key} ${CODO_row_sync_key} ${CODOro_server_gitlab} ${CODOCMDB_API_KEY} ${CODOdevops_upload_token}

# 为了避免后续脚本无法读取环境变量
source ${CODOexport_gmt_api_cred}
export CODOro_server_gitlab=${CODOro_server_gitlab}
export CODOCMDB_API_KEY=${CODOCMDB_API_KEY} 
export CODOdevops_upload_token=${CODOdevops_upload_token} 
export CODOvke_ro_server_builder=${CODOvke_ro_server_builder}
export FL_PIPELINE_TASK_ID=${FL_PIPELINE_TASK_ID}
export BRANCH=${BRANCH}
export BINARY_NAME=${BINARY_NAME}
export VERSION_ID=${FLOW_ID}
export COMPILE=${COMPILE}
export TCMALLOC=${TCMALLOC}
export ASAN=${ASAN}
export TARGET=${TARGET}
export LOCATION=${LOCATION}
export RUN_PATH=${RUN_PATH}
export WORK_DIR=${WORK_DIR}
export IS_BACKUP=${IS_BACKUP}
export NAMESPACE=${NAMESPACE}
export CLOUD_WORKER_NUM=${codo_cloud_worker_num}
export DIYSER_BACKUP_PATH=${DIYSER_BACKUP_PATH}
export CONFIG_SELECT=${CONFIG_SELECT}
export GLOBAL_SCRIPTS_PATH=${GLOBAL_SCRIPTS_PATH}
export MAKE_NUM=${codo_make_num}
# 自选服存包机Rsync配置
source ${CODO_row_sync_diysvr_conf}
# 全量包存包机Rsync配置
source ${CODO_row_sync_conf}
export RSYNC_DEV_KEY=${CODO_row_sync_diysvr_key}
export RSYNC_KEY=${CODO_row_sync_key}
# 火山云NAS挂载
export NFS_SERVER="xxxx.nas.ivolces.com:/enas-xxxxx"
export GIT_REPO_ROSERVER="git@xxx"
export GIT_REPO_CONFIG="git@xxx"
export GIT_REPO_GAMELIBS="git@xxx"
export PROJECT="ROW"

# ==============RUN JOB=================
if [ "${STAGE}" == "init_script" ]; then
  echo "===Start ${STAGE}==="
  ssh-agent sh -c "ssh-add ${CODOops_gitlab} && git clone git@xxx:sa/${REPO}.git  -b ${SCRIPT_BRANCH} && cd ${REPO} && git log -5 --oneline"

elif [ "${STAGE}" == "pull_code" ]; then
  echo "===Start ${STAGE}=== ${BRANCH} ${CODOro_server_gitlab} None None ${TARGET}"
  cd ${WORK_DIR}/${GLOBAL_SCRIPTS_PATH} && python2 git_pull.py 

elif [ "${STAGE}" == "init_job" ]; then
	export GIT_SSH_COMMAND="ssh -i $CODOops_gitlab -p 52000 -o StrictHostKeyChecking=no"
  cd ${WORK_DIR}/${CLOUD_SCRIPTS_PATH} && sh init_job.sh 
  
elif [ "${STAGE}" == "run_job" ]; then
  cd ${WORK_DIR}/${CLOUD_SCRIPTS_PATH} && sh run_job.sh 

elif [ "${STAGE}" == "binary_hander" ]; then
  echo "===Start ${STAGE}=== ${BRANCH} ${COMPILE} ${TCMALLOC} ${ASAN} ${TARGET}"
  cd ${WORK_DIR}/${GLOBAL_SCRIPTS_PATH} && sh binary_hander.sh

elif [ "${STAGE}" == "sync_pkg" ]; then
  echo "===Start ${STAGE}==="
  cd ${WORK_DIR}/${GLOBAL_SCRIPTS_PATH}
  python2 tar_file.py 
  
elif [ "${STAGE}" == "del_env" ]; then
  echo "===Start ${STAGE}==="
  cd ${WORK_DIR}/${CLOUD_SCRIPTS_PATH} && sh del_env.sh 
  [ -d ${WORK_DIR} ] && rm -rf ${WORK_DIR}
else
  echo "Error STAGE: ${STAGE} "
  exit 1
fi



# ==============判断结果是否正常=================
if [ $? -eq 0 ]; then
    echo "===Succeed ${STAGE}==="
else
    echo "===Fail ${STAGE}==="
    exit 1
fi



