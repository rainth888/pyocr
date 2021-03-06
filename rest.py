# -*- coding: utf-8 -*-
import io
import os
import time

import cv2
import numpy as np
from flask import Flask, request, redirect, url_for,jsonify,render_template
# from flask_cors import CORS

from detector import Detector
detector = Detector('./ctpn/checkpoints','./ctpn/data/text.yml')
from recognizer import Recognizer
recoer = Recognizer('./crnn/labels/char_std_5990.txt', './crnn/models/weights_densenet.h5')

app = Flask(__name__)
app.results = []
app.config['UPLOAD_FOLDER'] = 'samples'
app.config["CACHE_TYPE"] = "null"
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'png', 'jpg', 'jpeg', 'gif'])
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024    # 1 Mb limit

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def get_cv_img(r):
    f = r.files['img']
    in_memory_file = io.BytesIO()
    f.save(in_memory_file)
    nparr = np.fromstring(in_memory_file.getvalue(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def process(img):
    start_time = time.time()
    rois, _, img = detector.detect(img)
    print("CTPN time: %.03fs" % (time.time() - start_time))
    from utilis import sort_box
    rois = sort_box(rois)
    start_time = time.time()
    ocr_result = recoer.recognize(img,rois)
    print("CRNN time: %.03fs" % (time.time() - start_time))

    # sorted_data = sorted(zip(rois, ocr_result), key=lambda x: x[0][1] + x[0][3] / 2)
    # rois, ocr_result = zip(*sorted_data)

    res = {"results": []}

    # error: numpy+json( raise TypeError(repr(o) + " is not JSON serializable"))
    # solution: numpy to int
    for key in ocr_result:
        roi = ocr_result[key][0]
        xs = (roi[0],roi[2],roi[4],roi[6])
        ys = (roi[1],roi[3],roi[5],roi[7])
        res["results"].append({
            'pos': (min(xs),min(ys),max(xs),max(ys)),
            'text': ocr_result[key][1]
        })
    return res

import json


@app.route('/ocr', methods=['POST'])
def ocr():
    if request.method == 'POST':
        img = get_cv_img(request)
        ret = process(img)
        return json.dumps(ret,encoding='utf-8', indent=2, ensure_ascii=False)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
