#!/bin/env python3
# coding=utf-8
import logging
import sys
import os
import commands
import threading
import traceback
import time


GIT_CLONE_STATUS = True
GIT_REPO_MAP = {
    "roserver": os.getenv("GIT_REPO_ROSERVER"),
    "config": os.getenv("GIT_REPO_CONFIG"),
    "gamelibs": os.getenv("GIT_REPO_CONFIG")
}

P4_USER = ""
P4_PASSWD = ""
P4_HOST_PORT = "10.0.0.1:1666"
P4_REPO_MAP = {
    "config": "//RO/Main/config/..."
}
NOT_CONIG_LIST = ["server", "diysvr"]
log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


class P4:
    def __init__(self, user=P4_USER, passwd=P4_PASSWD, host_port=P4_HOST_PORT):
        self.user = user
        self.passwd = passwd
        self.host_port = host_port
        self.login()

    def login(self):
        cmd = ("login", "<", self.passwd)
        return self.run_p4_cmd(cmd)

    def clone(self, *args, **kwargs):
        return self.run_p4_cmd(args, **kwargs)

    def log(self, repo, *args, **kwargs):
        cmd = ("changes", repo) + args
        return self.run_p4_cmd(cmd, **kwargs)

    def run_p4_cmd(self, args, **kwargs):
        runcmd = ("p4", "-u", self.user, "-p", self.host_port) + args
        return run_cmd(runcmd, **kwargs)

    def clone_depth(self, repo, dir, **kwargs):
        return self.clone("-d", dir, "clone", "-f", repo, **kwargs)


class Git:

    def __init__(self, private_key=None):
        self.private_key = private_key

    def clone(self, *args, **kwargs):
        cmd = ("git", "clone") + args
        return self.run_git_cmd(cmd, **kwargs)

    def pull(self, *args, **kwargs):
        try_num = 4
        cmd = ("git", "pull") + args
        for i in range(1, try_num):
            status, output = self.run_git_cmd(cmd, fail_is_exit=False, **kwargs)
            if status == 0:
                return status, output
            elif i < (try_num - 1):
                logging.warning("pull仓库失败：%s, 继续重试，第%s次 " % (output, i))
            elif i == (try_num - 1):
                msg = "pull仓库失败：%s, 已重试%s次" % (output, i)
                logging.error(msg)
                raise Exception(msg)
            time.sleep(3*i)
        return 
    
    def log(self, *args, **kwargs):
        cmd = ("git", "log") + args
        return self.run_git_cmd(cmd, **kwargs)

    def reset(self, *args, **kwargs):
        cmd = ("git", "reset") + args
        return self.run_git_cmd(cmd, **kwargs)

    def switch(self, *args, **kwargs):
        cmd = ("git", "switch") + args
        return self.run_git_cmd(cmd, **kwargs)

    def clean(self, *args, **kwargs):
        cmd = ("git", "clean") + args
        return self.run_git_cmd(cmd, **kwargs)
    
    def run_git_cmd(self, git_cmd, fail_is_exit=True, **kwargs):
        if self.private_key:
            agent_header = "ssh-agent sh -c 'ssh-add {private_key} && {git_cmd}' "
            git_cmd = agent_header.format(private_key=self.private_key, git_cmd=" ".join(git_cmd))
        return run_cmd(git_cmd, fail_is_exit, **kwargs)

    def clone_depth(self, git_url, branch, **kwargs):
        return self.clone("-b", branch, "--depth", "1", git_url, **kwargs)

    def get_log(self, **kwargs):
        return self.log('--pretty="%h - %s (%ci) <%aN> %d"', "-5", **kwargs)


def run_cmd(cmd, fail_is_exit=True):
    """
    执行shell命令
    :param cmd: 命令 ,类型支持字符、列表、元祖
    :param fail_is_exit: 失败是否强制退出
    :return: 命令输出
    """
    if type(cmd) is tuple or type(cmd) is list:
        cmd = " ".join(cmd)
    logging.info("commands: {}".format(cmd))
    status, output = commands.getstatusoutput(cmd)
    if status != 0 and fail_is_exit:
        logging.error(output)
        raise Exception(output)
    logging.info("output: %s" % output)

    return status, output


