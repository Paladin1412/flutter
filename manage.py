#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import hashlib
import os
import re
import sys
import time
import zipfile

from datetime import datetime
import requests


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django1.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def get_match_stack(issue_stack, pattern):
    res = []
    stack_lines = issue_stack.splitlines()
    for stack_line in stack_lines:
        stack_line = stack_line.strip()
        stack_line = stack_line + '(test)'
        ma = re.findall(pattern, stack_line)
        if ma:
            res.append(ma[0])
    return res


if __name__ == '__main__':
    line = 'com/tencent/mobileqq/AVGestureWrapper/0.2.0/AVGestureWrapper-0.2.0.jarcom/tencent/av/BuildConfig.class'
    hl = hashlib.md5()
    hl.update(line.encode(encoding='utf-8'))
    print(hl.hexdigest())
    line = 'com/tencent/mobileqq/AVGestureWrapper/0.2.0/AVGestureWrapper-0.2.0.jar/com/tencent/av/BuildConfig.class'
    hl.update(line.encode(encoding='utf-8'))
    print(hl.hexdigest())
    line = 'api "com.tencent.mobileqq:osk_exoplayer2_bundle:$qzone_player_version"'
    reVersion = re.search(
        "\\$({?)(AE_jar_version|qzone_player_version|qqminiVersion)({?)",
        line)
    if reVersion:
        print(reVersion.group())
        print(reVersion.group(1))
        print(reVersion.group(2))
    line = "   api(\"com.tencent.mobileqq:AVGestureWrapper:0.2.0\")"
    if re.search("^(\\s*)//", line):
        print("dsgas")
    re_url = re.search("api( *)(\\(*)['\"](com\\.tencent\\S+)['\"]", line)

    date_one = 'Mon Aug 17 11:14:49 2020'
    date_one = datetime.strptime(date_one, '%a %b %d %H:%M:%S %Y').__str__()
    date_one = date_one.split(' ')[0]
    print(date_one)
    date_two = time.strftime('%Y-%m-%d', time.localtime())
    date_one = int(time.mktime(time.strptime(date_one, '%Y-%m-%d')))
    date_two = int(time.mktime(time.strptime(date_two, '%Y-%m-%d')))
    diff = abs(date_one - date_two)
    print(diff / (3600 * 24))

    line = 'Date:   Mon Aug 1++1:14:49 2020 +0800'
    date = re.search('Date:   ([\\s\\S]*) +', line)
    print(date.group(1))

    q = [
        "com.tencent.mobileqq.utils.dialogutils.QQCustomMenuItemPriorityHelper$2.int compare(com.tencent.mobileqq.utils.dialogutils.QQCustomMenuItem,com.tencent.mobileqq.utils.dialogutils.QQCustomMenuItem)(P:77)",
        "com.tencent.mobileqq.utils.dialogutils.QQCustomMenuItemPriorityHelper$2.int compare(java.lang.Object,java.lang.Object)(P:74)",
        "java.util.TimSort.binarySort(TimSort.java:296)", "java.util.TimSort.sort(TimSort.java:221)",
        "java.util.Arrays.sort(Arrays.java:1492)", "java.util.ArrayList.sort(ArrayList.java:1470)",
        "java.util.Collections.sort(Collections.java:206)",
        "com.tencent.mobileqq.utils.dialogutils.QQCustomMenuItemPriorityHelper.void sortMenu(com.tencent.mobileqq.utils.dialogutils.QQCustomMenu)(P:74)",
        "com.tencent.mobileqq.utils.BubbleContextMenu.com.tencent.mobileqq.utils.dialogutils.QQCustomMenuNoIconLayout createContent(com.tencent.widget.BubblePopupWindow,android.content.Context,com.tencent.mobileqq.utils.dialogutils.QQCustomMenu,android.view.View$OnClickListener)(P:124)",
        "com.tencent.mobileqq.activity.selectable.CommonMenuWrapper.void showAtLocation(android.view.View,int,int,com.tencent.mobileqq.utils.dialogutils.QQCustomMenu,int,boolean,android.app.Activity,boolean,java.lang.Integer)(P:199)"]

    l = [
        "com.tencent.mobileqq.utils.dialogutils.QQCustomMenuItemPriorityHelper.void sortMenu(com.tencent.mobileqq.utils.dialogutils.QQCustomMenu)(P:74)",
        "com.tencent.mobileqq.utils.BubbleContextMenu.com.tencent.mobileqq.utils.dialogutils.QQCustomMenuNoIconLayout createContent(com.tencent.widget.BubblePopupWindow,android.content.Context,com.tencent.mobileqq.utils.dialogutils.QQCustomMenu,android.view.View$OnClickListener)(P:124)",
        "com.tencent.mobileqq.activity.selectable.CommonMenuWrapper.void showAtLocation(android.view.View,int,int,com.tencent.mobileqq.utils.dialogutils.QQCustomMenu,int,boolean,android.app.Activity,boolean,java.lang.Integer)(P:199)",
        "com.tencent.mobileqq.activity.selectable.CommonMenuWrapper.void showAtLocation(android.view.View,int,int,com.tencent.mobileqq.utils.dialogutils.QQCustomMenu,int,boolean,java.lang.Integer)(P:189)",
        "com.tencent.mobileqq.activity.selectable.AIOMenuWrapper.void showMenu(com.tencent.mobileqq.utils.dialogutils.QQCustomMenu,android.view.View,int,int,int)(P:26)",
        "com.tencent.mobileqq.activity.selectable.CommonMenuWrapper.void show(android.view.View,int,int,int)(P:86)",
        "com.tencent.mobileqq.activity.selectable.AIOSelectableDelegateImpl.boolean handleMessage(android.os.Message)(P:444)",
        "android.os.Handler.dispatchMessage(Handler.java:98)", "android.os.Looper.loop(Looper.java:181)",
        "android.app.ActivityThread.main(ActivityThread.java:6293)"]
