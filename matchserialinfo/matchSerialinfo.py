import os
import re
import datetime
import threading
import fcntl
import time
import sys
import logging.handlers
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

def strdef(expression,getlastnlines):
    str1 = (re.compile(expression)
            .findall(getlastnlines)[0][0] + "-"
            + re.compile(expression)
            .findall(getlastnlines)[0][1] + "-"
            + re.compile(expression)
            .findall(getlastnlines)[0][2] + " "
            + re.compile(expression)
            .findall(getlastnlines)[0][3] + ":"
            + re.compile(expression)
            .findall(getlastnlines)[0][4] + ":"
            + re.compile(expression)
            .findall(getlastnlines)[0][5]
            )

    return str1

def Recompile(getlastnlines,pppnum):
    # print("CSQ：：",
    #       re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..CSQ: (\d*),(\d*).*")
    #       .findall(getlastnlines))
    # logging.warning(
    #       re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..CSQ: (\d*),(\d*).*")
    #       .findall(getlastnlines))
    #
    # print("COPS：：",
    #       re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..COPS: (\d*),(\d*),\"(\w*)\",(\d*).*")
    #       .findall(getlastnlines))
    # logging.warning(re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..COPS: (\d*),(\d*),\"(\w*)\",(\d*).*")
    #       .findall(getlastnlines))
    #
    # print("ICCID：：",
    #       re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..ICCID: (\w*).*")
    #       .findall(getlastnlines))
    # logging.warning(re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..ICCID: (\w*).*")
    #       .findall(getlastnlines))
    #
    # print("HCSQ：：",
    #         re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..HCSQ: (.*),(\d*),(\d*),(\d*).*")
    #       .findall(getlastnlines))
    # logging.warning(re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..HCSQ: (.*),(\d*),(\d*),(\d*).*")
    #       .findall(getlastnlines))

    #if cops or iccid one of them is match faild ,will not write serialinfofile
    if len(re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..COPS: (\d*),(\d*),\"(\w*)\",(\d*).*")
                   .findall(getlastnlines))>0 and len(
        re.compile(".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..ICCID: (\d*).*")
          .findall(getlastnlines))>0:

        savefile = open("/dev/shm/ppp%s"%pppnum, "wb")

        ##judge time is not 10 seconds?
        recsq=".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..CSQ: (\d*),(\d*).*"
        csqtime=datetime.datetime.strptime(strdef(recsq,getlastnlines), '%Y-%m-%d %H:%M:%S')
        fcntl.flock(savefile.fileno(), fcntl.LOCK_EX)##fcntl.LOCK_EX means Exclusive lock
        if (datetime.datetime.now()-csqtime)<datetime.timedelta(seconds=10):
            jsoncsq='{CSQ}'.format(CSQ='{"CSQ":'+"\""+re.compile(recsq)
                           .findall(getlastnlines)[0][6]
                           +","+re.compile(recsq)
                           .findall(getlastnlines)[0][7]+"\""
                           +",")

        recops=".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..COPS: (\d*),(\d*),\"(\w*)\",(\d*).*"
        copstime=datetime.datetime.strptime(strdef(recops, getlastnlines),'%Y-%m-%d %H:%M:%S')
        if (datetime.datetime.now()-copstime)<datetime.timedelta(seconds=10):
            jsoncops='{COPS}'.format(COPS='"COPS":'+"\""+re.compile(recops).findall(getlastnlines)[0][6]
                           +"," + re.compile(recops).findall(getlastnlines)[0][7]
                           +"," +re.compile(recops).findall(getlastnlines)[0][8]
                           +"," + re.compile(recops).findall(getlastnlines)[0][9]+"\""
                           +",")

        reiccid=".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..ICCID: (\w*).*"
        iccidtime = datetime.datetime.strptime(strdef(reiccid, getlastnlines), '%Y-%m-%d %H:%M:%S')
        if (datetime.datetime.now()-iccidtime)<(datetime.timedelta(seconds=10)):
            jsoniccid='{ICCID}'.format(ICCID='"ICCID":'+"\""+re.compile(reiccid).findall(getlastnlines)[0][6]+"\""+",")

        rehcsq = ".*\[(\d*)-(\d*)-(\d*) (\d*):(\d*):(\d*)\]..HCSQ: (.*),(\d*),(\d*),(\d*).*"
        hcsqtime = datetime.datetime.strptime(strdef(rehcsq, getlastnlines), '%Y-%m-%d %H:%M:%S')
        if (datetime.datetime.now() - hcsqtime) < (datetime.timedelta(seconds=10)) :
            if len(re.compile(rehcsq).findall(getlastnlines)[0])==10:
                print ("hcsqTD",re.compile(rehcsq).findall(getlastnlines))
                jsonhcsqTD='{HCSQ}'.format(HCSQ='"HCSQ":'+"\'"+re.compile(rehcsq).findall(getlastnlines)[0][6]
                                           .replace('\"',"")
                               + "," + re.compile(rehcsq).findall(getlastnlines)[0][7]
                               + "," + re.compile(rehcsq).findall(getlastnlines)[0][8]
                               + "," + re.compile(rehcsq).findall(getlastnlines)[0][9]
                                +"}")

                jsonone=jsoncsq+jsoncops+jsoniccid+jsonhcsqTD
                print (jsonone)
                logging.warning(jsonone)
                savefile.write(jsonone.encode())
                savefile.flush()  # close file before Flush Buffer
            if len(re.compile(rehcsq).findall(getlastnlines)[0]) == 11:
                print ("hcsqLTE" ,re.compile(rehcsq).findall(getlastnlines))
                jsonhcsqLTE='{HCSQ}'.format(HCSQ='"HCSQ":'+"\""+re.compile(rehcsq).findall(getlastnlines)[0][6].
                                            replace('\"',"")
                                   +","+re.compile(rehcsq).findall(getlastnlines)[0][7]
                                  + "," + re.compile(rehcsq).findall(getlastnlines)[0][8]
                                  + "," + re.compile(rehcsq).findall(getlastnlines)[0][9]
                                  + "," + re.compile(rehcsq).findall(getlastnlines)[0][10]+"\""
                                  +"}")

                jsontwo = jsoncsq + jsoncops + jsoniccid + jsonhcsqLTE
                print (jsontwo)
                logging.warning(jsontwo)
                savefile.write(jsontwo.encode())
                savefile.flush()  # close file before Flush Buffer

        fcntl.flock(savefile, fcntl.LOCK_UN)#release lock
        savefile.close()

class startThread(threading.Thread):
    def run(self):
        while True:
            #IF out file is exist
            if  os.path.exists('/home/butel/4GAssembler/com/out2')==True:
                RCV_LOG = r"/home/butel/4GAssembler/com/out2"
                getlastnlines = str(get_last_n_lines(RCV_LOG, "100"))
                Recompile(getlastnlines,2)
                time.sleep(10)
            if  os.path.exists('/home/butel/4GAssembler/com/out7')==True:
                RCV_LOG = r"/home/butel/4GAssembler/com/out7"
                getlastnlines = str(get_last_n_lines(RCV_LOG, "100"))
                Recompile(getlastnlines,7)
                time.sleep(10)
            if  os.path.exists('/home/butel/4GAssembler/com/out12')==True:
                RCV_LOG = r"/home/butel/4GAssembler/com/out12"
                getlastnlines = str(get_last_n_lines(RCV_LOG, "100"))
                Recompile(getlastnlines,12)
                time.sleep(10)

if __name__ == '__main__':
    Initlog()
    #sysargv=sys.argv
    mystartthread=startThread()
    mystartthread.start()



