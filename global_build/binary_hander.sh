#!/bin/bash
# desc: 二进制处理，包含符号表拆分和二进制备份、上传自选服存包机
set -e

# 日志函数
log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# 检查环境变量
check_env_var() {
    local var_name=$1
    if [[ -z "${!var_name}" ]]; then
        log_error "环境变量未设置: ${var_name}"
        exit 1
    fi
}

# 初始化必要环境变量
initialize_env_vars() {
    local required_vars=("BRANCH" "COMPILE" "TARGET" "DIYSER_BACKUP_PATH" "RUN_PATH" "BINARY_NAME" "IS_BACKUP" \
    "RSYNC_DEV_SERVER" "RSYNC_DEV_USER" "RSYNC_DEV_KEY" "RSYNC_DEV_MODULE")
    for var in "${required_vars[@]}"; do
        check_env_var "$var"
    done

    branch=${BRANCH}
    binary_name=${BINARY_NAME}
    compile=${COMPILE}
    target=${TARGET}
    diysvr_backup_path=${DIYSER_BACKUP_PATH}
    run_path=${RUN_PATH}
    backup_flag=${IS_BACKUP}
    rsync_dev_key=${CODOro_sync_diysvr_ropkg}
    prefix="${run_path}/ro_${branch}"

    rsync_server=${RSYNC_DEV_SERVER}
    rsync_user=${RSYNC_DEV_USER}
    rsync_key=${RSYNC_DEV_KEY}
    rsync_module=${RSYNC_DEV_MODULE}
    binary_array=()
}

# 解析二进制文件列表
parse_binary_list() {
    cd "${prefix}/roserver/Build/${compile}/"
    if [[ "${binary_name}" == "All" ]]; then
        binary_array=($(ls bin | grep -E "server|combinetool" | grep -v ".sh"))
    else
        binary_array=($(echo "${binary_name}" | tr ',' '\n'))
    fi
}

# 创建目录
create_dir_if_not_exists() {
    local dir=$1
    if [[ ! -d "${dir}" ]]; then
        mkdir -p "${dir}"
    fi
}

# 备份二进制文件
backup_binaries() {
    local backup_dir="${diysvr_backup_path}/${branch}"
    local dbg_bin_dir="dbg_bin"

    create_dir_if_not_exists "${backup_dir}"
    create_dir_if_not_exists "${dbg_bin_dir}"

    log_info "开始备份二进制文件..."
    local bak_start=$(date +%s)
    for svr in "${binary_array[@]}"; do
        if [[ "${target}" == "diysvr" ]]; then
            local src_file="bin/${svr}"
            local dest_file="${backup_dir}/${svr}"
            if [[ -f "${dest_file}" && $(md5sum "${dest_file}" | awk '{print $1}') == $(md5sum "${src_file}" | awk '{print $1}') ]]; then
                log_info "${svr} 无需拷贝，文件未变更。"
                continue
            fi
            log_info "拷贝: ${svr}"
            cp -vf "${src_file}" "${dest_file}" &
        else
            log_info "拆分符号表: ${svr}"
            objcopy --only-keep-debug "bin/${svr}" "${dbg_bin_dir}/${svr}.dbg" &
            objcopy --strip-debug "bin/${svr}" "${dbg_bin_dir}/${svr}" &
        fi
    done
    echo "等待二进制处理任务....."
    wait
    echo "二进制处理任务完成....."

    backup_config_files "${backup_dir}"
    generate_compile_log "${backup_dir}"
    local bak_end=$(date +%s)
    log_info "二进制备份完成，耗时: $((bak_end - bak_start)) 秒"
}

# 备份配置文件
backup_config_files() {
    local backup_dir=$1
    local gsconf_dir="${backup_dir}/gsconf"
    create_dir_if_not_exists "${gsconf_dir}"

    if [[  -d ${prefix}/rogamelibs/script ]]; then
        if [[ ! -d ${backup_dir}/gsconf/lua_gamelibs ]]; then
            mkdir -p ${backup_dir}/gsconf/lua_gamelibs
        fi
        cp -a ${prefix}/rogamelibs/script/* ${backup_dir}/gsconf/lua_gamelibs/ &
    else
        if [[  -d ${backup_dir}/gsconf/lua_gamelibs ]]; then
            rm -fr ${backup_dir}/gsconf/lua_gamelibs
        fi
    fi
    if [[ ${compile} == "Release" ]]; then
        cp ${prefix}/roserver/lib/RelWithDebInfo/*.so ${backup_dir} &
    elif [[ ${compile} == "Debug" ]]; then
        cp ${prefix}/roserver/lib/Debug/*.so ${backup_dir} &
    fi
    cp -a ${prefix}/roserver/exe/gsconf/script/ ${backup_dir}/gsconf/ &
    cp -a ${prefix}/roserver/exe/gsconf/serveronly/ ${backup_dir}/gsconf/ &
    cp -a ${prefix}/roserver/exe/audioconf/ ${backup_dir} &
    cp -a ${prefix}/roserver/exe/conf.template/ ${backup_dir} &
    cp -a ${prefix}/roserver/exe/gateconf/ ${backup_dir} &
    wait
}

# 生成编译日志
generate_compile_log() {
    local backup_dir=$1
    local log_file="${backup_dir}/compileserver"
    echo "二进制编译时间: $(date '+%Y-%m-%d %T')" > "${log_file}"
    echo "二进制编译节点 rogamelibs:" >> "${log_file}"
    (cd "${prefix}/rogamelibs/" && git log -1) >> "${log_file}"
    echo "二进制编译节点 roserver:" >> "${log_file}"
    git log -1 >> "${log_file}"
}

# 同步到存包服务器
sync_to_backup_server() {
    local backup_dir="${diysvr_backup_path}/${branch}"
    if [[ "${target}" == "diysvr" && "${backup_flag}" == "1" ]]; then
        log_info "开始同步 ${backup_dir%*/} 到存包服务器..."

        rsync -vrtopg --progress --delete --password-file="${rsync_key}" "${backup_dir%*/}" ${rsync_user}@${rsync_server}::${rsync_module}
        if [[ $? -ne 0 ]]; then
            log_error "同步失败：${backup_dir%*/}"
        else
            log_info "同步成功，删除本地备份包..."
            rm -rf "${backup_dir%*/}" || log_error "删除本地目录失败：${backup_dir%*/}"
        fi
    else
        log_info "不同步条件，跳过同步。"
    fi
}

# 主流程
main() {
    initialize_env_vars
    parse_binary_list
    backup_binaries
    sync_to_backup_server
}

main
