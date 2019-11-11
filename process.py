# -*- coding: utf-8 -*-
import sys
import os
import time

import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.autograd import Variable

from PIL import Image

import cv2
from skimage import io
import numpy as np
import craft_utils
import imgproc
import file_utils
import json
import zipfile

from PIL import Image
import json
import timeit
import os
from PIL import ImageEnhance
from recognizer.parser import parse_email
from recognizer.parser import parse_phone
from recognizer.parser import parse_website
from recognizer.parser import parse_name
from recognizer.parser import parse_address
from recognizer.parser import parse_company
from recognizer.parser import parse_info
from utils import preprocessing
import pytesseract

from craft import CRAFT

from collections import OrderedDict
def copyStateDict(state_dict):
    if list(state_dict.keys())[0].startswith("module"):
        start_idx = 1
    else:
        start_idx = 0
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = ".".join(k.split(".")[start_idx:])
        new_state_dict[name] = v
    return new_state_dict

CONFIG = {
    'trained_model':'weights/craft_mlt_25k.pth',
    'text_threshold':0.7,
    'low_text':0.4,
    'link_threshold':0.4,
    'cuda':False,
    'canvas_size':1280,
    'mag_ratio':1.5,
    'poly':False,
    'show_time':False,
    'test_folder':'data/',
    'refine':False,
    'refiner_model':'weights/craft_refiner_CTW1500.pth'
}

""" For test images in a folder """
image_list, _, _ = file_utils.get_files(CONFIG['test_folder'])

result_folder = './result/'
if not os.path.isdir(result_folder):
    os.mkdir(result_folder)

def test_net(net, image, text_threshold, link_threshold, low_text, cuda, poly, refine_net=None):
    t0 = time.time()

    # resize
    img_resized, target_ratio, size_heatmap = imgproc.resize_aspect_ratio(image, CONFIG['canvas_size'], interpolation=cv2.INTER_LINEAR, mag_ratio=CONFIG['mag_ratio'])
    ratio_h = ratio_w = 1 / target_ratio

    # preprocessing
    x = imgproc.normalizeMeanVariance(img_resized)
    x = torch.from_numpy(x).permute(2, 0, 1)    # [h, w, c] to [c, h, w]
    x = Variable(x.unsqueeze(0))                # [c, h, w] to [b, c, h, w]
    if cuda:
        x = x.cuda()

    # forward pass
    y, feature = net(x)

    # make score and link map
    score_text = y[0,:,:,0].cpu().data.numpy()
    score_link = y[0,:,:,1].cpu().data.numpy()

    # refine link
    if refine_net is not None:
        y_refiner = refine_net(y, feature)
        score_link = y_refiner[0,:,:,0].cpu().data.numpy()

    t0 = time.time() - t0
    t1 = time.time()

    # Post-processing
    boxes, polys = craft_utils.getDetBoxes(score_text, score_link, text_threshold, link_threshold, low_text, poly)

    # coordinate adjustment
    boxes = craft_utils.adjustResultCoordinates(boxes, ratio_w, ratio_h)
    polys = craft_utils.adjustResultCoordinates(polys, ratio_w, ratio_h)
    for k in range(len(polys)):
        if polys[k] is None: polys[k] = boxes[k]

    t1 = time.time() - t1

    # render results (optional)
    render_img = score_text.copy()
    render_img = np.hstack((render_img, score_link))
    ret_score_text = imgproc.cvt2HeatmapImg(render_img)

    if CONFIG['show_time'] : print("\ninfer/postproc time : {:.3f}/{:.3f}".format(t0, t1))

    return boxes, polys, ret_score_text



def craftnet():
    # load net
    net = CRAFT()     # initialize

    print('Loading weights from checkpoint (' + CONFIG['trained_model'] + ')')
    if CONFIG['cuda']:
        net.load_state_dict(copyStateDict(torch.load(CONFIG['trained_model'])))
    else:
        net.load_state_dict(copyStateDict(torch.load(CONFIG['trained_model'], map_location='cpu')))

    if CONFIG['cuda']:
        net = net.cuda()
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = False

    net.eval()

    # LinkRefiner
    refine_net = None
    if CONFIG['refine']:
        from refinenet import RefineNet
        refine_net = RefineNet()
        #print('Loading weights of refiner from checkpoint (' + CONFIG['refiner_model'] + ')')
        if CONFIG['cuda']:
            refine_net.load_state_dict(copyStateDict(torch.load(CONFIG['refiner_model'])))
            refine_net = refine_net.cuda()
            refine_net = torch.nn.DataParallel(refine_net)
        else:
            refine_net.load_state_dict(copyStateDict(torch.load(CONFIG['refiner_model'], map_location='cpu')))

        refine_net.eval()
        CONFIG['poly'] = True

    t = time.time()

    # load data
    for k, image_path in enumerate(image_list):
        #print("Test image {:d}/{:d}: {:s}".format(k+1, len(image_list), image_path), end='\r')
        orig, image = imgproc.loadImage(image_path)

        bboxes, polys, score_text = test_net(net, image, CONFIG['text_threshold'], CONFIG['link_threshold'], CONFIG['low_text'], CONFIG['cuda'], CONFIG['poly'], refine_net)

        # save score text
        filename, file_ext = os.path.splitext(os.path.basename(image_path))
        mask_file = result_folder + "/res_" + filename + '_mask.jpg'
        cv2.imwrite(mask_file, score_text)

        file_utils.saveResult(image_path, image[:,:,::-1], polys, dirname=result_folder)

    information = []
    for file in os.listdir('result/temp_result'):
        filename = os.path.splitext(file)[0]
        extension = os.path.splitext(file)[1]
        if extension == '.tif':
            #!tesseract oem 13 --tessdata-dir ./result/ ./result/temp_result{filename}.png ./test/{filename+'-eng'} -l eng+vie
            image = Image.open('result/temp_result/'+file)

            config = '--psm 10 --oem 3 -l vie+eng'
            raw_text = pytesseract.image_to_string(image, lang = 'eng+vie', config = config)
            information.append(raw_text)

    X = {
        "name":[],
        "phone":[],
        "email":[],
        "company":[],
        "website":[],
        "address":[],
        "extra_information":[]
    }
    for i in range(len(information)):
        info = information[i]
        if parse_info(info):

            email_parse = parse_email(info)
            if email_parse != None:
                X["email"].append(email_parse)
                continue

            phone_parse = parse_phone(info)
            if phone_parse != None:
                X["phone"].append(phone_parse)
                continue

            website_parse = parse_website(info)
            if website_parse != None:
                X["website"].append(website_parse)
                continue

            company_parse = parse_company(info)
            if company_parse != None:
                X["company"].append(company_parse)
                continue

            address_parse = parse_address(info)
            if address_parse != None:
                X["address"].append(address_parse)
                continue

            name_parse = parse_name(info)
            if name_parse != None:
                X["name"].append(info)
                continue

            X["extra_information"].append(info)
    return X
