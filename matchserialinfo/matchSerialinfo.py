import os
import re
import datetime
import threading
import fcntl
import time
import sys
import logging.handlers
import json
from logging.handlers import RotatingFileHandler

def Initlog():
    if os.path.exists('./LOG') == False:
        os.mkdir("./LOG")
    Rthandler = RotatingFileHandler('LOG//myserialinfo.log', maxBytes=10*1024*1024,backupCount=5)
    Rthandler.setLevel(logging.WARN)
    log_fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    formatter = logging.Formatter(log_fmt)
    Rthandler.setFormatter(formatter)
    logging.getLogger('').addHandler(Rthandler)

def get_last_n_lines(logfile, n):
    n=int(n)
    blk_size_max = 4096
    n_lines = []
    with open(logfile, 'rb') as fp:
        fp.seek(0, os.SEEK_END)#0代表偏移量，os.SEEK_END代表从文件结尾开始，相当于2，fp.seek(0, 2)
        cur_pos = fp.tell()#文件指针当前位置
        while cur_pos > 0 and len(n_lines) < n:
            blk_size = min(blk_size_max, cur_pos)#min函数返回给定参数的最小值。
            fp.seek(cur_pos - blk_size, os.SEEK_SET)
            blk_data = fp.read(blk_size)
            assert len(blk_data) == blk_size
            lines = blk_data.split(b'\n')

            # adjust cur_pos
            if len(lines) > 1 and len(lines[0]) > 0:
                n_lines[0:0] = lines[1:]
                cur_pos -= (blk_size - len(lines[0]))
            else:
                n_lines[0:0] = lines
                cur_pos -= blk_size

            fp.seek(cur_pos, os.SEEK_SET)

    if len(n_lines) > 0 and len(n_lines[-1]) == 0:
        del n_lines[-1]

    fp.close()
    return n_lines[-n:]


def GetTime(result):
    str = result[0][0]+"-"+result[0][1]+"-"+result[0][2]+" "+result[0][3]+":"+result[0][4]+":"+result[0][5]
    htime=datetime.datetime.strptime(str, '%Y-%m-%d %H:%M:%S')
    return htime

def WriteFile(jsonresult,pppnum):
    savefile = open("/dev/shm/ppp%s" % pppnum, "wb")
    fcntl.flock(savefile.fileno(), fcntl.LOCK_EX)  ##fcntl.LOCK_EX means Exclusive lock
    savefile.write(jsonresult.encode())
    fcntl.flock(savefile, fcntl.LOCK_UN)  # release lock
    savefile.close()

def Recompile(csqstr,copsstr,iccidstr,hcsqstr,pppnum):
    CSQResult = CSQPattern.findall(csqstr)
    COPSResult = COPSPattern.findall(copsstr)
    HCSQResult = HCSQPattern.findall(hcsqstr)
    ICCIDResult = ICCIDPattern.findall(iccidstr)
    HCSQTDResult=HCSQTDPattern.findall(hcsqstr)
    jsondict={'CSQ': '','COPS':'','ICCID':'','HCSQ':''}
    if len(CSQResult):
        csqtime=GetTime(CSQResult)
        if (datetime.datetime.now()-csqtime)<datetime.timedelta(seconds=60):
            jsondict['CSQ']="%s,%s"%(CSQResult[0][6],CSQResult[0][7])
    if len(COPSResult)>0:
        copstime=GetTime(COPSResult)
        if (datetime.datetime.now()-copstime)<datetime.timedelta(seconds=10):
            jsondict['COPS']="%s,%s,%s,%s"%(COPSResult[0][6],COPSResult[0][7],COPSResult[0][8],COPSResult[0][9])
    if len(ICCIDResult)>0:
        iccidtime = GetTime(ICCIDResult)
        if (datetime.datetime.now()-iccidtime)<(datetime.timedelta(seconds=10)):
            jsondict['ICCID']=str(ICCIDResult[0][6])
    if len(HCSQResult):
        hcsqtime = GetTime(HCSQResult)
        if (datetime.datetime.now() - hcsqtime) < (datetime.timedelta(seconds=10)) :
            if len(HCSQResult[0]) == 11:
                jsondict['HCSQ']="%s,%s,%s,%s,%s"%(HCSQResult[0][6].replace('\"',""),HCSQResult[0][7],
                HCSQResult[0][8],HCSQResult[0][9],HCSQResult[0][10])
    elif len(HCSQTDResult):
        hcsqtdtime=GetTime(HCSQTDResult)
        if (datetime.datetime.now() - hcsqtdtime) < (datetime.timedelta(seconds=10)) :
            if len(HCSQTDResult[0][6]) == 'TD-SCDMA':
                jsondict['HCSQ']="%s,%s,%s,%s"%(HCSQResult[0][6].replace('\"',""),HCSQResult[0][7],
                HCSQResult[0][8],HCSQResult[0][9])
    jsonstr = json.dumps(jsondict)
    logging.warning(jsonstr)
    WriteFile(jsonstr,pppnum)


def KeyWordFilter(nlines,keyword):
    for linebyte in reversed(nlines):
        linestr=str(linebyte)
        if keyword in linestr:
            return linestr
    return ""


def main(num):
    RCV_LOG = r"out%s"%num
    nlines = get_last_n_lines(RCV_LOG, "100")
    csqstr = KeyWordFilter(nlines, "+CSQ")
    copsstr = KeyWordFilter(nlines, "COPS")
    iccidstr = KeyWordFilter(nlines, "ICCID")
    hcsqstr = KeyWordFilter(nlines, "HCSQ")
    Recompile(csqstr, copsstr, iccidstr, hcsqstr, num)

if __name__ == '__main__':
    Initlog()
    CSQPattern = re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..CSQ: (\d*),(\d*).*")
    COPSPattern = re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..COPS: (\d*),(\d*),\"(\w*)\",(\d*).*")
    HCSQPattern = re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..HCSQ: (.*?),(\d*),(\d*),(\d*),(\d*)")
    ICCIDPattern = re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..ICCID: (\w*).*")
    HCSQTDPattern=re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..HCSQ: (.*?),(\d*),(\d*),(\d*)")

    while True:
        #IF out file is exist
        if  os.path.exists('out2')==True:
            main(2)
        if  os.path.exists('out7')==True:
            main(7)
        if  os.path.exists('out12')==True:
            main(12)
        time.sleep(1)



