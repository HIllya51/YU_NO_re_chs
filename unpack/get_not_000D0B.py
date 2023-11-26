 
with open('vtext_trans.txt','r',encoding='utf8') as ff:
    bs=ff.read()
lines=bs.split('\n') 
with open('vunknown.txt','w',encoding='utf8') as ff1:
    for i in range(len(lines)):
        if i%3==0:
            text=lines[i]
        elif i%3==1:
            trs=lines[i]
            if trs=='UNKNOWN': 
                print(text,file=ff1)
               
with open('vunknown.txt','r',encoding='utf8') as ff:
    bs=ff.read()
lines=bs.split('\n')
import os
readall=b''
for f in os.listdir('vMES/'):
    with open('vMES/'+f,'rb') as ff:
        readall+=ff.read()
from tqdm import tqdm
with open('vprefix.txt','w',encoding='utf8')   as ff:
    for i in tqdm(range(len(lines))): 
            text=lines[i]
            if text=='':continue
            print(text,file=ff) 
             
            idx=0
            collect=[]
            while True:
                idx=readall.find(text.encode('cp932')+b'\0',idx)
                if idx<=0:break
                idx+=len(text.encode('cp932'))
                #print(text,idx,idx+32)
                get=readall[idx:idx+32].hex().upper()
                if get not in collect:
                    collect.append(get)
                # if len(collect)==100:
                #      print(text)
                # if len(collect)>100:
                #      print(idx,len(readall))
            _extra=[] 
            for c in collect: 
                print('//'+c,file=ff)
                # rep=c.replace('3F','FF')
                # if rep not in collect and rep not in _extra:
                #     print('//'+rep,file=ff)
                #     _extra.append(rep)
                # rep=c.replace('46','F6')
                # if rep not in collect and rep not in _extra:
                #     print('//'+rep,file=ff)
                #     _extra.append(rep)
                     