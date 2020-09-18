import re


def get_java_key_stack(self, res_line):
    result = {}
    res_fnA = re.search(self.pattern_filenameA, res_line)
    if res_fnA:
        javaName = res_fnA.group().split('.')[0]
        res_fnAA = re.search('(\\w+\\.)+' + javaName, res_line)
        if res_fnAA:
            result['fileName'] = res_fnAA.group()
        else:
            result['fileName'] = javaName
    else:
        res_fnB = re.search(self.pattern_filenameB, res_line)
        if res_fnB:
            result['fileName'] = res_fnB.group().split('$')[0]
        else:
            res_fnC = re.search(self.pattern_filenameC, res_line)
            if res_fnC:
                result['fileName'] = res_fnC.group()
            else:
                res_fnD = re.search(self.pattern_filenameD, res_line)
                if res_fnD:
                    result['fileName'] = res_fnD.group()
    if re.search(".kt", res_line):
        result['line'] = res_line[:500]
        return result
    if result and len(result['fileName']) > 0:
        result['line'] = res_line[:500]
    return result


def get_java_stack(self, issue_stack, isLine=False):
    result = {}
    for line in issue_stack.splitlines():
        if re.search(self.pattern_stack, line) and not re.search(self.pattern_exce, line) and re.search("com\\.tencent",
                                                                                                        line):
            result = self.get_java_key_stack(line)
            break

    if not result:
        firstLine = re.search(self.pattern_stack, issue_stack)
        if firstLine:
            result = self.get_java_key_stack(firstLine.group())
    if result:
        result['keyStack'] = []
        for line in issue_stack.splitlines():
            re_line = re.search(self.pattern_stack, line)
            if re_line:
                if isLine:
                    result['keyStack'].append(re_line.group()[:500])
                else:
                    result['keyStack'].append(re.sub('\(([\w|\W]+):(\d+)\)', '', line[:500]))
        if isLine:
            a = result['keyStack'].index(result['line'])
        else:
            a = result['keyStack'].index(re.sub('\(([\w|\W]+):(\d+)\)', '', result['line']))
        # 取Java堆栈前10行
        if len(result['keyStack'][a:]) < 10:
            result['keyStack'] = result['keyStack'][-10:]
        else:
            result['keyStack'] = result['keyStack'][a:a + 10]
        print('java')
        print('\r\n'.join(result['keyStack']))
    return result

if __name__ == '__main__':
    if 0:
        print(12138)
    # stack = 'com.tencent.mobileqq.msf.sdk.report.b: MsfCoreSocketReaderNewHeldCatchedException:java.lang.Object.wait(Native Method) java.lang.Object.wait(Object.java:422) com.tencent.mobileqq.msf.core.net.m$b.run(P:541)  : MsfCoreSocketReaderNew QueueHeld\r\ncom.tencent.mobileqq.msf.core.s$d.void run()(P:377)\r\nandroid.os.Handler.handleCallback(Handler.java:873)\r\nandroid.os.Handler.dispatchMessage(Handler.java:99)\r\nandroid.os.Looper.loop(Looper.java:224)\r\nandroid.os.HandlerThread.run(HandlerThread.java:65)\r\n","exceptionFingure":"com.tencent.mobileqq.msf.sdk.report.b\n MsfCoreSocketReaderNewHeldCatchedException:java.lang.Object.wait(B)  : MsfCoreSocketReaderNew QueueHeld\ncom.tencent.mobileqq.msf.core.s$d.void run(B)\nandroid.os.Handler.handleCallback(B)\nandroid.os.Handler.dispatchMessage(B)\n'
    # get_java_stack(stack, isLine=T)
    line = 'com.tencent.mobileqq.statistics.crash.RenderInSubThreadMonitor$RenderInSubThreadException: java.lang.RuntimeException: Render in SubThread is not approved,Process will exit !!!'
    line = 'com.tencent.mobileqq.statistics.crash.RenderInSubThreadMonitor.void checkWithObj(java.lang.Object)(P:32)'
    p = "(\\.|\\w|\\$|-| |,|\\(|\\)|<|>|\\[|\\])*((\\(ProGuard(:\\S+)*\\))|(\\(Unknown Source(:\\S+)*\\))|(\\(\\w+\\.java:\\d+\\))|(\\(\\w+:\\d+\\)))|(\\(\\w+\\.kt:\\d+\\))"
    r = re.search(p, line)
    s = r.group()
    print(s)
