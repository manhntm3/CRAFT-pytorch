from PIL import Image
from PIL import ImageFilter
import numpy as np

def preprocessing(img, basewidth = 1800, threshold = 0.35):
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS) 

    #convert to grayscale
    img = img.convert('LA')

    img = img.filter(ImageFilter.BoxBlur(2))
    #img = ImageEnhance.Contrast(img).enhance(8.0)
    #img = ImageEnhance.Brightness(img).enhance(0.7)
    #img = img.filter(ImageFilter.SHARPEN)

    v = np.median(img)
    sigma = 0.35
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))

    img = img.point(lambda p: p > lower and upper)

    #threshold = 140  
    #img = img.point(lambda p: p > threshold and 255) 
    
    return img

if __name__ == '__main__':
    abc = 1