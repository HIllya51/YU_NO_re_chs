import json
from traceback import print_exc 
from common import fuhaos
def parseone(fname):
    with open(fname,'r',encoding='utf8') as ff:
        _extra=ff.read()
    
    xx={}
    all_=(_extra).split('\n')
    for i in range(len(all_)):

        text= all_[i]
        if i%3==0:
            orig=text
        elif i%3==1:
            trans=text 
            if text!='UNKNOWN':
                xx[orig]=trans
            else:
                #print(orig)
                pass
    return xx
xx=parseone('../unpack/vtext_trans.txt')
xx.update(parseone('../unpack/vtext_trans2.txt'))

xx['服装']='服装'
xx['手']='手'
xx['神帝']='神帝'
        
with open('../unpack/vtext_all.txt','r',encoding='utf8') as ff:
    lines=ff.read().split('\n')
for i in range(len(lines)-2):
    def parse(string):
        if len(string)==0:return
        if string not in xx:
            if len(set(string)-set(fuhaos))==0:
                xx[string]=string
        if '\u3000'==string[0]:
            try:
                xx[string]=xx[string[1:]]
            except:
                pass
    line=lines[i] 
    line1=lines[i+1]
    line2=lines[i+2]
    parse(line)
    parse(line1)
    parse(line2)
    try:
        if line1[0] not in '【】':
            #print(line,line1)
            xx[line+line1]=xx[line]+xx[line1]
            xx[line+'たくや'+line1]=xx[line]+'拓也'+xx[line1]
            if line2[0] not in '【】':
                #print(line,line1,line2)
                xx[line+line1+line2]=xx[line]+xx[line1]+xx[line2]
                xx[line+'たくや'+line1+line2]=xx[line]+'拓也'+xx[line1]+xx[line2]
                xx[line+line1+'たくや'+line2]=xx[line]+xx[line1]+'拓也'+xx[line2]
    except:
            print(line,line1,line2) 
            print_exc()
with open('map.json','w',encoding='utf8')  as ff:
    ff.write(json.dumps(xx,ensure_ascii=False,indent=4))

# for k in xx:
#     if xx[k]=='UNKNOWN':
#         print(k)