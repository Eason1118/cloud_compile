#!/bin/bash

# 日志路径
LOG_DIR="/var/log/process_manager"
mkdir -p $LOG_DIR

# 定义进程配置
declare -A PROCESSES

case "$PROCESS_TARGET" in
    client)
        mkdir -p $NFS_PATH && mount -t nfs $NFS_ARGS $NFS_HOST $NFS_PATH|$LOG_DIR/mountd.stdout.log|$LOG_DIR/mountd.stderr.log
        PROCESSES["yadcc-daemon"]="/usr/local/yadcc/yadcc-daemon --scheduler_uri flare://$YADCC_SCHEDULER_ADDR --token=$YADCC_TOKEN --max_remote_tasks=$YADCC_MAX_REMOTE_TASKS|$LOG_DIR/yadcc-daemon.stdout.log|$LOG_DIR/yadcc-daemon.stderr.log"
    ;;
    scheduler)
        PROCESSES["yadcc-scheduler"]="/usr/local/yadcc/yadcc-scheduler  --acceptable_user_tokens=$YADCC_TOKEN --acceptable_servant_tokens=$YADCC_SERVANT_TOKEN --inspect_credential=roo:yadcc|$LOG_DIR/yadcc-scheduler.stdout.log|$LOG_DIR/yadcc-scheduler.stderr.log"
    ;;
    worker)
        PROCESSES["yadcc-daemon"]="/usr/local/yadcc/yadcc-daemon --scheduler_uri flare://$YADCC_SCHEDULER_ADDR --token=$YADCC_TOKEN --max_remote_tasks=$YADCC_MAX_REMOTE_TASKS|$LOG_DIR/yadcc-daemon.stdout.log|$LOG_DIR/yadcc-daemon.stderr.log"
    ;;
    *)
        echo "Usage: $0 {client|scheduler|worker}"
    ;;
esac

# 监控进程函数
monitor_process() {
    local name=$1
    local command=$2
    local stdout_log=$3
    local stderr_log=$4

    echo "[$(date)] Starting process '$name'..." >> $LOG_DIR/manager.log

    while true; do
        # 检查进程是否已经运行
        if ! pgrep -f "$command" > /dev/null; then
            echo "[$(date)] Process '$name' not running. Restarting..." >> $LOG_DIR/manager.log
            nohup bash -c "$command" >> "$stdout_log" 2>> "$stderr_log" &
            sleep 2  # 等待进程启动
        fi
        sleep 5  # 定时检查进程状态
    done
}

# 启动所有配置的进程
for name in "${!PROCESSES[@]}"; do
    IFS="|" read -r command stdout_log stderr_log <<< "${PROCESSES[$name]}"
    monitor_process "$name" "$command" "$stdout_log" "$stderr_log" &
done

# 等待所有后台任务完成（模拟前台运行）
wait

