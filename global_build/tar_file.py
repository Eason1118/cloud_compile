#!/bin/env python3
# coding=utf-8
import logging
import sys
import os
import random
import shutil
import requests
import json

try:
    import commands
except ImportError:
    import subprocess as commands
import time
import traceback
from datetime import datetime
reload(sys)
sys.setdefaultencoding("utf-8")

log_format = '%(asctime)s|%(levelname)s|%(message)s'
logging.basicConfig(format=log_format, datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

SERVERS_LIST = ["dbserver", "controlserver", "audioserver", "idipserver", "authserver", "gateserver", "masterserver",
                "gameserver", "tradeserver", "battleserver", "loginserver", "rankserver", "payserver", "fmserver",
                "matchserver", "middleserver", "dbproxyserver", "routerserver", "combinetool", "chatserver",
                "watchproxyserver", "httpserver"]
# flow订单触发任务
FLOW_CREATE_URL = "https://tianmen.huanle.com/api/job/v1/flow/accept/create/"

def get_env_file_connext(env_path):
    connext = None
    if env_path and os.path.exists(env_path):
        with open(env_path, "r") as f:
            connext = f.read().strip()
    return connext


# 行云Token
XY_TOKEN = get_env_file_connext(env_path=os.getenv("CODOdevops_upload_token"))
# 行云任务ID
XY_TASK_ID = os.getenv("FL_PIPELINE_TASK_ID")
# tianmen api key
CODO_API_KEY = get_env_file_connext(env_path=os.getenv("CODOCMDB_API_KEY"))



def human_datetime(date=None, strf_time=None):
    """转换时间格式到字符串"""
    if date:
        assert isinstance(date, datetime)
    else:
        date = datetime.now()
    if strf_time:
        return date.strftime(strf_time)
    return date.strftime('%Y-%m-%d %H:%M:%S')


def run_cmd(cmd, fail_is_exit=False):
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
        raise Exception(output)
    elif output:
        logging.info("output: %s" % output)
    return status, output


def copy_server(tmp_dir, prefix, servers_list, compile, target, pwd_path):
    # 复制二进制文件到缓存目录
    for ser in servers_list:
        server_path = "{prefix}/roserver/Build/{compile}/dbg_bin/{server}".format(prefix=prefix, compile=compile,
                                                                                  server=ser)
        if os.path.exists(server_path):
            tmp_server_path = "%s/%s" % (tmp_dir, ser)
            os.makedirs(tmp_server_path)
            copy(server_path, tmp_server_path)
        else:
            logging.warning("not find server : %s" % server_path)
    
    # init包 需要copy gcc .so文件
    if target in ("init", "all"):
        glb_lib_pkg_path = "%s/glb_lib_pkg" % pwd_path
        if os.path.exists(glb_lib_pkg_path):
            glb_lib_pkg_path = "%s/*" % glb_lib_pkg_path
            tmp_lib_path = "%s/gcc_lib" % tmp_dir
            os.makedirs(tmp_lib_path)
            copy(glb_lib_pkg_path, tmp_lib_path)

    return


def copy_conf_temp(tmp_dir, prefix):
    # copy配置模板到缓存目录
    server_template_config = "%s/conf.template" % tmp_dir
    logging.info("src: %s , dest: %s" % ("%s/roserver/exe/conf.template" % prefix, server_template_config))
    copy("%s/roserver/exe/conf.template" % prefix, server_template_config)
    return


def get_params(param_list, index, defalut=None):
    return param_list[index] if len(param_list) >= (index + 1) else defalut


def copy(src, dest):
    return run_cmd("cp -rf %s %s" % (src, dest), fail_is_exit=True)


def copy_config(tmp_dir, prefix, location, config_select, init=None):
    # 如果same_files中的key 与all_files相同，则覆盖all_files配置，否则默认all_files
    all_files, same_files = dict(), dict()
    if init is True:
        all_files["serveronly"] = "/roserver/exe/gsconf/serveronly"

    overseas_config_lua_game = None
    all_files["curve"] = "/config/Assets/Editor/EditorResources/Server/Curve"
    all_files["lua_script"] = "/config/LuaGame"
    all_files["lua_server"] = "/config/LuaServer"
    all_files["AI"] = "/config/Assets/Resources/AI"
    all_files["SkillData"] = "/config/Assets/Resources/SkillData"
    all_files["rogameslib_table"] = "/config/Table/ServerBytes"
    all_files["SceneGrid"] = "/config/Assets/Resources/SceneGrid"
    all_files["nav_datas"] = "/config/Assets/Resources/NavDatas"
    all_files["scene_unity_datas"] = "/config/Assets/Resources/ScenesUnityDatas"
    all_files["air_space_datas"] = "/config/Assets/Resources/AirSpaceDatas"
    all_files["distance_check_datas"] = "/config/Assets/Resources/ClyDatas"
    all_files["map_layer_datas"] = "/config/Assets/Resources/MlyDatas"
    all_files["terrian_datas"] = "/config/Assets/Resources/TerrainDatas"
    all_files["path_datas"] = "/config/Assets/Resources/PathDatas"
    all_files["script"] = "/roserver/exe/gsconf/script"
    all_files["WayPoint"] = "/config/Assets/Resources/WayPoint"
    all_files["scene_spawner"] = "/config/Assets/Resources/SceneDatas"
    all_files["Tlog"] = "/config/TLog"
    all_files["lua_resource"] = "/config/LuaResource"
    all_files["lua_gamelibs"] = "/rogamelibs/script"

    if location == "korea":
        same_files["rogameslib_table"] = "/config/overseas_config/Korea/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/Korea/Assets/Resources/PathDatas"
        same_files["scene_spawner"] = "/config/overseas_config/Korea/Assets/Resources/SceneDatas"
        same_files["SkillData"] = "/config/overseas_config/Korea/Assets/Resources/SkillData"
        overseas_config_lua_game = "%s/config/overseas_config/Korea/LuaGame" % prefix
    elif location == "japan":
        same_files["rogameslib_table"] = "/config/overseas_config/Japan/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/Japan/Assets/Resources/PathDatas"
        same_files["SkillData"] = "/config/overseas_config/Japan/Assets/Resources/SkillData"
        same_files["scene_spawner"] = "/config/overseas_config/Japan/Assets/Resources/SceneDatas"
        overseas_config_lua_game = "%s/config/overseas_config/Japan/LuaGame" % prefix

    elif location == "northamerica":
        same_files["rogameslib_table"] = "/config/overseas_config/NorthAmerica/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/NorthAmerica/Assets/Resources/PathDatas"
        same_files["SkillData"] = "/config/overseas_config/NorthAmerica/Assets/Resources/SkillData"
        same_files["scene_spawner"] = "/config/overseas_config/NorthAmerica/Assets/Resources/SceneDatas"
        overseas_config_lua_game = "%s/config/overseas_config/NorthAmerica/LuaGame" % prefix

    elif location == "hmt":
        same_files["rogameslib_table"] = "/config/overseas_config/HMT/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/HMT/Assets/Resources/PathDatas"
        same_files["SkillData"] = "/config/overseas_config/HMT/Assets/Resources/SkillData"
        same_files["scene_spawner"] = "/config/overseas_config/HMT/Assets/Resources/SceneDatas"
        overseas_config_lua_game = "%s/config/overseas_config/HMT/LuaGame" % prefix

    elif location == "sea":
        same_files["rogameslib_table"] = "/config/overseas_config/SEA/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/SEA/Assets/Resources/PathDatas"
        same_files["SkillData"] = "/config/overseas_config/SEA/Assets/Resources/SkillData"
        same_files["scene_spawner"] = "/config/overseas_config/SEA/Assets/Resources/SceneDatas"
        overseas_config_lua_game = "%s/config/overseas_config/SEA/LuaGame" % prefix

    elif location == "lna":
        same_files["rogameslib_table"] = "/config/overseas_config/LNA/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/LNA/Assets/Resources/PathDatas"
        same_files["SkillData"] = "/config/overseas_config/LNA/Assets/Resources/SkillData"
        same_files["scene_spawner"] = "/config/overseas_config/LNA/Assets/Resources/SceneDatas"
        overseas_config_lua_game = "%s/config/overseas_config/LNA/LuaGame" % prefix
    
    elif location == "rocn":
        all_files["serveronly"] = "/roserver/exe/gsconf/serveronly"
        all_files["lua_gamelibs"] = "/rogamelibs/script"
        same_files["rogameslib_table"] = "/config/overseas_config/CNLive/Table/ServerBytes"
        same_files["path_datas"] = "/config/overseas_config/CNLive/Assets/Resources/PathDatas"
        same_files["SkillData"] = "/config/overseas_config/CNLive/Assets/Resources/SkillData"
        same_files["scene_spawner"] = "/config/overseas_config/CNLive/Assets/Resources/SceneDatas"
        same_files["nav_datas"] = "/config/overseas_config/CNLive/Assets/Resources/NavDatas"
        overseas_config_lua_game = "%s/config/overseas_config/CNLive/LuaGame" % prefix

    tmp_gsconf = "%s/gsconf" % tmp_dir
    if not os.path.exists(tmp_gsconf):
        os.makedirs(tmp_gsconf)
    if config_select == "all":
        # 将对应地区的配置进行合并到最终配置文件中
        for conf_data_map in [all_files, same_files]:
            for conf_name, conf_path in conf_data_map.items():
                copy_path = "%s/%s" % (prefix, conf_path)
                dest_path = "%s/%s" % (tmp_gsconf, conf_name)
                if os.path.exists(copy_path):
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    copy(copy_path + "/*", dest_path)

        if overseas_config_lua_game and os.path.exists(overseas_config_lua_game):
            copy(overseas_config_lua_game + "/*", "%s/lua_script" % tmp_gsconf)

    elif config_select:
        logging.info("根据自定义选择的配置文件进行合并： %s" % config_select.split())
        for conf_name, conf_path in all_files.items():
            for conf in config_select.split():
                level_1_path = conf.split("/")[0]
                if conf_name == level_1_path and os.path.exists("%s/%s/%s" % (prefix, conf_path, conf)):
                    src = "%s/%s/%s" % (prefix, conf_path, conf)
                    dest = "%s/%s" % (tmp_gsconf, level_1_path)
                    copy(src, dest)
                    logging.info("合并自定义选择的配置文件，src：%s， dest：%s" % (src, dest))

    # 初始化需要的文件
    if init is True:
        init_conf_map = {
            "loginconf": "roserver/exe/loginconf",
            "audioconf": "roserver/exe/audioconf"
        }
        for conf_name, conf_path in init_conf_map.items():
            copy_path = "%s/%s" % (prefix, conf_path)
            dest_path = "%s/%s" % (tmp_dir, conf_name)
            if os.path.exists(copy_path):
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                copy(copy_path + "/*", dest_path)
        
    # loginconf
    tmp_loginconf = "%s/loginconf" % tmp_dir
    if not os.path.exists(tmp_loginconf):
        os.makedirs(tmp_loginconf)
    for item in [all_files, same_files]:
        if "rogameslib_table" not in item:
            continue
        copy_path = "%s/%s/%s" % (prefix, item["rogameslib_table"], "region.txt")
        dest_path = "%s/%s" % (tmp_loginconf, "rogameslib_table")
        dest_file = os.path.join(dest_path, "region.txt")
        # 失败重试机制
        for i in range(3):
            try:
                if os.path.exists(copy_path):
                    if not os.path.exists(dest_path):
                        os.makedirs(dest_path)
                    if os.path.exists(dest_file):
                        logging.info("====remove: %s" % dest_file)
                        os.remove(dest_file)

                    copy(copy_path, dest_path)
                    break
                else:
                    break
            except Exception as error:
                if i == 2:
                    raise Exception(error)
            time.sleep(1)

    return


def tar_file(branch, prefix, location, target, tmp_dir, tar_file_path, rsync_key, tmp_path, rsync_conf):
    """将合并好的二进制文件、配置文件 进行压缩成tar.gz，并传输到存包机中"""
    roserver = "%s/roserver" % prefix
    if os.path.exists(roserver):
        roserver_file_list = ["/start", "/stop", "/sql/create_sql", "/sql/update_sql", "/gateconf"]
        if target == "init":
            roserver_file_list += ["dbconf", "audioconf", "loginconf"]
        logging.info("将roserver的指定文件进行合并, %s" % roserver_file_list)
        for file_path in roserver_file_list:
            dir_name = os.path.dirname(file_path)
            dest_dir = "%s/%s" % (tmp_dir, dir_name)
            if dir_name != "/" and not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            src_path = "%s/exe/%s" % (roserver, file_path)
            dest_path = "%s/%s" % (tmp_dir, file_path)
            if file_path == "loginconf":
                login_rogslib_path = os.path.join(src_path, "rogameslib_table")
                if os.path.islink(login_rogslib_path):
                    os.unlink(login_rogslib_path)
                if os.path.exists(login_rogslib_path):
                    shutil.rmtree(login_rogslib_path)
            if os.path.exists(dest_path):
                src_path += "/*"
            copy(src_path, dest_path)

    logging.info("开始压缩")
    if not os.path.exists(tar_file_path):
        os.makedirs(tar_file_path)
    tar_file_name = "%s_%s_%s_%s.tar.gz" % (location, branch, target, human_datetime(strf_time="%Y%m%d%H%M%S"))
    tar_package_path = "%s/%s" % (tar_file_path, tar_file_name)
    os.chdir(tmp_path)
    tar_cmd = "tar --use-compress-program=pigz -cpf %s ro_game" % tar_package_path
    status, output = run_cmd(tar_cmd)
    if status != 0:
        raise Exception("tar file fail, cmd: %s ,out: %s" % (tar_cmd, output))
    logging.info("压缩完成")

    md5_cmd = "md5sum %s | awk '{print $1}'" % tar_package_path
    status, md5sum = run_cmd(md5_cmd)
    size = get_pkg_size(tar_package_path)

    rsync_cmd = "rsync -av --progress --password-file=%s %s  %s" % (
    rsync_key, tar_package_path, rsync_conf)
    status, output = run_cmd(rsync_cmd)


    if status == 0:
        logging.info("同步成功, 删除本地包:%s" % tar_package_path)
        run_cmd("rm -r %s" % tar_package_path)
    else:
        raise Exception("rsync fail")

    # 回调行云接口
    xy_callback(tar_file_name, md5sum, size, target)

    return md5sum, tar_file_name


def tar_dbg_server(tar_file_path, prefix, tar_file_name, compile, dbg_tmp_dir, servers_list, rsync_key, tmp_path, rsync_conf):
    # 打包符号文件
    dbg_file_name = "dbg_%s" % tar_file_name
    tar_package_path = "%s/%s" % (tar_file_path, dbg_file_name)
    # 复制二进制文件到缓存目录
    for ser in servers_list:
        server_path = "{prefix}/roserver/Build/{compile}/dbg_bin/{server}.dbg".format(prefix=prefix, compile=compile,
                                                                                      server=ser)
        if os.path.exists(server_path):
            tmp_server_path = "%s/%s" % (dbg_tmp_dir, ser)
            os.makedirs(tmp_server_path)
            copy(server_path, tmp_server_path)
        else:
            logging.warning("not find dbg server : %s" % server_path)

    os.chdir(tmp_path)
    tar_cmd = "tar --use-compress-program=pigz -cpf %s ro_dbg_bin" % tar_package_path
    status, output = run_cmd(tar_cmd)
    if status != 0:
        raise Exception("tar file fail, cmd: %s ,out: %s" % (tar_cmd, output))
    logging.info("压缩完成")

    rsync_cmd = "rsync -av --progress --password-file=%s %s  %s" % (
    rsync_key, tar_package_path, rsync_conf)
    status, output = run_cmd(rsync_cmd)
    if status == 0:
        logging.info("同步成功, 删除本地包:%s" % tar_package_path)
        run_cmd("rm -r %s" % tar_package_path)
    else:
        raise Exception("rsync fail")

    return dbg_file_name


def get_pkg_size(pkg):
    cmd = "ls -l %s | awk '{print $5}'" % pkg
    status, pkg_size = run_cmd(cmd)
    try:
        size = int(pkg_size)
    except:
        logging.error("获取包体大小失败: %s, %s" % (status, output))
        size = 0
    return size

def xy_callback(tarfile, md5, size, target):
    """回调行云接口"""
    try:
        print("###SOF###{output}###EOF###".format(output=json.dumps({
            "md5": md5,
            "server_pkg": tarfile,
            "dbg_server_pkg": "dbg_" + tarfile,
            "pkg_size": size,
            "target": target,
            "pipeline_task": XY_TASK_ID
        }, ensure_ascii=False)))

        if not XY_TOKEN or not XY_TASK_ID:
            logging.warning("为获取到token或task_id，无法回调行云制品库接口")
            return
        headers = {'Authorization': XY_TOKEN, 'Content-Type': 'application/json'}
        hostname = "https://devops.huanle.com"
        url = hostname + "/artifact/api/v1/artifact/create"
        data = {
            "name": tarfile,  # 文件名
            "source_type": 1,  # 资源类型，1 是CI流水线产生
            "size": size,  # 产物大小 字节(byte) 作为单位
            "outer": True,  # 是否外部产物
            "outer_url": tarfile,  # 如果是外部产物，填入这个外部产物的URL
            "ext": ".tar.gz",  # 文件后缀名
            "content_type": 2,  # 根据实际传，1-实际的文件，2-URL（外部产物）
            "project_id": 1,
            "source_id": XY_TASK_ID,
            "md5": md5  # 文件的 MD5 值
        }
        logging.info("请求数据：%s, Headers: %s" % (data, headers))
        ret = requests.post(url, headers=headers, data=json.dumps(data)).json()
        logging.info("创建包体属性；%s" % ret)
        art_id = ret["data"]["id"]
        url = hostname + "/artifact/api/v1/artifact/upload-finish"
        data = {
            'id': art_id,
            "project_id": 1
        }
        ret = requests.post(url, headers=headers, data=json.dumps(data)).json()
        logging.info("更新制品状态为完成：%s" % ret)

    except Exception as e:
        traceback.print_exc()
        logging.error("执行行云回调失败: %s" % e)
    return

def push_cos_callback(pkg):
    """触发上传COS异步任务"""

    try:
        headers = {"Sdk-Method": "zQtY4sw7sqYspVLrqV", "Cookie": "auth_key=%s" % CODO_API_KEY}
        params = {
            "ro_pkg": pkg
        }
        data = dict(
            flow_version_name="RO-Server东南亚包传输COS桶-运维项目",
            order_name="RO-Server东南亚包传输COS桶",
            global_params=json.dumps(params),
            creator="CI自动触发"
        )
        logging.info("触发上传COS异步任务参数:%s" % data)
    
        response = requests.post(url=FLOW_CREATE_URL, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            logging.error("回调失败:%s" % response.text)
        else:
            logging.info("回调成功: %s" % response.text)
    except:
        traceback.print_exc()
    return


def main():
    start_time = time.time()
    
    run_path = os.getenv("RUN_PATH")     # 执行路径                               
    branch = os.getenv("BRANCH")      # 分支
    target = os.getenv("TARGET")   # 打包类型
    compile = os.getenv("COMPILE")   # 编译参数
    location = os.getenv("LOCATION")  # 语言包地区
    config_select = os.getenv("CONFIG_SELECT")   # 指定打包的config文件
    binary_name = os.getenv("BINARY_NAME")  # 选择单个或多个服务进程编译
    rsync_server = os.getenv("RSYNC_SERVER")   # rsync server
    rsync_user = os.getenv("RSYNC_USER")   # rsync user
    rsync_key = os.getenv("RSYNC_KEY")   # rsync key
    rsync_module = os.getenv("RSYNC_MODULE")   # rsync module

    assert run_path, "RUN_PATH 不能为空"
    assert target, "TARGET 不能为空"
    assert branch, "BRANCH 不能为空"
    assert compile, "COMPILE 不能为空"
    assert location, "LOCATION 不能为空"
    assert config_select, "CONFIG_SELECT 不能为空"
    assert binary_name, "BINARY_NAME 不能为空"
    assert rsync_server, "RSYNC_SERVER 不能为空"
    assert rsync_user, "RSYNC_SERVER 不能为空"
    assert rsync_key, "RSYNC_KEY 不能为空"
    assert rsync_module, "RSYNC_MODULE 不能为空"

    if target == "diysvr":
        logging.info("自选服不需要打tar包")
        return
    
    rsync_conf = "%s@%s::%s" % (rsync_user, rsync_server, rsync_module)
    tar_file_path = "%s/tarfile" % run_path
    prefix = "%s/ro_%s" % (run_path, branch)
    file_name = human_datetime(strf_time="%Y-%m-%d_%H%M%S") + str(random.randint(100, 999))
    tmp_path = "/data/tmp_tarfile/%s" % file_name
    tmp_dir = "%s/ro_game" % tmp_path
    dbg_tmp_dir = "%s/ro_dbg_bin" % tmp_path

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    if not os.path.exists(dbg_tmp_dir):
        os.makedirs(dbg_tmp_dir)
    run_status = True
    try:
        if binary_name != "All" and binary_name:
            servers_list = binary_name.split(",")
        else:
            servers_list = SERVERS_LIST

        if target not in ["binary", "config", "init", "all", "serveronly"]:
            raise Exception("unknow type: %s" % target)

        if target == "binary":
            logging.info("%s ---copy_binary" % target)
            copy_server(tmp_dir, prefix, servers_list, compile, target, run_path)
            logging.info("%s ---copy_conf_temp" % target)
            copy_conf_temp(tmp_dir, prefix)

        elif target == "config":
            logging.info("%s ---copy_config" % target)
            copy_config(tmp_dir, prefix, location, config_select)

        elif target == "init":
            logging.info("%s ---copy_server" % target)
            copy_server(tmp_dir, prefix, servers_list, compile, target, run_path)
            logging.info("%s ---copy_config" % target)
            copy_config(tmp_dir, prefix, location, config_select, init=True)
            logging.info("%s ---copy_conf_temp" % target)
            copy_conf_temp(tmp_dir, prefix)

        elif target in ("all", "serveronly"):
            logging.info("%s ---copy_server" % target)
            copy_server(tmp_dir, prefix, servers_list, compile, target, run_path)
            logging.info("%s ---copy_config" % target)
            copy_config(tmp_dir, prefix, location, config_select)
            logging.info("%s ---copy_conf_temp" % target)
            copy_conf_temp(tmp_dir, prefix)

        logging.info("%s ---tar_file" % target)
        md5sum, tar_file_name = tar_file(branch, prefix, location, target, tmp_dir, tar_file_path, rsync_key, tmp_path, rsync_conf)
        if target in ("all", "init"):
            tar_dbg_file = tar_dbg_server(tar_file_path, prefix, tar_file_name, compile, dbg_tmp_dir, servers_list,
                                      rsync_key, tmp_path, rsync_conf)
        else:
            tar_dbg_file = ""
        
        if location == "sea":
            push_cos_callback("%s,%s" % (tar_file_name, tar_dbg_file))

    except Exception as e:
        logging.error(e)
        traceback.print_exc()
        run_status = False
    finally:
        logging.info("清除缓存文件 %s" % tmp_path)
        shutil.rmtree(tmp_path)
        logging.info("打包耗时：%s秒" % (int(time.time() - start_time)))
        if run_status is False:
            sys.exit(1)


if __name__ == '__main__':
    main()
