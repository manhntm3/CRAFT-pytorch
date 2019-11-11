# -*- coding: utf-8 -*-
import os
import numpy as np
import cv2
import imgproc
from PIL import Image

# borrowed from https://github.com/lengstrom/fast-style-transfer/blob/master/src/utils.py
def get_files(img_dir):
    imgs, masks, xmls = list_files(img_dir)
    return imgs, masks, xmls

def list_files(in_path):
    img_files = []
    mask_files = []
    gt_files = []
    for (dirpath, dirnames, filenames) in os.walk(in_path):
        for file in filenames:
            filename, ext = os.path.splitext(file)
            ext = str.lower(ext)
            if ext == '.jpg' or ext == '.jpeg' or ext == '.gif' or ext == '.png' or ext == '.pgm':
                img_files.append(os.path.join(dirpath, file))
            elif ext == '.bmp':
                mask_files.append(os.path.join(dirpath, file))
            elif ext == '.xml' or ext == '.gt' or ext == '.txt':
                gt_files.append(os.path.join(dirpath, file))
            elif ext == '.zip':
                continue
    # img_files.sort()
    # mask_files.sort()
    # gt_files.sort()
    return img_files, mask_files, gt_files

def unique_pairs(n):
    for i in range(n):
        for j in range(n):
            yield i, j

def saveResult(img_file, img, boxes, dirname='./result/', verticals=None, texts=None):
        """ save text detection result one by one
        Args:
            img_file (str): image file name
            img (array): raw image context
            boxes (array): array of result file
                Shape: [num_detections, 4] for BB output / [num_detections, 4] for QUAD output
        Return:
            None
        """
        img = np.array(img)

        # make result file list
        filename, file_ext = os.path.splitext(os.path.basename(img_file))

        # result directory
        res_file = dirname + "res_" + filename + '.txt'
        res_img_file = dirname + "res_" + filename + '.jpg'

        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        rects = []
        for i, box in enumerate(boxes):
            poly = np.array(box).astype(np.int32).reshape((-1))
            poly = re_arr(poly)
            rects.append(poly)
        loop = True
        while loop:
            loop = False
            temp_rects = rects
            for i, j in unique_pairs(len(temp_rects)):
                rect1 = temp_rects[i]
                rect2 = temp_rects[j]
                if check_relativity(temp_rects[i],temp_rects[j]):
                    merge = merge_rect(temp_rects[i], temp_rects[j])
                    rects.insert(0,merge)
                    rects.remove(rect1)
                    rects.remove(rect2)
                    loop = True
                    break
        count = 0
        for rect in rects:
            temp = img[rect[1]:rect[7],rect[0]:rect[2]]
            im = Image.fromarray(temp)
            im.save('result/temp_result/'+str(count)+'.tif')
            count = count + 1
        with open(res_file, 'w') as f:
            for i, box in enumerate(boxes):
                poly = np.array(box).astype(np.int32).reshape((-1))
                poly = np.array(re_arr(poly))
                #rectangles.append(poly)
                strResult = ','.join([str(p) for p in poly]) + '\r\n'
                f.write(strResult)

                poly = poly.reshape(-1, 2)
                cv2.polylines(img, [poly.reshape((-1, 1, 2))], True, color=(0, 0, 255), thickness=2)
                ptColor = (0, 255, 255)
                if verticals is not None:
                    if verticals[i]:
                        ptColor = (255, 0, 0)

                if texts is not None:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.5
                    cv2.putText(img, "{}".format(texts[i]), (poly[0][0]+1, poly[0][1]+1), font, font_scale, (0, 0, 0), thickness=1)
                    cv2.putText(img, "{}".format(texts[i]), tuple(poly[0]), font, font_scale, (0, 255, 255), thickness=1)

        # Save result image
        cv2.imwrite(res_img_file, img)
        
        #cv2.imshow("asd",img)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
def merge_rect(rect1, rect2):
#     rect1 = rect1.reshape(-1, 2)
#     rect2 = rect2.reshape(-1, 2)
#     return np.concatenate((rect1, rect2), axis = 0)
    rect = []
    # top left x
    rect.append(min(rect1[0], rect1[6], rect2[0], rect2[6]))
    # top left y
    rect.append(min(rect1[1], rect1[3], rect2[1], rect2[3]))
    # top right x
    rect.append(max(rect1[2], rect1[4], rect2[2], rect2[4]))
    # top right y
    rect.append(min(rect1[1], rect1[3], rect2[1], rect2[3]))
    # bottom right x
    rect.append(max(rect1[2], rect1[4], rect2[2], rect2[4]))
    # bottom right y
    rect.append(max(rect1[5], rect1[7], rect2[5], rect2[7]))
    #bottom left x
    rect.append(min(rect1[0], rect1[6], rect2[0], rect2[6]))
    # bottom left y
    rect.append(max(rect1[5], rect1[7], rect2[5], rect2[7]))
    return rect


def is_closed(a, b, diff):
    if abs(a-b) <= diff:
        return True
    
def re_arr(poly):
    rect = []
    # top left x
    rect.append(min(poly[0],poly[2],poly[4],poly[6]))
    # top left y
    rect.append(min(poly[1],poly[3],poly[5],poly[7]))
    # top right x
    rect.append(max(poly[0],poly[2],poly[4],poly[6]))
    # top right y
    rect.append(min(poly[1],poly[3],poly[5],poly[7]))
    # bottom right x
    rect.append(max(poly[0],poly[2],poly[4],poly[6]))
    # bottom right y
    rect.append(max(poly[1],poly[3],poly[5],poly[7]))
    #bottom left x
    rect.append(min(poly[0],poly[2],poly[4],poly[6]))
    # bottom left y
    rect.append(max(poly[1],poly[3],poly[5],poly[7]))
    return rect
    
def check_relativity(rect1, rect2, closed_text_ratio = 0.5, line_difference_ratio = 0.5):
    # check if two boxes belong to one line
#    h0h1         h2h3   h0h1         h2h3
#    #################   #################
#    #               #   #               #
#    #  rectangle1   #   #   rectangle2  #
#    #               #   #               #
#    #################   #################
#    h6h7         h4h5   h6h7         h4h5  
    #
#
    height1 = rect1[5] - rect1[3]
    height2 = rect2[5] - rect2[3]
    
    mean_h = (height1 + height2) / 2
    
    if not is_closed(height1, height2, mean_h * line_difference_ratio):
        return False
    #check if the two boxes are in the same line
    if not is_closed(rect1[5], rect2[7], height1 * line_difference_ratio):
        return False
    #check if the distance between 2 boxes is not over  closed text ratio of height
    if not is_closed(rect2[6], rect1[4], closed_text_ratio * mean_h):
        return False
    return True
    
if __name__ == '__main__':
    x1 = [108, 244, 176, 244, 176, 269, 108, 269]
    x2 = [175, 241, 398, 241, 398, 267, 175, 267]
    print(check_relativity(x1,x2))
    print(merge_rect(x1,x2))
