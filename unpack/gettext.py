import os
import re
allfound=[]
for f  in os.listdir('vTXT'):
    with open('vTXT/'+f,'r',encoding='cp932') as ff:
        text=ff.read()
    found1=re.findall('#1-TEXT',text)
    found=re.findall('#1-TEXT\n\\[\n    "(.*?)"\n\\]',text)
    if(len(found1)!=len(found)):
        print(f)
    _=[]
    for _1 in found:
        if _1 in ['【',
                  '　　　　　　　　　　　　　▼',
                  '　　　　　　　　　　　　▼']:
            continue 
        else:
            _.append(_1)
    allfound=allfound+_

with open('vtext.txt','w',encoding='utf8') as ff:
    ff.write('\n'.join(list(set(allfound))))

import os
import re
allfound=[]
for f  in os.listdir('vTXT'):
    with open('vTXT/'+f,'r',encoding='cp932') as ff:
        text=ff.read()
    found1=re.findall('#1-TEXT',text)
    found=re.findall('#1-TEXT\n\\[\n    "(.*?)"\n\\]',text)
    if(len(found1)!=len(found)):
        print(f)
    _=[]
    for _1 in found:
        if _1 in [
                  '　　　　　　　　　　　　　▼',
                  '　　　　　　　　　　　　▼']:
            continue 
        else:
            _.append(_1)
    allfound=allfound+_

with open('vtext_all.txt','w',encoding='utf8') as ff:
    ff.write('\n'.join(list((allfound))))