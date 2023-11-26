#coding=utf8
import os,re,json,pykakasi
path=r'C:\dataH\AAAAAAAAAA\Jpn\data\script\txt' 
from common import castkata2hira,halfsolve,parsetokana,half,getinner,fuhaos,halfts

def splittext(string):
    _=(']' in string) + ('[' in string)
    #print(string,_,_%2)
    if _%2!=0:return [[string,1]]
    _save=[]
    i=0
    while i>=0 and i<len(string):
        if string[i]=='[':
            idx=string.find(']',i)
            token=string[i:idx+1]
            #print(token)
            if len(set(token)-set(half))==0:
                _save.append([token,1])
            else:
                if len(_save)==0:
                    _save.append([token,0])
                elif _save[-1][1]==0:
                    _save[-1][0]+=token
                else:
                    _save.append([token,0])
            i=idx+1
        else:
            idx=string.find('[',i)
            if idx>=0:
                token=string[i:idx]
            else:
                token=string[i:]
            #print(token)
            if len(_save)==0:
                _save.append([token,0])
            elif _save[-1][1]==0:
                _save[-1][0]+=token
            else:
                _save.append([token,0])
            i=idx
    #print(_save)
    return _save
def repair(text,string):
    string=getinner(string)
    starts='『《('
    ends='』》)。'
    if len(text)==0:return string
    addstart=''
    while len(text):
        c=text[0]
        if c in starts:
            text=text[1:]
            addstart=addstart+c
        else:
            break
    addends=''
    while len(text):
        c=text[-1]
        if c in ends:
            text=text[:-1]
            addends=c+addends
        else:
            break 
    # if len(addends+addstart):
    #     print(text,string)
    return addstart+string+addends

def toplain(string): 
     
    parsechange=[
        ('[ruby-base]',''),
        ('[ruby-text-start]','('),
        ('[ruby-text-end]',')'), 
    ]
    #[margin top="32"][color index="880000"]なお、持っているアイテム、宝玉の数はそのままで、宝玉セーブした場所へ行けるのが特徴である。[color index="800000"][%e] 
    #なお、持っているアイテム、宝玉の数はそのままで、宝玉セーブした場所へ行けるのが特徴である。
    #[margin top="32"][name]たくや[line]ベーシックな社会的価値観や、道徳は必ずと言っていいほど教えた。[%p]
    #ベーシックな社会的価値観や、道徳は必ずと言っていいほど教えた。
    #『そしてそれは、人類の新たな[ruby-base]終焉[ruby-text-start]しゅうえん[ruby-text-end]と始まりを意味するのだ‥‥。』[%p]
    #そしてそれは、人類の新たな終焉（しゅうえん）と始まりを意味するのだ‥‥。
    #[name]たくや[line][ruby-base]煩雑[ruby-text-start]はんざつ[ruby-text-end]って形容が、お似合いだな‥‥。[%p]
    #】煩雑（はんざつ）って形容が、お似合いだな‥‥。
    
    for pair in parsechange:
        string=string.replace(pair[0],pair[1])
    
    return string
with open('name.json','r',encoding='utf8')  as ff:
    names=json.load(ff)
    for k in names:
        if type(names[k])==list:
            names[k]=names[k][-1]
    names[':name:']=':name:'
with open('trans.json','r',encoding='utf8')  as ff:
    trans=json.load(ff)
    for k in trans:
        trans[k]=trans[k][0]
        if type(trans[k])==list:
            trans[k]=trans[k][-1]
        # if '(' in trans[k]:
        #    #print(k)
with open('baidu.json','r',encoding='utf8')  as ff:
    baidu=json.load(ff) 
#print(names)
allsplit=set()
notrans=[]
errorfile=[]
from collections import Counter
from tqdm import tqdm
for f in tqdm(os.listdir(path)): 
    if f.endswith('.scx.txt')==False:continue
    #if f!='yns_open.scx.txt':continue
    with open(path+'/'+f,'r',encoding='utf8') as ff:
        lines=ff.read().split('\n')
    
    for j in range(len(lines)):
        line=lines[j]  
        if '】' in line:
            continue
        splits=splittext(toplain(line))
       #print(splits)
        for i in range(len(splits)):
            if splits[i][1]==0:
                text_=splits[i][0]
                text=halfts(splits[i][0])
                
                #print("text",text,splits[i])
                if len(set(text)-set(fuhaos))==0:
                    pass
                elif text in names:
                    splits[i][0]=names[text]
                else: 
                   #print("text_",text_)
                    if text in trans:
                        splits[i][0]=repair(text_, trans[text])
                    else:
                        text=parsetokana(text)
                        if text in trans:
                            splits[i][0]=repair(text_, trans[text])
                        else: 
                                
                            if 'たくや' in text:
                                texts=text.split('たくや')
                                collect=[]
                                success=True
                                for t in texts:
                                    if t not in trans:
                                        success=False
                                        break
                                    else:
                                        collect.append(trans[t])
                                if success:
                                    splits[i][0]=repair(text_, '拓也'.join(collect))
                                else:
                                    notrans.append(f) 
                                    notrans.append(splits[i][0]) 
                                    errorfile.append(f)
                                    if splits[i][0] in baidu:
                                        splits[i][0]='JF|'+baidu[splits[i][0]]
                                    #notrans.append(text_) 
                                    #notrans.append(text) 
                            else: 
                                notrans.append(f) 
                                notrans.append(splits[i][0]) 
                                errorfile.append(f)
                                if splits[i][0] in baidu:
                                    splits[i][0]='JF:'+baidu[splits[i][0]]
                                #notrans.append(text_) 
                                #notrans.append(text) 
        try:
            lines[j]=''.join([_[0] for _ in splits])
        except:
            print(print(splits)) 
    # with open(path+'/'+f+'.txt','w',encoding='utf8') as ff:
    #     ff.write('\n'.join(lines))
    with open(os.path.dirname(path)+'/solved/'+f,'w',encoding='utf8') as ff:
        ff.write('\n'.join(lines))
with open('nots.txt','w',encoding='utf8') as ff:
    ff.write('\n'.join(notrans))
print(len(notrans),len(set(notrans)))
#print(Counter(errorfile))