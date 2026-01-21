# coding=utf-8

import requests
import webbrowser
import os
import subprocess
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


"""
1. 所有生成的文件都将放在user的Documents下的名为scheme的文件夹下
"""

# 请根据需求替换下方最重要的五个参数
project_path = "/Users/aikesi/Documents/Prorjects/call/code/leavecall"  # fixme 项目路径, 要打包的项目在哪里
workspace_name = "leavecall.xcworkspace"                 # fixme 工程名称, 要打包哪个工程
scheme_name = "leavecall"                                # fixme 要打包哪个scheme
config = "Debug"                                    # environment 打release还是debug
save_path = ''      # 程序自动计算, 不用管, 本次打包内容存放的路径

# debug 和 Release 使用不同的plist文件, 两种包打出来的体积相差还是较大的
plist_path_dev = 'ExportOptions_adhoc.plist'  # 之前打包成功的plist文件
plist_path_appstore = 'ExportOptions_appstore.plist'  # 之前打包成功的plist文件

# 蒲公英api信息:
API_KEY = "5302a529a2056d0bf688d0d2332f63e7"
USER_KEY = "ea99283e4bc1cd32908219a8a86fc7b8"
download_path = "https://www.pgyer.com/leavecall"    # fixme 更换为你自己的蒲公英下载地址

# fixme 发邮件信息, 根据实际情况换为自己的相关信息
stmp_server = "smtp.qq.com"  # 邮件服务期底子
authorization_code = "vyccfznymsgmbicc"  # 发件人邮箱授权码, 用来登录发件人邮箱
sender_address = "469087843@qq.com"     # 发件人邮箱
receiver_address_people = ["aikesi128@163.com"]   # 收件人数组


def log(info):
    print("\n***************************** < %s > ******************************" % info.capitalize())


def log_error(error):
    print(f'\n*************** WARNING: {error.capitalize()} !!! ***************')


def send_email():
    log("Begin to send email...")
    # QQ邮箱需要使用SSL连接，端口465
    server = smtplib.SMTP_SSL(stmp_server, 465)
    server.login(sender_address, authorization_code)

    multi = MIMEMultipart("mixd")
    multi["from"] = sender_address
    multi["to"] = receiver_address_people[0]

    if config == "Debug":
        multi["subject"] = Header("上传pgyer完成通知", "utf-8")
        html_text = """
            <p>应用已更新至蒲公英, 请更新您的应用程序</p>
            <a href = "%s">click to update</a>
        """ % download_path
    else:
        multi["subject"] = Header("上传appstore完成通知", "utf-8")
        html_text = '<p>应用已更新至TestFlight, 稍后收到Testflight推送后请下载最新版进行测试</p>'

    html = MIMEText(html_text, "html", "utf-8")
    # html["content-disposition"] = "attachment;"
    multi.attach(html)

    server.sendmail(sender_address, receiver_address_people, multi.as_string())
    server.quit()
    log("Email send success!")

    # open safari
    if config == "Debug":
        webbrowser.open_new(download_path)

    os.system(f'open {save_path}')


# 蒲公英上传参考地址: https://www.pgyer.com/doc/view/api#fastUploadApp
def upload_pgyer():
    log("Begin upload ipa file to pgyer")
    start = time.time()
    ipa_path = f'{os.path.join(save_path,"export")}/{scheme_name}.ipa'
    url = 'https://www.pgyer.com/apiv2/app/getCOSToken'     # 新版快速上传
    data = {
        'uKey': USER_KEY,
        '_api_key': API_KEY,
        'buildType': 'ipa',
        'oversea': 2,
        'installType': '1',
        'updateDescription': "this is test script for iOS"
    }

    # 获取上传地址
    r = requests.post(url, data=data)
    if r.status_code == 200:

        # 获取arguments成功, 准备上传文件
        obj = r.json()
        endpoint = obj['data']['endpoint']
        key = obj['data']['key']
        params = obj['data']['params']
        body = {"key": key,
                "signature": params['signature'],
                "x-cos-security-token": params['x-cos-security-token'],
                }
        files = {"file": open(ipa_path, "rb")}
        resp = requests.post(endpoint, data=body, files=files)
        if resp.status_code == 204:
            log("Upload pyger success, take %0.1f second" % (time.time() - start))
        else:
            log('upload pyger fail')
            exit(-1)
    else:
        log("Upload failed, take %0.1f second" % (time.time() - start))
        exit(-1)


def upload_appstore():
    ipa_path = f'{os.path.join(save_path, "export")}/{scheme_name}.ipa'
    
    # 检查IPA文件是否存在
    if not os.path.exists(ipa_path):
        log_error(f'IPA file not found: {ipa_path}')
        exit(-1)
    
    # fixme 命令构造查看参开文档 [3.3 上传的应用商店账号的验证问题] 章节进行修改
    command = f'xcrun altool --upload-app -f {ipa_path} -t ios -u 742748212@qq.com ' \
              '--apiIssuer bbd158ad-295f-4afc-81dc-da8b4efc53e9 --apiKey 7D98AQPH95 ' \
              '--verbose --show-progress'
    log("Begin upload ipa to app store")
    log(command)
    start = time.time()
    
    # 捕获标准输出和标准错误，以便显示详细的错误信息
    res = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = res.communicate()
    
    end = time.time()
    
    # 输出命令的执行结果
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
    
    if res.returncode == 0:
        log("upload appstore success, take %.1f seconds" % (end - start))
    else:
        log_error(f"upload appstore failed, take %.1f seconds" % (end - start))
        log_error(f"Return code: {res.returncode}")
        if stderr:
            log_error(f"Error details: {stderr}")
        exit(-1)