def run_clone_job(git, repo, branch, fail_is_exit=True):
    try_num = 4
    for i in range(1, try_num):
        status, output = git.clone_depth(repo, branch, fail_is_exit=False)
        if status == 0:
            return
        elif status != 0 and i < (try_num - 1):
            logging.warning("克隆代码%s仓库失败：%s, 继续重试，第%s次 " % (repo, output, i))
        elif status != 0 and fail_is_exit and i == (try_num - 1):
            global GIT_CLONE_STATUS
            GIT_CLONE_STATUS = False
            logging.error("克隆代码%s仓库失败：%s, 已重试%s次" % (repo, output, i))
        time.sleep(3*i)
    return


def create_branch_dir(git, prefix, branch, prefix_roserver, branch_type, p4=None):
    """
    创建并拉取相关代码仓库的代码
    :param git: git对象
    :param prefix: 自定义的项目目录
    :param branch: 代码分支
    :return: None
    """
    os.makedirs(prefix)
    os.chdir(prefix)
    t_list = list()

    for _branch, repo in GIT_REPO_MAP.items():
        if p4 and _branch == "config":
            logging.info("使用P4拉取config分支")
            t = threading.Thread(target=run_clone_job, args=(p4, P4_REPO_MAP["config"], _branch,))
        else:
            # 当打包类型是config时，允许gamelibs分支不存在
            fail_is_exit = True
            if branch_type == "config" and _branch in ["gamelibs", "roserver"]:
                fail_is_exit = False
            # 打包类型是自选服或server时，允许拉取config分支不存在
            if branch_type in NOT_CONIG_LIST and _branch == "config":
                fail_is_exit = False
            t = threading.Thread(target=run_clone_job, args=(git, repo, branch, fail_is_exit,))
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()

    # 如果拉取失败就删除当前创建的prefix目录
    if not GIT_CLONE_STATUS:
        run_cmd(["rm", "-rf", prefix])
        sys.exit(1)
    
    if os.path.exists(prefix_roserver):
        # 对roserver/config进行编译
        os.chdir(prefix_roserver)
        run_cmd(["sh", "create_cmake.sh", "%s/config" % prefix_roserver])

    return

def pull_config(git, branch, prefix_config):
    """
    更新本地config代码仓库
    :param git: git对象
    :param prefix_config: config的绝对路径
    :return: bool
    """
    if not os.path.exists(prefix_config):
        return False
    
    try:
        os.chdir(prefix_config)
        git.reset("--hard")
        git.clean("-df")
        git.switch(branch)
        git.pull("-r", "--depth", "2")
        logging.info("pull config代码 完成" )
    except:
        traceback.print_exc()
        return False
    return True


def reset_pull_config(git, prefix, prefix_config, branch, p4):
    """
    重置本地config代码仓库
    :param git: git对象
    :param prefix: 自定义的项目目录
    :param prefix_config: config的绝对路径
    :param branch: 分支
    :return: None
    """
    if not os.path.exists(prefix):
        os.makedirs(prefix)

    os.chdir(prefix)
    if prefix_config:
        run_cmd(["rm", "-rf", prefix_config])
    if p4:
        logging.info("使用P4拉取config分支")
        p4.clone_depth(P4_REPO_MAP["config"], "config")
        status, res = p4.log(repo=P4_REPO_MAP["config"])
        logging.info("更新config change: %s" % res)
    else:
        git.clone_depth(GIT_REPO_MAP["config"], branch)
        os.chdir(prefix_config)
        status, res = git.get_log()
        logging.info("更新config log: %s" % res)
    return


