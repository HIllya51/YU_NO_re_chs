#coding=utf8
import os,re,json,pykakasi
path=r'C:\dataH\AAAAAAAAAA\Jpn\data\script\txt'
from common import halfsolve,castkata2hira,parsetokana,halfts
 
from tqdm import tqdm
import json,re
def getxx(string):
        def findlast(ss):
            idx=0
            while True:
                _idx=ss.find('【',idx)
                if _idx<0:return idx
                idx=_idx+1

        if '】' in string:
            text= string[string.find('】')+1:]
            if '【' in string[:string.find('】')]:
                a=string[:string.find('】')]
                name=a[findlast(a):]
            else:
                name=None
            return name,text
        else:return None,string
     
with open('map.json','r',encoding='utf8') as ff:
    js=json.load(ff)
_name={}
trans={}
for k in tqdm(js):
    
        name,text=getxx(k)
        name2,ts=getxx(js[k])
        name,text=halfts(name),halfts(text)

        
        if name is None or name=="":
            pass
        elif name2 is None or name2=="":
            pass
        elif name not in _name:
            _name[name]=[name2]
        else:
            if name2 not in _name[name]:
                _name[name]+=[name2]
        if name:
            tp=(name,ts)
        else:
            tp=(ts,)
        if text is None or text=="":
            pass
        elif ts is None or ts=="":
            pass
        elif text not in trans:
            trans[text]=[tp]
        else:
            if tp not in trans[text]:
                trans[text]+=[tp]
        
        text=parsetokana(text)
        if text is None or text=="":
            pass
        elif ts is None or ts=="":
            pass
        elif text not in trans:
            trans[text]=[tp]
        else:
            if tp not in trans[text]:
                trans[text]+=[tp]
        
        if len(text)>1 and text[0]=='(' :
            text=text[1:]
        if len(text) and text[-1]==')':
            text=text[:-1]
        if len(text)>1 and text[0]=='《' :
            text=text[1:]
        if len(text) and text[-1]=='》':
            text=text[:-1]
        if len(text) and text[-1]=='。':
            text=text[:-1]

        if text is None or text=="":
            pass
        elif ts is None or ts=="":
            pass
        elif text not in trans:
            trans[text]=[tp]
        else:
            if tp not in trans[text]:
                trans[text]+=[tp]
        
             
# for name in trans:
#     if len(trans[name])==1:
#         trans[name]=trans[name][0]
with open('trans.json','w',encoding='utf8')  as ff:
    ff.write(json.dumps(trans,ensure_ascii=False,indent=4))

for name in _name:
    if len(_name[name])==1:
        _name[name]=_name[name][0]
if 0:   
    with open('name.json','w',encoding='utf8')  as ff:
        ff.write(json.dumps(_name,ensure_ascii=False,indent=4))
