from PIL import Image
import numpy as np
import cv2
img=Image.open('origin/font.png')
print(dir(img))
print(img.size)
img=np.array(img)  
imgnew=np.array(Image.open(r'C:\Users\wcy\Documents\GitHub\YU_NO_re_chs\pack\mgsfontgen-dx-master\chn\FONT_A.png'))
imgnew[:48*10]=img[:48*10]
Image.fromarray(imgnew).save(r'C:\dataH\AAAAAAAAAA\Jpn\data\system\font.png')
Image.fromarray(imgnew).save(r'C:\dataH\AAAAAAAAAA\Jpn\data\system\font2.png')

# for i in range(h//48):

#     cv2.imwrite(f'slice2/{i}.png',img[i*48:i*48+48])