def update_server(git, branch, prefix_server_name):
    """
    还原到上一次提交rogamelibs、roserver 服务组件代码
    :param git: git对象
    :param prefix_server_name: 服务组件的绝对路径
    :return: 更新前日志，更新后日志
    """
    old_log, new_log = None, None
    if not os.path.exists(prefix_server_name):
        return old_log, new_log
    os.chdir(prefix_server_name)
    status, old_log = git.get_log()
    logging.info("更新前%s log: %s " % (prefix_server_name, old_log))
    git.reset("--hard")     # 彻底还原到上一次提交的状态
    git.clean("-df")
    git.switch(branch)
    git.pull("-r", "--depth", "4")
    status, new_log = git.get_log()
    logging.info("更新后%s log: %s " % (prefix_server_name, new_log))
    return old_log, new_log


def branch_handle(branch, git, p4, branch_type, run_path):
    """
    更新或创建本地相关服务组件的代码仓库
    :param bracnh: 分支名称
    :param git: git命令对象
    :param p4: p4命令对象
    :return: None
    """
    try:

        prefix = "%s/ro_%s" % (run_path, branch)
        prefix_config = "%s/config" % prefix
        prefix_rogamelibs = "%s/rogamelibs" % prefix
        prefix_roserver = "%s/roserver" % prefix
        prefix_roserver_debug_bin = "%s/Build/Debug/bin" % prefix_roserver
        prefix_roserver_release_bin = "%s/Build/Release/bin" % prefix_roserver

        if not os.path.exists(prefix):
            logging.info("代码分支文件：%s 不存在, 开始创建......" % prefix)
            create_branch_dir(git, prefix, branch, prefix_roserver, branch_type, p4)
        elif branch_type not in NOT_CONIG_LIST:

            status = pull_config(git, branch, prefix_config)
            if status is False:
                logging.info("2.删除重新拉取config分支")
                # 删除重新拉取config分支
                reset_pull_config(git, prefix, prefix_config, branch, p4)

        if branch == "games":
            os.chdir(prefix_config)
            return git.pull("origin", "develop_config", "-r", "--depth", "4")

        # 对rogamelibs进行还原到上一次提交，获取更新前和更新后的日志
        old_log, new_log = update_server(git, branch, prefix_rogamelibs)

        # roserver还原到上一次提交
        update_server(git, branch, prefix_roserver)

        # rogamelibs有更新lib文件，删除二进制文件
        if os.path.exists(prefix_rogamelibs):
            if old_log != new_log:
                logging.info("有更新到lib文件，删除二进制重新生成")
                if os.path.exists(prefix_roserver_debug_bin):
                    os.chdir(prefix_roserver_debug_bin)
                    run_cmd(["rm", "-rf", "*server"])
                if os.path.exists(prefix_roserver_release_bin):
                    os.chdir(prefix_roserver_release_bin)
                    run_cmd(["rm", "-rf", "*server"])
            else:
                logging.info("未更新到lib文件")
    except OSError as e:
        traceback.print_exc()
        logging.error("执行失败，请检查目录：%s" % e)
        sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        logging.error("执行失败, 错误：%s" % e)
        sys.exit(1)

    return


def get_params(param_list, index, defalut=None):
    return param_list[index] if len(param_list) >= (index + 1) else defalut


def main():
    param_branch = os.getenv("BRANCH")                         # 分支（如果是不同名分支，则为config分支）
    param_private_key_file = os.getenv("CODOro_server_gitlab")         # 拉取代码密钥文件
    param_target = os.getenv("TARGET")                                 # 拉取分支的方式（同名分支还是不同名分支）
    run_path = os.getenv("RUN_PATH")                                   # 执行路径
    param_is_p4 = "None"
    param_p4_passwd = "None"

    assert run_path, "RUN_PATH 不能为空"
    assert param_private_key_file, "CODOro_server_gitlab 不能为空"
    assert param_branch, "BRANCH 不能为空"
    assert param_target, "TARGET 不能为空"

    # 获取Git对象
    git = Git(param_private_key_file)
    # 获取P4对象
    p4 = P4(passwd=param_p4_passwd) if param_is_p4.lower() == "true" else None

    branch_handle(param_branch, git, p4, param_target, run_path)


if __name__ == '__main__':
    main()

