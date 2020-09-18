# -*- coding: utf-8 -*-
'''
从RDM批量导出issues
Created on 2019年6月27日
@author: cissili
'''

import json
import shutil

import requests
import time
import re
import os

from svn_handler import SVNHandle
from file_handler import FileHandler
from crashapp.log import logger
from crashapp.filter_issues import FilterIssues
import logging

logger = logging.getLogger('app')
import datetime
import traceback
from common_method import *
import tarfile
import urllib
from enumrate_class import *
import sys
from multiprocessing import Process, Manager

reload(sys)
sys.setdefaultencoding('utf8')

RDQ_API = 'http://api.rdm.wsd.com/gateway/crash/api/{}/{}/batchIssueCrash?' \
          'offset=0&limit={}&status={}&type={}&version={}&contact={}&sortField={}&sortOrder=desc&ft={}&rdm_app_id={}&rdm_app_key={}'

RDM_LINK = 'http://rdm.oa.com/products?productId=6c5ccd48-0f0b-442a-ba03-d657ec58a5be&sub=issueDetail%3Ftarget%3Dnew_rdm%' \
           '26productId%3D6c5ccd48-0f0b-442a-ba03-d657ec58a5be%26platformId%3D1%26mergeId%3D{}%26packageId%3D{}&model=exception'

SORT_USRNUM = 'userNum'
SORT_UPTIME = 'uploadTime'
PRE_STACK = 3
TOP = 10

TIME_TAG = str(time.time())[0:10]


