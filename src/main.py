import cv2 as cv
import numpy as np
import os

def is_in_key_region(x, y, p):
  return cv.pointPolygonTest(np.array([p[0], p[1], p[3], p[2]]), (x, y), True) > 0

class FingerPositionDetector(object):

  def __init__(self) -> None:
    # the key_regions corresponds to the regions of every keys
    self.key_regions = []
    if os.path.exists('key_regions.db'):
      self.key_regions = list(np.load('key_regions.db', allow_pickle=True))
    self.keycodes = [
      '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '+',
      'esc', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'backspace',
      'capslock', 'tab','a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', 'enter',
      'shift', '`', '\\', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', 'up', '?', 'shift',
      'ctrl', 'alt', 'fn', '[', ']', 'space', "'", 'left', 'down', 'right', 'del'
    ]

    if os.path.exists('finger_contour.db'):
      self._standard_contour = np.load('finger_contour.db', allow_pickle=True)

  def set_key_regions_interactively(self, sample_img):
    img = sample_img.copy()
    self.key_regions = []
    for i in range(5):
      points = []
      n = int(input(f"Input the number of key caps in row {i+1}, then start clicking in the image to input regions:"))
      cv.namedWindow(winname="Set key regions")

      j = 0
      def record_points(event, x, y, flags, param):
        nonlocal j
        if event == cv.EVENT_LBUTTONUP:
          if j >= 2 * (n + 1):
            print("This row is complete.")
            self.show_key_regions(img)
            return
          cv.circle(img, (x, y), 2, (0, 255, 0), thickness=-1)
          points.append([x, y])
          if (j + 1) % 2 == 0 and j != 1:
            self.key_regions.append(np.array([points[-4], points[-2], points[-3], points[-1]], dtype='int'))

          j = j + 1
      
      cv.setMouseCallback("Set key regions", record_points)

      while True:
        cv.imshow("Set key regions", img)
          
        if cv.waitKey(10) == 27:  # press esc
            break
      cv.destroyAllWindows()

    print("Inputted key regions: ", self.key_regions)
    np.array(self.key_regions).dump('key_regions_.db')

  def show_key_regions(self, img):
    img_ = img.copy()

    for p in self.key_regions:
      cv.line(img_, p[0], p[1], (255, 0, 0), thickness=2)
      cv.line(img_, p[1], p[3], (255, 0, 0), thickness=2)
      cv.line(img_, p[3], p[2], (255, 0, 0), thickness=2)
      cv.line(img_, p[2], p[0], (255, 0, 0), thickness=2)

    cv.imshow("Key cap regions", img_)

  def _get_key_regions(self, img):
    """Generate a list of images that are key caps of the virtual keyboard.

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

  def find_center(self, img):
    img_ = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    _, img_ = cv.threshold(img_, 127, 255, cv.THRESH_BINARY)
    # img_ = cv.Canny(img, 30, 130, L2gradient=True)
    contours, _ = cv.findContours(img_, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    contour = np.vstack(contours)
    M = cv.moments(contour)
    cX = int(M["m10"] / (M["m00"]+0.000001))
    cY = int(M["m01"] / (M["m00"]+0.000001))
    return (cX, cY)

    # contours_ = []
    # for c in contours:
    #   if cv.arcLength(c, closed=False) > 80:
    #     contours_.append(c)

    # min_dist = 99999.0
    # for c in contours_:
    #   dist = cv.matchShapes(self._standard_contour, c, cv.CONTOURS_MATCH_I1, 0)
    #   if dist < min_dist:
    #     min_dist = dist
    # cv.imshow('test', img_)

    # cv.drawContours(img, self._standard_contour, -1, (255, 0, 0))
    # cv.drawContours(img, contours_, -1, (0, 255, 0))
    # cv.imshow('test1', img)
    # cv.waitKey()
    # cv.destroyAllWindows()

    # return min_dist

  def get_key_code(self, img):
    center = self.find_center(img)

    for i, p in enumerate(self.key_regions):
      if is_in_key_region(center[0], center[1], p):
        return self.keycodes[i]

d = FingerPositionDetector()

img = cv.imread('keyboard_with_a_hand.jpg')

print(d.get_key_code(img))

cv.waitKey()
