#!/bin/bash
set -e

# 检查环境变量的函数
check_env_var() {
    var_value=$1
    if [[ -z "${var_value}" ]]; then
        echo "错误: 必须设置 ${var_value} 环境变量"
        exit 1
    fi
}

check_env_var "COMPILE" 
check_env_var "TCMALLOC" 
check_env_var "ASAN" 
check_env_var "TARGET" 
check_env_var "VERSION_ID" 
check_env_var "BRANCH" 
check_env_var "RUN_PATH"
check_env_var "MAKE_NUM"

version_id=${VERSION_ID}
compile=${COMPILE}
tcmalloc_stat=${TCMALLOC}
asan_stat=${ASAN}
target=${TARGET}
branch=${BRANCH}
run_path=${RUN_PATH}
MAKE_NUM=${MAKE_NUM}


if [[ $target == "config" || $target == "serveronly" ]]; then
    echo "target config or serveronly not need compile gamelib"
    exit 0
fi

echo "编译lib库：asan:"${asan_stat}

prefix="${run_path}/ro_${branch}"

echo "准备编译configlib"
configlib_path=${prefix}/rogamelibs/table/buildtool

if [ -f $configlib_path/build_linux.sh ]; then
    echo "准备编译configlib"
    cd ${configlib_path} && ./build_linux.sh
    if (( $? != 0 )); then
        echo "编译configlib出错"
        exit 55
    fi
    echo "编译configlib结束"
fi
######################## configlib编译结束

echo "准备编译gamelib"
gamelib_path=${prefix}/rogamelibs/buildtool

if [[ ! -d ${gamelib_path} ]]; then
    echo "编译gamelib路径 ${gamelib_path} 不存在"
    exit 55
fi
cd ${gamelib_path}

build_path="build_linux"
if [[ $compile == "Release" ]]; then
    build_path="build_linux_release"
fi
if [[ ! -d $build_path ]]; then
    mkdir $build_path
fi
if [[ -d ${build_path} ]]; then
    cd $build_path
    pwd
    rm -rf CMakeCache.txt CMakeFiles cmake_install.cmake Makefile
fi

if [[ $compile == "Release" ]]; then
    cd ..
    if [[ ! -f build_linux_release.sh ]]; then
        echo "编译gamelib出错,找不到脚本 build_linux_release.sh"
        exit 55
    fi
    ./build_linux_release.sh
    if [[ $? -ne 0 ]] ; then
        echo "./build_linux_release.sh 执行失败"
        exit 1
    fi
else
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
    compiler_flag="-DDevelop=On"
    cmake -DCMAKE_TOOLCHAIN_FILE=../cmake/LINUX.cmake -DCMAKE_BUILD_TYPE=Debug -DASAN=${asan_stat} -DCMAKE_C_COMPILER=$icc_path/${lan_cc} -DCMAKE_CXX_COMPILER=$icc_path/${lan_cxx} $compiler_flag ../..
    make -j${MAKE_NUM}
fi

if  [[ $? == 0 ]]; then
    echo "编译gamelib成功"
else
    echo "编译gamelib失败,请在测试群里@服务器值班同学"
    exit 55
fi

    
    