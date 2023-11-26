path=r'C:\dataH\AAAAAAAAAA\Jpn\data\script\solved'
import os
from collections import Counter
chars=''
for i,f in enumerate(os.listdir(path)):
    if i==0:print(f)
    with open(path+'/'+f,'r',encoding='utf8')  as ff:
        chars+=ff.read()
 
with open('../font/charset.utf8','r',encoding='utf8')  as ff:
    origin=ff.read()[:64*10]
origin+='｜'
added=list(set(chars)-set(origin))
cntchars=Counter(chars)
added.sort(key=lambda x:-cntchars[x])
origin+=''.join(list(added))

# origin=list(origin)
# for i in range(10*64,len(origin)):
#     if len(added)==0:break
#     if origin[i] not in chars:
#         origin[i]=added[0]
#         added=added[1:]
# origin=''.join(origin)
 

compoud=[]
for c in origin:
    if ord(c)>=0xe000 and ord(c)<60000:
        compoud.append('['+hex(ord(c))[2:].upper()+']= ')
print(len(origin))
with open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\sc3tools-main_pack\resources\yuno\charset.utf8','w',encoding='utf8')  as ff:
    ff.write(origin)
with open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\sc3tools-main_pack\resources\yuno\compound_chars.map','w',encoding='utf8')  as ff:
    ff.write('\n'.join(compoud))
with open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\mgsfontgen-dx-master\chn\charset.utf8','w',encoding='utf8')  as ff:
    ff.write(origin)
with open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\mgsfontgen-dx-master\chn\CompoundCharacters.tbl','w',encoding='utf8')  as ff:
    ff.write('\n'.join(compoud))