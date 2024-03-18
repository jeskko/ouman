#!/usr/bin/env python3

import yaml,serial,logging
from time import sleep
from prometheus_client import Info,Gauge,start_http_server

logging.basicConfig(level=logging.INFO)

def getregister(i):
    crc=int((0x81+0x02+0x00+i) & 0xFF)
    sendbuff=[0x02,0x81,0x02,0x00,i,crc]

    ser.write(sendbuff)

    ser.flush()

    b1=ser.read()
    b2=ser.read()
    le=int.from_bytes(ser.read(),'big')
    crc_recv=int.from_bytes(b2,"big")+le
    tmp=" "
    res=bytes()
    while ((len(tmp)>0) and (le>0)):
        tmp=ser.read()
        crc_recv+=int.from_bytes(tmp,"big")
        res=res+tmp
        le-=1
    crc=int.from_bytes(ser.read(),"big")
    crc_recv=crc_recv&0xff
    if crc!=crc_recv:
        print("CRC error!")
        return False
    return res[2:]
        
def getdata(d):
    result=[]
    try:
        for i in d.items():
            r=getregister(i[0])
            resu=""
            for x in r:
                rt=hex(x)[2:]
                if (len(rt)<2):
                    rt="0"+rt
                resu+=rt
            logging.debug(f"{i[0]}: {resu}")
            for j in i[1].items():
                idx=j[0]
                if j[1]["type"]=="TEMP_100":
                    metrics[j[1]["short"]].set((r[idx]*256+r[idx+1])/100)
                if j[1]["type"]=="TEMP_10":
                    metrics[j[1]["short"]].set((r[idx]*256+r[idx+1])/10)
                if j[1]["type"]=="BYTE":
                    metrics[j[1]["short"]].set(r[idx])
                if j[1]["type"]=="SHORT":
                    metrics[j[1]["short"]].set((r[idx]*256+r[idx+1]))
    except IndexError:
        logging.debug("Problem with reading")
                
    
with open('config.yaml') as c:
    conf = yaml.safe_load(c)    

# initialize metrics

metrics={}

metrics["device"]=Info('device', 'Device information')

# if socket connection, serial configuration parameter starts with s
if conf["ouman-prometheus"]["serial"][0] == "s":
    ser = serial.serial_for_url(conf["ouman-prometheus"]["serial"], timeout=1)
else:
    ser=serial.Serial(conf["ouman-prometheus"]["serial"],4800, timeout=1)

# device model
r=getregister(0x5f)
model=(r[5:].decode('CP437').rstrip('\x00'))

# device version
r=getregister(1)
sernum=str(int.from_bytes(r[0:3],"little"))
modelnum=(r[4:7]).decode('CP437').rstrip('\x00')
version=str(r[8]/10)
build_date=(r[9:]).decode('CP437').rstrip('\x00')

metrics["device"].info({'model': model,
                        'modelnum': modelnum,
                        'version': version,
                        'build_date': build_date,
                        'serial': sernum})

try:
    for d in conf["devices"][model]:
        for i in d.items():
            for j in i[1].items():
                if j[1]["type"]=="TEMP_100":
                    metrics[j[1]["short"]]=Gauge(j[1]["short"],j[1]["name"])
                elif j[1]["type"]=="TEMP_10":
                    metrics[j[1]["short"]]=Gauge(j[1]["short"],j[1]["name"])
                elif j[1]["type"]=="BYTE":
                    metrics[j[1]["short"]]=Gauge(j[1]["short"],j[1]["name"])
                elif j[1]["type"]=="SHORT":
                    metrics[j[1]["short"]]=Gauge(j[1]["short"],j[1]["name"])
except KeyError:
    logging.error(f"Unknown device {model}.")
    exit()

start_http_server(conf["ouman-prometheus"]["port"])

while True:

    for d in conf["devices"][model]:
        getdata(d)
    
    sleep(5)