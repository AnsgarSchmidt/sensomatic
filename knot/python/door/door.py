from   picamera.array import PiRGBArray
from   picamera       import PiCamera
import numpy          as     np
import time
import cv2

def mse(imageA, imageB):
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

def init():
    for i in range(10):
        getImage()

def getImage():
    rawCapture           = PiRGBArray(camera)
    camera.capture(rawCapture, format="bgr")
    image                = rawCapture.array
    crop_img             = image[20:240, 300:520]
    #camera.close()
    return crop_img

camera               = PiCamera()
camera.awb_mode      = 'off'
camera.exposure_mode = 'auto'
camera.awb_gains     = 1.6
camera.brightness    = 48
camera.contrast      = 3
camera.iso           = 1234
init()
camera.exposure_mode = 'off'
normalimg            = getImage()

while True:
    img       = getImage()
    name      = "/mnt/door/door%d.png" % time.time()
    mseval    = mse(normalimg, img)
    normalimg = img
    font       = cv2.FONT_HERSHEY_SIMPLEX

    if mseval > 100:
        print mseval
        #cv2.putText(img,str(mseval),(0,23), font, 1,(0,0,0),2)
        cv2.imwrite(name, img)