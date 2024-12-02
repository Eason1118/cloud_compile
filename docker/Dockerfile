# 基础镜像
FROM centos:7.9.2009

# 设置维护者信息
LABEL maintainer="louwenjun"

# 替换为国内镜像源
COPY Centos-7-ali.repo /etc/yum.repos.d/
RUN yum -y clean all && \
    yum -y makecache

# 更新系统并安装常用依赖包
RUN yum -y update && \
    yum -y groupinstall "Development Tools" && \
    yum -y install \
        wget \
        bzip2 \
        gcc \
        gcc-c++ \
        make \
        flex \
        bison \
        glibc-devel \
        texinfo \
        mariadb-server \
        mariadb \
        mariadb-devel \
        tar \
        net-tools \
        && yum clean all

# 设置环境变量
ENV LANG=C.UTF-8 \
    TZ=Asia/Shanghai \
    PATH=/usr/local/gcc-9.2.0/bin:/usr/local/go/bin:/opt/cmake-3.24.2-linux-x86_64/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/gcc-9.2.0/lib64:$LD_LIBRARY_PATH

# 下载 GCC 和依赖库并安装
WORKDIR /usr/local/src
RUN wget -q https://ftp.gnu.org/gnu/gcc/gcc-9.2.0/gcc-9.2.0.tar.gz && \
    wget -q https://gmplib.org/download/gmp/gmp-6.1.2.tar.bz2 && \
    wget -q https://www.mpfr.org/mpfr-4.0.2/mpfr-4.0.2.tar.bz2 && \
    wget -q https://ftp.gnu.org/gnu/mpc/mpc-1.1.0.tar.gz && \
    wget -q http://isl.gforge.inria.fr/isl-0.18.tar.bz2 && \
    tar -xvzf gcc-9.2.0.tar.gz && \
    tar -xvjf gmp-6.1.2.tar.bz2 && \
    tar -xvjf mpfr-4.0.2.tar.bz2 && \
    tar -xvzf mpc-1.1.0.tar.gz && \
    tar -xvjf isl-0.18.tar.bz2 && \
    mv gmp-6.1.2 gcc-9.2.0/gmp && \
    mv mpfr-4.0.2 gcc-9.2.0/mpfr && \
    mv mpc-1.1.0 gcc-9.2.0/mpc && \
    mv isl-0.18 gcc-9.2.0/isl && \
    mkdir gcc-build && cd gcc-build && \
    ../gcc-9.2.0/configure --prefix=/usr/local/gcc-9.2.0 --enable-languages=c,c++ --disable-multilib && \
    make -j$(nproc) && make install && \
    cd /usr/local/src && rm -rf gcc-9.2.0 gcc-build *.tar.*

# 下载并安装 Go
ARG GOLANG_VERSION=1.23.2
RUN wget -q https://golang.org/dl/go${GOLANG_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GOLANG_VERSION}.linux-amd64.tar.gz && \
    rm -f go${GOLANG_VERSION}.linux-amd64.tar.gz

# 下载并安装 CMake
ARG CMAKE_VERSION=3.24.2
RUN wget -q https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz && \
    tar -zxvf cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz -C /opt && \
    rm cmake-${CMAKE_VERSION}-linux-x86_64.tar.gz

# 解压和配置Yadcc
ADD yadcc.tar.gz /usr/local/

# 创建必要的软链接
RUN ln -sf /usr/local/gcc-9.2.0/bin/gcc /usr/local/bin/gcc && \
    ln -sf /usr/local/gcc-9.2.0/bin/g++ /usr/local/bin/g++

# 安装指定版本的 Python
ARG PYTHON_VERSION=3.6.8
RUN wget -q https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar -xvf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && make altinstall && \
    cd .. && rm -rf Python-${PYTHON_VERSION}*

# 设置默认 Python 和 pip 命令
RUN ln -sf /usr/local/bin/python3.6 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.6 /usr/bin/pip3

# 拷贝启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 设置默认工作目录
WORKDIR /

# 启动命令
CMD ["/start.sh"]

