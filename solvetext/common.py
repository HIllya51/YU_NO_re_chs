#coding=utf8
half=' ()[]1234567890!@#$%^&*_+-=,./?;:\'"`~qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
QUAN='　（）［］１２３４５６７８９０！＠＃＄％＾＆＊＿＋－＝，．／？；：＇＂｀～ｑｗｅｒｔｙｕｉｏｐａｓｄｆｇｈｊｋｌｚｘｃｖｂｎｍＱＷＥＲＴＹＵＩＯＰＡＳＤＦＧＨＪＫＬＺＸＣＶＢＮＭ'
fuhaos=half+QUAN+'。，、；’：“”‘！？【】『』'
castkata2hira=str.maketrans('ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ','ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ')
halfsolve=str.maketrans(QUAN,half)
def getinner(text):
    starts='『《('
    ends='』》)。'
    while len(text):
        if text[0] in starts:
            text=text[1:]
        else:break
    while len(text):
        if text[-1] in ends:
            text=text[:-1]
        else:break
    return text

def halfts(string):
    if string is None:return None 
    if len(string)==0:return string
    parsechange=[ 
     
        ('なんだか','ちょっと'),
        ('なるのさ','なった'),
        ('ている','てる'),   
        ('学生','生徒'),  
        ('いやいや','いや'),
        ('やらいう','いう'),   
    ] 
    for pair in parsechange:
        string=string.replace(pair[0],pair[1]) 
    string= string.translate(castkata2hira).translate(halfsolve)
    return getinner(string)
 
import fugashi
tagger = fugashi.Tagger("-Owakati") 
def parse_2(string:str):
    nodes=tagger.parseToNodeList(string)
    _=[]
    for node in nodes:
        if set(node.surface)-set(fuhaos)==set():
            _.append(node.surface)
        else:
            if node.feature.kana:
                _.append(node.feature.kana)
            else:
                _.append(node.surface)
   
    return ''.join(_)
    
def parsetokana(string:str):
    strings=string.split(' ')
    _=[]
    for string in strings:
        _.append(parse_2(string))
    return (' '.join(_)).translate(castkata2hira)
if __name__=='__main__':
    print(parsetokana('ぐっすりと‥‥そう‥‥そうよ。'))