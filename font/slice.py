from PIL import Image
import numpy as np
import cv2
img=Image.open('origin/font2.png')
print(dir(img))
print(img.size)
img=np.array(img)  
img[img[:,:,-1]==0]=0
img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
h,w,c=img.shape
cv2.imwrite(f'1.png',img )
# for i in range(h//48):

#     cv2.imwrite(f'slice2/{i}.png',img[i*48:i*48+48])
