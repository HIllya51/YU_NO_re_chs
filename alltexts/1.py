import os

for f in os.listdir('en'):
    with open('en/'+f,'r',encoding='utf8') as ff:
        en=ff.read().split('\n')
    with open('ja/'+f,'r',encoding='utf8') as ff:
        ja=ff.read().split('\n')
    with open('zh/'+f,'r',encoding='utf8') as ff:
        zh=ff.read().split('\n')
 
    # if len(set((len(en),len(ja),len(zh))))!=1:
    #     print(f,(len(en),len(ja),len(zh)))
    #     continue
    with open('jazh/'+f,'w',encoding='utf8') as ff:
        for i in range(len(ja)):
            print('JA',ja[i], file=ff)
            #print(en[i], file=ff)
            print('ZH',zh[i], file=ff)
            print('', file=ff)