def export():
    log("Begin export ipa")

    if not os.path.exists(plist_path_dev):
        log_error('please check plist_path_dev exportOptionPlist file path')
        exit(0)

    if not os.path.exists(plist_path_appstore):
        log_error('please check plist_path_appstore exportOptionPlist file path')
        exit(0)

    plist_path = ''
    if config == "Debug":
        plist_path = plist_path_dev
    else:
        plist_path = plist_path_appstore

    start = time.time()
    arc_p = os.path.join(save_path, f'{scheme_name}.xcarchive')
    exp_p = os.path.join(save_path, 'export')
    command = f"xcodebuild -exportArchive -archivePath {arc_p} -exportPath {exp_p} -exportOptionsPlist {plist_path}"
    log(command)
    res = subprocess.Popen(command, shell=True)
    res.wait()
    end = time.time()
    if res.returncode == 0:
        log("export success, take %.1f seconds" % (end - start))
    else:
        log("export failed, take %.1f seconds" % (end - start))
        exit(-1)

    # 暂时先不删除archive后的文件
    # command = "rm -rf %s" % archive_path
    # res = subprocess.Popen(command, shell=True)
    # res.wait()
    # if res.returncode == 0:
    #     log("archive file has been deleted")
    # else:
    #     log("archive file delete fail")


def archive():
    log("begin archive")
    start = time.time()
    arc_p = os.path.join(save_path, f'{scheme_name}.xcarchive')
    ws_p = os.path.join(project_path, workspace_name)  # 工程全路径
    command = f"xcodebuild archive -archivePath {arc_p} -workspace {ws_p} -scheme {scheme_name} -configuration {config}"
    log(command)
    res = subprocess.Popen(command, shell=True)
    res.wait()
    end = time.time()
    if res.returncode == 0:
        log("archive success, take %.1f seconds" % (end - start))
    else:
        log("archive failed, take %.1f seconds" % (end - start))
        exit(-1)


def clear():
    log("Begin clear")
    start = time.time()
    workspace_p = os.path.join(project_path, workspace_name)    # 工程全路径
    command = f"xcodebuild clean -workspace {workspace_p} -scheme {scheme_name}"
    res = subprocess.Popen(command, shell=True)
    res.wait()
    end = time.time()
    if res.returncode == 0:
        log("clean success, take %0.1f seconds" % (end - start))
    else:
        log("clean failed, take %0.1f seconds" % (end - start))


def check_file():
    global project_path
    # 检查项目路径
    if not os.path.exists(project_path):
        log_error('Please check project path, 项目路劲不存在')
        # 目标路径不存在, 开始计算项目路径
        res = os.popen("pwd")
        project_path = res.read().replace("/script", "").strip()

    # 检查workspace
    if not os.path.exists(os.path.join(project_path, workspace_name)):
        log_error('Please check workspace path')
        return

    # 检查user documents目录下有没有名为scheme的文件夹
    doc_path = os.popen('cd ~/Documents; pwd').read().strip()
    des_root_path = os.path.join(doc_path, scheme_name)  # ~/Documents/scheme
    if not os.path.exists(des_root_path):
        os.mkdir(des_root_path)  # 创建根文件夹

    global save_path

    # 文件夹名称
    dir_name = time.strftime('%Y-%m-%d_%H_%M')
    save_path = os.path.join(des_root_path, dir_name)   # ~/Documents/scheme/2023-01-01_12_12_23
    if not os.path.exists(save_path):
        os.mkdir(save_path)  # 创建本次存放文件的文件夹

    log(f'root path is {save_path}')
    log('Finish check')


def choose_upload_location():
    global config
    print('请选择上传目标: 1. 蒲公英  2.app store\n')
    des = input()

    while not isinstance(des.isdecimal(), int):
        print('请选择上传目标: 1. 蒲公英  2.app store\n')
        des = input()

    if int(des) != 1 and int(des) != 2:
        exit('非法输入, 程序终止!!!')

    if int(des) == 1:
        config = "Debug"
    else:
        config = 'Release'


if __name__ == "__main__":

    start_time = time.time()

    check_file()

    # clear() # 不用clear 会导致下一次真机运行编译比较慢
    choose_upload_location()
    archive()
    export()

    if config == "Release":
        upload_appstore()
    else:
        upload_pgyer()

    send_email()
    # webbrowser.open_new(download_path)

    end_time = time.time()
    log("python script execute finished, take %.1f seconds" % (end_time - start_time))