class ExportIssues():
    '''
    issues的获取与处理
    '''

    def __init__(self, filehandler=None):
        # 加载配置文件
        # order = 'from bugs import %s_%s_%s as conf' % ('config', platform, product)
        # exec order
        # self.conf = conf

        self.history_crash_issues = []
        self.new_crash_issues = []
        self.logged_issues = []
        self.stack_pool = []
        self.dump_stack = []

        # self.pattern_exce = '^(java\.|android\.|com\.android\.|dalvik\.|de\.|external\.|org\.|ANR_EXCEPTION)'

        if filehandler == None:
            return
        self.filehandler = filehandler
        # self.svn = SVNHandle(filehandler)
        # self.svn.update_svn()

        self.platform = filehandler.platflag

        self.number = filehandler.setconfig['GET_CRASH_NUM']
        self.ft = filehandler.setconfig['CRASH_FT']
        self.rdm_app_id = filehandler.setconfig['RDM_APP_ID']
        self.rdm_app_key = filehandler.setconfig['RDM_APP_KEY']
        self.crash_type = filehandler.setconfig.get('CRASH_TYPE')
        self.default_te = filehandler.setconfig['CRASH_DEFAULT_TE']
        self.default_owner = filehandler.setconfig['CRASH_DEFAULT_OWNER']
        self.status = filehandler.setconfig.get('ISSUE_STATUS')
        self.previous_and_current_version = filehandler.setconfig['PREVIOUS_AND_CURRENT_VERSION']
        self.version_bundle_map = filehandler.setconfig['VERSION_BUNDLE_MAP']
        self.bundle_id = filehandler.setconfig['BUNDLE_ID']

        self.min_crash_num = filehandler.setconfig.get('MIN_CRASH_NUM', 1)
        self.OSVersion = filehandler.setconfig.get('OS_VERSION', '')

        self.stack_pattern = filehandler.setconfig['PATTERN_STACK']
        self.pattern_exce = filehandler.setconfig['PATTERN_EXCE']
        self.pattern_native = filehandler.setconfig['PATTERN_NATIVE']
        # self.pattern_native_exce = filehandler.setconfig['PATTERN_NATIVE_EXCE']
        self.pattern_filenameA = filehandler.setconfig['PATTERN_FILENAME_A']
        self.pattern_filenameB = filehandler.setconfig['PATTERN_FILENAME_B']
        self.pattern_filenameC = filehandler.setconfig['PATTERN_FILENAME_C']
        self.pattern_filenameD = filehandler.setconfig['PATTERN_FILENAME_D']
        # 越狱插件更新地址：https://docs.google.com/spreadsheets/d/17Rn7sT94DpIGiPL_PoRhXKYfTV_Qc6E7zYGGQX7W-yg/edit#gid=680557560

        self.ignore_crash = filehandler.ignoreconfig['Crash']
        self.ignore_anr = filehandler.ignoreconfig['ANR']

        if self.platform == 2:
            self.pattern_break = filehandler.setconfig['IOS_BREAK_PATTERN']

        self.utestuins = None
        # self.utestuins = filehandler.utestuins
        self.crashDetail = filehandler.setconfig.get('CRASH_DETAIL')
        # self.issueId = None
        self.issueId = filehandler.issueId

    def handle_rdq_url(self, **kwargs):
        '''
        拼接rqd接口url
        '''
        # RDQ_API = 'http://api.rdm.wsd.com/gateway/crash/api/{}/{}/batchIssueCrash?' \
        #               'offset=0&limit={}&status={}&type={}&version={}&contact={}&sortField={}&sortOrder=desc&ft={}&rdm_app_id={}&rdm_app_key={}'
        RDQ_API = 'http://api.rdm.wsd.com/gateway/crash/api/{}/{}/batchIssueCrash?rdm_app_id={}&rdm_app_key={}&offset=0&sortOrder=desc'

        RDQ_API = RDQ_API.format(self.bundle_id, self.platform, self.rdm_app_id, self.rdm_app_key)

        param = ''
        if kwargs:
            self.filehandler.recording("RDM导出issues的参数有: {}".format(kwargs))
            for key, value in kwargs.iteritems():
                param += "&{}={}".format(key, value)
        return RDQ_API + param

    def export_issues(self, rqd_url):
        '''
        使用RQD接口导出issue文件
        :param rqd_url: 拼接参数后的URL
        :return: 解压后的文件名
        '''
        self.filehandler.recording('开始访问RDM:\n' + rqd_url)
        response = retry_post(rqd_url, try_times=3, interval=5, req_type='get')
        response = response.text
        url_data = response.split('basePath:')[1].split(',readme:')[0].split(',filePrefix:')
        download_url = url_data[0] + '/' + url_data[1] + '.tar.gz'
        # download_url = 'http://fms.et.wsd.com/fms1/data/EXPORT/issue/20190910/com.tencent.mobileqq_114115_.tar.gz'
        self.filehandler.recording('等待RDM完成文件上传, 约2分钟')
        ##这里要等待RDM完成文件上传,一般为2分钟
        # time.sleep(60)
        self.filehandler.recording('开始下载文件:\n' + download_url)

        local_path = os.path.join(os.getcwd(), 'crashapp', 'issuefile', url_data[1] + '.tar.gz')
        # local_path = os.path.join(os.getcwd(), 'crashapp', 'issuefile', 'com.tencent.mobileqq_114115_.tar.gz')
        unzip_file_path = ''
        extractall_times = 0
        while True:
            try:
                download = retry_post(download_url, try_times=5, interval=120, req_type='get')
                data = download.content
                self.filehandler.recording('下载文件成功,尝试解压文件')
                with open(local_path, "wb") as code:
                    code.write(data)
                t = tarfile.open(local_path, 'r')
                t.extractall()
                t.close()
                if t:
                    self.filehandler.recording('解压文件{}成功'.format(local_path))

                    break
            except Exception:
                if extractall_times >= 5:
                    exstr = traceback.format_exc()
                    self.filehandler.recording(exstr)
                    raise Exception(exstr)
                self.filehandler.recording('尝试解压，第{}次失败'.format(str(extractall_times + 1)))
                # os.remove(local_path)
                extractall_times = extractall_times + 1
                time.sleep(5)

        try:
            issue_path = os.path.join(os.getcwd(), 'crashapp', 'issuefile')
            unzip_file_path = url_data[1] + '0.txt'
            # unzip_file_path = 'com.tencent.mobileqq_114115_0.txt'
            shutil.move(unzip_file_path, issue_path)
            unzip_file_path = os.path.join(issue_path, url_data[1] + '0.txt')
            # unzip_file_path = os.path.join(issue_path, 'com.tencent.mobileqq_114115_0.txt')
            if os.path.exists(unzip_file_path):
                return unzip_file_path
            else:
                return None

        except:
            self.filehandler.recording('issue文件移动失败' + unzip_file_path)
            return None

    def export_one_issues(self, version, crashDetail=None, limit=0):
        '''
        根据输入参数拼接URL导出1个文件
        :param version: 版本号
        :param crashDetail: crash关键字，可选
        :param limit: 导出issue条数，一般根据字段排序后导出top的数量
        :return: 文件
        '''
        params = {
            'limit': limit,
            'status': self.status if self.status else 0,
            'version': version,
            # 'sortField': 'userNum',
            'sortField': 'crashNum',

        }
        if self.crash_type:
            params['type'] = self.crash_type
        if self.ft:
            params['ft'] = self.ft
        if crashDetail:
            params['crashDetail'] = crashDetail


        rqd_url = self.handle_rdq_url(**params)
        issuefile = self.export_issues(rqd_url)
        return issuefile

    def export_gray_issues(self):
        '''
        直接取参数拼接URL导出
        :return: 文件列表
        '''
        filelist = []
        for ver in self.version_bundle_map:
            issuefile = self.export_one_issues(version=ver, limit=self.number)
            if issuefile:
                filelist.append(issuefile)
        return filelist

    def export_by_crashDetail(self):
        '''
        根据crash关键字列表，循环拼接URL导出
        :return:文件列表
        '''
        filelist = []
        for ver in self.version_bundle_map:
            for detail in self.crashDetail:
                issuefile = self.export_one_issues(ver, detail, self.number)
                if issuefile:
                    filelist.append(issuefile)
        return filelist

    def export_by_uin(self):
        '''
        根据UIN列表，循环拼接URL导出
        :return:文件列表
        '''
        filelist = []
        for uin in self.utestuins:
            params = {
                'limit': self.number,
                'status': self.status if self.status else 0,
                'contact': uin,
                'sortField': 'uploadTime',
            }
            if self.crash_type:
                params['type'] = self.crash_type
            if self.ft:
                params['ft'] = self.ft

            rqd_url = self.handle_rdq_url(**params)
            issuefile = self.export_issues(rqd_url)
            if issuefile:
                filelist.append(issuefile)
        return filelist

    def export_by_issueId(self):
        '''
        根据issueId列表，循环拼接URL导出（limit、issueId）
        :return:文件列表
        '''
        filelist = []
        for issueId in self.issueId:
            print issueId
            params = {
                'limit': 1,
                'issueId': issueId
            }
            # 拼接访问rdm的api接口
            rqd_url = self.handle_rdq_url(**params)
            rqd_url = re.sub('&sortOrder=desc', '', rqd_url)
            #   使用RQD接口导出issue文件
            issuefile = self.export_issues(rqd_url)
            if issuefile:
                filelist.append(issuefile)
        return filelist

    def dedupe_issues(self, issue_list):
        '''
        根据issueId去重
        :param issue_list: 导出的所有文件中，所有issue组成的列表
        :return: 根据issueId去重后的issue列表
        '''
        ids = []
        dedupe_issues = []
        self.filehandler.recording('issueId去重【前】数据: {} 条'.format(len(issue_list)))

        for issue in issue_list:
            id = issue["issueId"]
            temp = {}
            if id not in ids:
                ids.append(id)
                temp_list = filter(lambda x: x["issueId"] == issue["issueId"], issue_list)
                # temp_list = sorted(temp_list, key=lambda x: x['userNum'], reverse=True)
                dedupe_issues.append(temp_list[0])
            else:
                continue
        print len(dedupe_issues)
        dedupe_issues = sorted(dedupe_issues, key=lambda x: int(x['userNum']), reverse=True)[:int(self.number)]
        self.filehandler.recording('issueId去重【后】数据: {} 条'.format(len(dedupe_issues)))
        return dedupe_issues

    def export_version_issue(self, ver):
        '''
        获取配置文件中，上个版本的limit=300的一个json文件
        :return:文件列表
        '''
        params = {
            'limit': 300,
            'version': ver,
            'sortField': 'crashNum',
        }
        if self.crash_type:
            params['type'] = self.crash_type
        if self.ft:
            params['ft'] = self.ft
        rqd_url = self.handle_rdq_url(**params)
        issuefile = self.export_issues(rqd_url)
        return issuefile

    def extract_keystack(self):
        issue_package_files = []
        for ver in self.previous_and_current_version:
            issue_path = os.path.join(os.getcwd(), 'crashapp', 'issuefile')
            json_file_path = os.path.join(issue_path, '{}_issue_package.json'.format(ver))
            issue_package_files.append(json_file_path)
            if not os.path.exists(json_file_path):
                file = self.export_version_issue(ver)
                if file is not None:
                    os.rename(file, json_file_path)
        issue_path = os.path.join(os.getcwd(), 'crashapp', 'issuefile')
        issue_filter_path = os.path.join(issue_path, '{}_issue_filter_package.json'.format(self.version_bundle_map.keys()[0]))
        if not os.path.exists(issue_filter_path):
            wait_filter_issues = []
            for f in issue_package_files:
                issues = self.filehandler.get_json_file(f)
                if issues:
                    wait_filter_issues.extend(issues)
            filehandler = FilterIssues(self.filehandler)
            issue_list = filehandler.filter_all_issues(wait_filter_issues)
            issue_list = filehandler.filter_keyStack(issue_list)
            with open(issue_filter_path, "w") as code:
                json.dump(issue_list, code)
                code.close()

    def export_issues_main(self, exportType=1):
        '''
        RQD接口导出数据的主函数入口
        :param exportType:
        :return: RDM crash原始数据issue列表
        '''
        # issue_files = [
        #     'D:\\workspace\\Intpweb_local\\INTProject\\crashapp\\issuefile\\test.txt'
        # ]

        if self.utestuins:
            print( self.utestuins)
            issue_files = self.export_by_uin()
        elif self.issueId:
            print( self.issueId)
            # 根据issueId列表，循环拼接URL导出（limit、issueId）
            issue_files = self.export_by_issueId()
        elif self.crashDetail[0] is not '' and self.crashDetail and len(self.crashDetail) > 0:
            print( self.crashDetail)
            issue_files = self.export_by_crashDetail()
        else:
            issue_files = self.export_gray_issues()

        all_issues = []
        for f in issue_files:
            issues_list = self.filehandler.get_json_file(f)
            if issues_list:
                all_issues.extend(issues_list)
        self.extract_keystack()

        return self.dedupe_issues(all_issues)


if __name__ == '__main__':
    from file_handler import FileHandler

    filehandler = FileHandler(platform='And')
    e = ExportIssues(filehandler)

    all_issues = [
        {'issueId': 123, 'keyStack': 'java.lang.wedxdf'},
        {'issueId': 234, 'keyStack': 'java.lang.wedxdf'},
        {'keyStack': 'java.lang.sadf323d', 'issueId': 234},
        {'issueId': 123, 'keyStack': 'java.lang.sadf323d'}
    ]
