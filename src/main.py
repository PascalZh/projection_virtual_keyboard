from time import sleep
import cv2 as cv
import numpy as np
import os
from receiver import get_image_from_esp_cam
import keyboard

def is_in_key_region(x, y, p):
  return cv.pointPolygonTest(np.array([p[0], p[1], p[3], p[2]]), (x, y), True) > 0

class FingerPositionDetector(object):

  def __init__(self) -> None:
    # 这个列表储存了所有的键区域，每个键区域是一个四边形，表示一个按键在图片中的范围
    # 每个键区域的格式为：[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]，其中[x1, y1]是左上角，[x2, y2]是右上角，[x3, y3]是左下角，[x4, y4]是右下角
    self.key_regions: list[np.ndarray] = []

    if os.path.exists('key_regions.db'):
      self.key_regions = list(np.load('key_regions.db', allow_pickle=True))

    self.key_codes = ['9', '8', '7', '6', '5', '4', '3', '2', '1']

    assert(len(self.key_codes) == len(self.key_regions))

    self.key_status = []  # 记录按键的状态，pressed_down表示按下，pressed_up表示抬起
    self.key_region_features = []
    for _ in range(len(self.key_codes)):
      self.key_status.append('pressed_up')
      self.key_region_features.append([])

  def set_key_regions_interactively(self, url):
    """通过鼠标操作，设置键区域

    Args:
        sample_img (opencv img): 测试用的图片
    """
    while True:
      i = 9 - int(input(f"请输入要修改的键区域（1-{len(self.key_codes)}, 0 to exit)："))
      if i == 9:
        break
      print("正在修改键{}的区域".format(self.key_codes[i]))
      print("请按左上、右上、左下、右下的顺序点击图片输入键帽的位置，然后按ESC键结束该行的输入")

      points = []
      cv.namedWindow(winname="Set key regions")

      j = 0
      def record_points(event, x, y, flags, param):
        nonlocal j
        if event == cv.EVENT_LBUTTONUP:
          if j >= 3:
            print("当前键区域已输入4个点，请按ESC键结束输入")
            points.append([x, y])
            print(points)
            self.key_regions[i] = np.array(points)
            return

          points.append([x, y])
          j = j + 1
      
      cv.setMouseCallback("Set key regions", record_points)
      
      for img in get_image_from_esp_cam('http://192.168.99.68'):
        # 将points画出来
        for p in points:
          cv.circle(img, p, 10, (0, 0, 255), thickness=2)
        self.show_key_regions(img)
        cv.imshow("Set key regions", img)

        if cv.waitKey(100) == 27:  # press esc
          break

      cv.destroyAllWindows()

      np.array(self.key_regions).dump('key_regions.db')

  def show_key_regions(self, img):
    """对图片修改，使其可以显示键区域"""

    for p in self.key_regions:
      cv.line(img, p[0], p[1], (255, 0, 0), thickness=2)
      cv.line(img, p[1], p[3], (255, 0, 0), thickness=2)
      cv.line(img, p[3], p[2], (255, 0, 0), thickness=2)
      cv.line(img, p[2], p[0], (255, 0, 0), thickness=2)

    return img

  def _get_key_regions(self, img):
    """生成一个包含所有键区域的列表

    Args:
        img (opencv image)
        key_regions (list[np.ndarray(dtype='int')]): a perspective is a quadrangle specified as four points: [top_left, top_right, bottom_left, bottom_right]
    """
    ret_imgs = []
    dst = np.array([[0, 0], [128, 0], [0, 128], [128, 128]], dtype='float32')
    for p in self.key_regions:
      M = cv.getPerspectiveTransform(p.astype('float32'), dst)
      ret_imgs.append(cv.warpPerspective(img, M, (128, 128)))
    return ret_imgs

  def calculate_center(self, img):
    """计算图片中手指的中心位置

    Args:
        img (opencv image): 图片

    Returns:
        tuple(float, float): 中心点的坐标
    """
    img_ = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    _, img_ = cv.threshold(img_, 127, 255, cv.THRESH_BINARY)
    # img_ = cv.Canny(img, 30, 130, L2gradient=True)
    contours, _ = cv.findContours(img_, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    if contours == ():
      return None
    contour = np.vstack(contours)
    M = cv.moments(contour)
    cX = int(M["m10"] / (M["m00"]+0.000000000001))
    cY = int(M["m01"] / (M["m00"]+0.000000000001))
    return (cX, cY)

  def update_key_status(self, img, calibrate_variance=False, log=False):
    """根据图片更新键的状态

    Args:
        img (opencv image): 
    """
    # 根据key_regions提取键区域
    key_regions = self._get_key_regions(img)
    for i in range(len(key_regions)):
      # 计算每个键区域的方差
      feature = np.var(key_regions[i])

      cv.imshow("9 Key regions", np.hstack(key_regions))
      print(f"Var_{self.key_codes[i]} = {feature}") if log else None

      if calibrate_variance:
        self.key_region_features[i].append(feature)
      else:
        if not self.stats_test(feature, i, log):
          self.key_status[i] = 'pressed_down'
          print(f"\033[33mkey code {self.key_codes[i]} pressed down\033[0m")
        else:
          self.key_status[i] = 'pressed_up'
        
  def stats_test(self, feature, i, log=False):
    print(self.stats[i]) if log else None
    critical_val = [0.40, 1.20, 1.10, 1.00, 1.96, 1.86, 1.50, 1.96, 1.40]  # 相应的数调低会使键更敏感、同时也更容易误触
    # corresponds to 9,    8,    7,    6,    5,    4,    3,    2,    1
    return abs((feature - self.stats[i][0])/self.stats[i][1]) < critical_val[i]  # 1.96 for 0.05 significance level
    
  def calculate_stats(self):
    self.stats = []
    for i in range(len(self.key_codes)):
      features = self.key_region_features[i]
      self.stats.append([np.mean(features), np.var(features)])

  def simulate_key_press(self):
    """模拟键盘按键"""
    for i in range(len(self.key_status)):
      if self.key_status[i] == 'pressed_down':
        keyboard.press(self.key_codes[i])
      else:
        keyboard.release(self.key_codes[i])

d = FingerPositionDetector()
# 把下面取消注释，可以用来设置键区域
d.set_key_regions_interactively('http://192.168.99.68'); exit(0)

calibrate_cnt = 0
for img in get_image_from_esp_cam('http://192.168.99.68'):
  print(f"\033[32m{calibrate_cnt} Calibrating... Don't touch or move!\033[0m") if calibrate_cnt < 20 else None
  if calibrate_cnt < 20:
    d.update_key_status(img, True)
    if calibrate_cnt == 19:
      d.calculate_stats()
  else:
    d.update_key_status(img, False)
    d.simulate_key_press()

  d.show_key_regions(img)

  cv.imshow("Capture", img)
  if cv.waitKey(100) == 27:
    break

  calibrate_cnt += 1
