import cv2 as cv
import numpy as np
import requests
import time

def get_image_from_esp_cam(url):
    i = 0
    while True:
        r = requests.get(url+'/capture')
        try:
            yield cv.imdecode(np.frombuffer(r.content, np.uint8), cv.IMREAD_COLOR)
        except Exception as e:
            print("Error when getting image from ESP, retrying the {}th time (max 10)".format(i+1))
            time.sleep(0.5)
            i = i + 1
            if i >= 10:
                raise e

def show_video():
    """For test"""
    for image in get_image_from_esp_cam('http://192.168.99.68'):
        cv.imshow('frame', image)  # 只是为了显示
        if cv.waitKey(10) == 27:  # press esc
            break

if __name__ == '__main__':
    show_video()
