
with open('charset.txt','r',encoding='utf8') as ff:
    text=ff.read().split('\n')
collect=[]
for i in range(len(text)):
    if i%2==0:continue
    if len(text[i])!=64:
        print(i,text[i])
    for c in text[i]:
        _c=c
        # while c in collect:
        #     c=chr(ord(c)+1)
        # if _c!=c:
        #     print(_c,ord(_c),c,ord(c))
        collect+=[c]

compoud=[]
for c in collect:
    if ord(c)>=0xe000 and ord(c)<60000:
        #print(ord(c),c)
        compoud.append('['+hex(ord(c))[2:].upper()+']= ')
with open('charset.utf8','w',encoding='utf8')  as ff:
    ff.write(''.join(collect))
with open('compound_chars.map','w',encoding='utf8')  as ff:
    ff.write('\n'.join(compoud))
with open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\sc3tools-main\resources\yuno\charset.utf8','w',encoding='utf8')  as ff:
    ff.write(''.join(collect))
with open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\sc3tools-main\resources\yuno\compound_chars.map','w',encoding='utf8')  as ff:
    ff.write('\n'.join(compoud))