# Cloud Compile

**云编译** 是基于 Kubernetes (k8s) 的弹性伸缩能力，旨在提高大型业务计算资源的利用率和业务扩展性的大型 C++ 联合编译解决方案。

## 项目背景

在大型 C++ 项目中，编译时间往往较长，且需要大量计算资源。传统的编译方式可能导致资源利用率不高，且扩展性受限。**云编译** 通过利用 k8s 的弹性伸缩特性，动态分配和回收计算资源，提高编译效率和资源利用率。

## 特性

- **弹性伸缩**：根据编译任务的需求，动态调整计算资源，避免资源浪费。
- **高效利用**：充分利用 k8s 的调度能力，提高计算资源的使用效率。
- **易于集成**：可与现有的 CI/CD 流水线无缝集成，提升开发效率。

## 目录结构

- `cloud_build/`：云编译的核心实现代码。
- `docker/`：Docker 镜像构建文件。
- `global_build/`：全局编译配置文件。
- `helm_chart/`：Helm 部署模板。
- `pipeline.sh`：示例 CI/CD 流水线脚本。

## 快速开始

1. **克隆项目**

   ```bash
   git clone https://github.com/Eason1118/cloud_compile.git
   cd cloud_compile
   ```

2. **构建 Docker 镜像**

   ```bash
   docker build -t cloud_compile:latest -f docker/Dockerfile .
   ```

3. **部署到 Kubernetes 集群**

   使用 Helm 部署：

   ```bash
   helm install cloud-compile ./helm_chart
   ```

4. **触发编译任务**

   通过执行 `pipeline.sh` 脚本，触发云编译任务：

   ```bash
   ./pipeline.sh
   ```

## 贡献指南

欢迎对本项目提出问题、功能请求或提交拉取请求。请确保在提交代码前，阅读并遵循项目的贡献指南。

## 许可证

本项目采用 [GPL-3.0](LICENSE) 许可证。
