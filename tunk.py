#!/usr/bin/env python3

import serial,datetime

ser=serial.Serial('/dev/ttyS4',4800, timeout=1)

# EH-203 
# Versio 2.15
# 10012409

# 1 versio
# 2 joku kello
# 3 sama kello
# 12 0c 3a28120f460000280a1e050f46fa0200640000020500010000000f00000000 l1 asioita
# 13 0d 0000d7008c00320000009600d7008c00320000009600000000000000000000
# 14 0e 3e2a140f4600000a1e02280064000000050000000000190000460532050100 l2 asioita
# 15 0f 0f000000000002190000000000002a11000000000002000000001300000000
# 16 10 00024400000041008c0046001200000001000f003c003c000a000000000000 lv asioita
# 17 11 0000010c0c060c040c0c0c0c0c0c0c0c0c63630c0000000000000000000000
# 18 12 ulkolämpö
# 19 13 
# 20 14 L1 menovesi
# 21 15 L1 huone
# 22 16
# 23 17 L1 paluu
# 24 18 LV meno
# 25 19 LV kierto
# 26 1a L2 meno
# 27 1b
# 28 1c
# 29 1d
# 30 1e
# 31 1f
# 32 20
# 33 21 mittaus 9
# 34 22 mittaus 10
# 35 23 000000000b01
# 36 24 000000000b0107e80208162008
# 37 25 0025000000001401
# 38 26 002600000000140107e80208162008
# 39 27 0027000000001401
# 40 28 002804
# 41 29 mittaus 11

# 45 tilamuuttuja 
# 49 L1-venttiili
# 50 L2-venttiili
# 51 LV-venttiili

# 60 huipputeho
# 61 huippuvirtaus
# 63 KL energia
# 64 KL vesi

# 24 joku kello
# 26 joku kello 

# 
i=0x0d

# sms-emulaatio päällä menee koko ajan, digitaalit ja releet
# 02 81 02 00 2d b0
rr=[]
for i in range(255):
    rr.append("")
while True: 
    for i in range(0,101):

        crc=int((0x81+0x02+0x00+i) & 0xFF)
        sendbuff=[0x02,0x81,0x02,0x00,i,crc]

        ser.write(sendbuff)

        ser.flush()

        b1=ser.read()
        b2=ser.read()
        le=int.from_bytes(ser.read(),'little')
        crc_recv=int.from_bytes(b2,"little")+le
        tmp=" "
        res=bytes()
        while ((len(tmp)>0) and (le>0)):
            tmp=ser.read()
            crc_recv+=int.from_bytes(tmp,"little")
            res=res+tmp
            le-=1
        crc=int.from_bytes(ser.read(),"little")
        crc_recv=crc_recv&0xff
        resu=""
        if crc==crc_recv:
            for x in res:
                r=hex(x)[2:]
                if (len(r)<2):
                    r="0"+r
                resu+=r
            try:
                if rr[i]!=resu:
                    out=resu
                    if i==1:
                        # version info
                        snro=int.from_bytes(res[2:5],"little")
                        model=(res[6:9]).decode('CP437').rstrip('\x00')
                        version=res[10]/10
                        build_date=(res[11:]).decode('CP437').rstrip('\x00')
                        out=f"{snro} {model} {version} {build_date}"
                    if (i==2 or i==3):
                        # clock
                        t=datetime.datetime(year=res[2]*256+res[3],month=res[4],day=res[5],hour=res[6],minute=res[7],second=res[8])
                        out=str(t)
                    if (i in [18,20,21,23,24,25,26,27,33,34,41]):
                        val=(res[2]*256+res[3])/100
                        out=f"{val} °C"
                    print(f"ID {i}: {out}")
            except IndexError:
                pass
            rr[i]=resu

        else:
            print("CRC error!")
        