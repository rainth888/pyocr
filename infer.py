# -*- coding: UTF-8 -*-
from __future__ import print_function

#import glob
from glob import glob
import os
import argparse
import time

import cv2

import shutil
import numpy as np
from PIL import Image

from detector import Detector
detector = Detector('./ctpn/checkpoints','./ctpn/data/text.yml')
from recognizer import Recognizer
recoer = Recognizer('./crnn/labels/char_std_5990.txt', './crnn/models/weights_densenet.h5')

image_files = glob('./samples/*.*')

def process(img):
    start_time = time.time()
    rois, _, img = detector.detect(img)
    print("CTPN time: %.03fs" % (time.time() - start_time))
    from utilis import sort_box
    rois = sort_box(rois)
    start_time = time.time()
    ocr_result = recoer.recognize(img,rois)
    print("CRNN time: %.03fs" % (time.time() - start_time))

    sorted_data = sorted(zip(rois, ocr_result), key=lambda x: x[0][1] + x[0][3] / 2)
    rois, ocr_result = zip(*sorted_data)

    res = {"results": []}

    for i in range(len(rois)):
        res["results"].append({
            'position': rois[i],
            'text': ocr_result[i]
        })

    return res

if __name__ == '__main__':
    for image_file in sorted(image_files):
        image = np.array(Image.open(image_file).convert('RGB'))
        result = process(image)
        print(result)
