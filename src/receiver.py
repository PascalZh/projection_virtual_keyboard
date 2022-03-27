import cv2
import numpy as np
import requests

def get_image_from_esp_cam(url):
    res = requests.get(url, stream=True)
    bytes = b''  # 目前收到的二进制内容
    sep_bytes = b'\r\n--123456789000000000000987654321\r\nContent-Type: image/jpeg\r\nContent-Length: '
    next = -1
    for chunk in res.iter_content(chunk_size=1024):
        bytes += chunk
        next = bytes.find(sep_bytes, len(sep_bytes))
        if -1 != next:  # 说明有新的一帧到了
            start = bytes.find(b'\r\n', len(sep_bytes))
            bin_data = bytes[start+4:next]
            image = cv2.imdecode(np.frombuffer(bin_data, np.uint8),
                        cv2.IMREAD_UNCHANGED)
            yield image
            bytes = bytes[next:]
            next = -1
    res.close()

def show_video():
    for image in get_image_from_esp_cam('http://192.168.250.68:81/stream'):
        cv2.imshow('frame', image)  # 只是为了显示
        cv2.waitKey(1)

show_video()
