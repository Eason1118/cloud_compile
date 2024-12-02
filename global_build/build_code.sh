#!/bin/bash
set -ex

# 检查环境变量的函数
check_env_var() {
    var_value=$1
    if [[ -z "${var_value}" ]]; then
        echo "错误: 必须设置 ${var_value} 环境变量"
        exit 1
    fi
}

check_env_var "BRANCH" 
check_env_var "COMPILE" 
check_env_var "TCMALLOC" 
check_env_var "ASAN" 
check_env_var "BINARY_NAME" 
check_env_var "TARGET" 
check_env_var "VERSION_ID" 
check_env_var "LOCATION" 
check_env_var "DIYSER_BACKUP_PATH"
check_env_var "RUN_PATH"
check_env_var "MAKE_NUM"

branch=${BRANCH}
compile=${COMPILE}
tcmalloc_stat=${TCMALLOC}
asan_stat=${ASAN}
binary_name=${BINARY_NAME}
target=${TARGET}
version_id=${VERSION_ID}
location=${LOCATION}
diysvr_backup_path=${DIYSER_BACKUP_PATH}
run_path=${RUN_PATH}
MAKE_NUM=${MAKE_NUM}

if [[ $target == "config" || $target == "serveronly" ]]; then
    echo "target config or serveronly not need compile code"
    exit 0
fi

echo binarygame=${binary_name}
echo "compile:${compile}"

if [ ${asan_stat} == "On" ] && [ ${tcmalloc_stat} == "On" ]; then
    echo "不能同时打开ASAN和TCMALLOC"
    exit 55
fi

# 安全检测开关；针对非欢乐管理的地区服务器包都关闭
if [ "${location}" == "korea" ] || [ "${location}" == "japan" ] || [ "${location}" == "northamerica" ] || [ "${location}" == "rocn" ]; then
  echo "安全检测开关--关闭"
  prevent_leak_stat=0
else
  echo "安全检测开关--开启"
  prevent_leak_stat=1
fi


echo 编译roserser, asan:${asan_stat}, tcmalloc:${tcmalloc_stat}

prefix="${run_path}/ro_${branch}"

compile_start_tick=$(date +%s)
echo "编译开始: $(date '+%Y-%m-%d %T')"

cd ${prefix}/roserver
if [ -f create_cmake.sh ]; then
    echo "开始--编译HttpServer"
    bash create_cmake.sh
    cd "Build/${compile}/"
    go env -w GO111MODULE='auto'
    bash build_go_http.sh 
    echo "结束--编译HttpServer"
else
    echo "所需create_cmake.sh文件不存在"
fi

cd ${prefix}/roserver/Build/${compile}/
rm -fr CMakeCache.txt CMakeFiles cmake_install.cmake Makefile share protocol *tool *server dbg_bin || true
icc_path="/usr/local/bin"
lan_cc=gcc
lan_cxx=g++
if [[ -d /usr/local/yadcc ]]; then
    icc_path=/usr/local/yadcc
    if [[ ! -z $(command -v clang++) ]] && (( $(grep -c USE_CLANG ../../CMakeLists.txt) > 0 )); then
        lan_cc=clang
        lan_cxx=clang++
    fi
fi
cmake -DCMAKE_BUILD_TYPE=${compile} -DGCC=9.2.0 -DGCOV=Off -DASAN=${asan_stat} -DLSAN=Off -DUSE_UNITY_BUILD=On \
      -DUSE_TCMALLOC=${tcmalloc_stat} -DVERSION_ID=${version_id} -DUSE_PREVENT_LEAK=${prevent_leak_stat} \
      -DCMAKE_C_COMPILER=$icc_path/${lan_cc} -DCMAKE_CXX_COMPILER=$icc_path/${lan_cxx} ../.. 

if [[ ${branch} == "release1.7.0" ]]; then
    make -j${MAKE_NUM} protolib
    cd ../../lib
    ln -snf ../../rogamelibs/buildtool/Server/lib/librogamelibs.a .
    ln -snf ../../rogamelibs/table/buildtool/Server/lib/libconfiglib.a .
    cd ${prefix}/roserver/Build/${compile}/
fi


function make_binary() {
    # 支持指定二进制编译
    local make_jobs=${1}
    if [ "${binary_name}" == "All" ]; then
        echo "开始编译所有二进制"
        make ${make_jobs}
        binary_list=$(ls bin | grep -E "server|combinetool"  | grep -v ".sh")
        binary_array=($binary_list)
    else
        # 使用jq将JSON数组转换为 shell 数组
        binary_array=($(echo ${binary_name} | tr ',' '\n'))
        for binary in "${binary_array[@]}"; do
            echo "====开始编译二进制：${binary}"
            [ ! -d $binary ] && echo "编译失败：$binary 目录不存在" && exit 1
            cd "$binary" 
            make ${make_jobs}
            cd ..
        done
    fi
}

make_binary -j${MAKE_NUM}

echo "===binary_array:${binary_array}"

if [ $? -ne 0 ]; then
    echo "编译出错"
    exit 233
fi

compile_end_tick=$(date +%s)
compile_interval=$((compile_end_tick - compile_start_tick))
echo
echo "编译结束: $(date '+%Y-%m-%d %T')"
echo "server 编译共花费时间:${compile_interval}秒"
    
