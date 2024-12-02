## 基于Yadcc联合编译的基础镜像制作

>  对于大型 C++ 项目，如何提高构建速度，当前我们使用腾讯开源的Yadcc方案
>
> https://github.com/Tencent/yadcc

### 镜像分别拥有三个类型服务

1. client
2. scheduler
3. worker

容器启动时，通过环境变量PROCESS_TARGET=client来决定启动哪个类型服务

https://github.com/Tencent/yadcc


