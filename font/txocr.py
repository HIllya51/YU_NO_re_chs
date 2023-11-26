 
from hashlib import sha1
import requests,time,random,uuid,base64,hashlib
def ocrapi(imgfile):   
        def truncate(q):
            if q is None:
                return None
            size = len(q)
            return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


        def encrypt(signStr):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(signStr.encode('utf-8'))
            return hash_algorithm.hexdigest()
        APP_KEY = 　
        APP_SECRET = 　
        YOUDAO_URL = 'https://openapi.youdao.com/ocrapi'
        file = open(imgfile, 'rb')
        content = base64.b64encode(file.read()).decode('utf-8')
        file.close()

        data = {}
        data['img'] = content
        data['detectType'] = '10012'
        data['imageType'] = '1'
        data['langType'] = 'ja'
        data['docType'] = 'json'
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = APP_KEY + truncate(content) + salt + curtime + APP_SECRET
        sign = encrypt(signStr)
        data['appKey'] = APP_KEY
        data['salt'] = salt
        data['sign'] = sign

        headers = {'Content-Type': 'application/x-www-form-urlencoded'} 
        response =requests.post(YOUDAO_URL, data=data, headers=headers)
         
        try:
            _=[]
            for l in response.json()['Result']['regions']:
                _+=l['lines'] 
            print(''.join([l['text'] for l in _]))
        except:
            raise Exception(response.text)
 
for i in range(60):
    print(i)
    ocrapi(f'slice/{i}.png')