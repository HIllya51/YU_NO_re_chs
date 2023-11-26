 
import requests 
import json,tqdm
import hashlib
import urllib
import random 
class TS( ):  
     
    def translate(self,query):  
         
        appid = '20151211000007653'
        secretKey = 'IFJB6jBORFuMmVGDRude'
        myurl = '/api/trans/vip/translate'

        fromLang = 'jp'
        toLang = 'zh'
        salt = random.randint(32768, 65536)
        q= query
        sign = appid + q + str(salt) + secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign
        
        res=requests.get('https://api.fanyi.baidu.com'+myurl)
        try:
            _='\n'.join([_['dst'] for _ in res.json()['trans_result']])  
             
            return _
        except:
            raise Exception(res.text)
ts=TS()
from common import fuhaos
with open('nots.txt','r',encoding='utf8') as ff:
    lines=ff.read().split('\n')
try:
    with open('baidu.json','r',encoding='utf8') as ff:
        ready=json.load(ff)
except:
    ready={}
for i in tqdm.trange(len(lines)):
    if len(lines)==0:continue
    if i%2==0:continue
    text=lines[i]
    if text in ready:
        continue
    elif set(text)-set(fuhaos)==set():
        trans=text
    else:
        trans=ts.translate(text)
    lines[i]=trans
    ready[text]=trans
    with open('baidu.json','w',encoding='utf8') as ff:
        ff.write(json.dumps(ready,ensure_ascii=False,indent=4))