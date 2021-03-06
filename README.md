# ESP32-CAM 使用注意事项
1.请保证模块输入电源至少5V 2A,否则图片会有几率出现水纹。
2.ESP32 GPIO32管脚控制摄像头电源，当摄像头工作时，请把GPIO32拉低。
3.由于IO0连接摄像头XCLK,使用时请把IO0悬空，请勿接高低电平。
4.出厂已含有默认固件，不另外提供下载，如需重烧其他固件请谨慎操作。
# 如何用ov2640看到980nm红外光
1. 首先买一个高通滤波片装到相机上，滤掉可见光。
2. 如果漫反射的红外光太弱，则可以通过**提高曝光时间、提高增益**的方式看到红外光。

# 参考资料

- [基于激光投影技术的虚拟键盘（硬件篇） - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/42963682)
- [Shape Matching using Hu Moments (C++ / Python) | LearnOpenCV](https://learnopencv.com/shape-matching-using-hu-moments-c-python/)
- [openCV Contours详解_huangjun2009的博客-CSDN博客_contours](https://blog.csdn.net/huangjun2009/article/details/89393527)
- [OpenCV——Canny边缘检测（cv2.Canny()）_m0_51402531的博客-CSDN博客_cv2.canny](https://blog.csdn.net/m0_51402531/article/details/121066693)

移除esp32-cam的ir filter，不过我买的没有ir filter：
- https://marksbench.com/electronics/removing-ir-filter-from-esp32-cam/