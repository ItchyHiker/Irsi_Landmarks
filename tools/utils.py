import os
import numpy as np
import cv2
import torch
import torchvision.transforms as transforms

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

# Add missing import
from imgaug import Keypoint, KeypointsOnImage

def nms(dets, thresh, mode='Union'):
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    scores = dets[:, 4]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        if mode == "Union":
            ovr = inter / (areas[i] + areas[order[1:]] - inter)
        elif mode == "Minimum":
            ovr = inter / np.minimum(areas[i], areas[order[1:]])
        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]

    return keep

def convert_to_square(bbox):
    square_bbox = bbox.copy()
    h = bbox[:, 3] - bbox[:, 1]
    w = bbox[:, 2] - bbox[:, 0]
    max_side = np.maximum(h, w)
    square_bbox[:, 0] = bbox[:, 0] + w * 0.5 - max_side * 0.5
    square_bbox[:, 1] = bbox[:, 1] + h * 0.5 - max_side * 0.5
    square_bbox[:, 2] = square_bbox[:, 0] + max_side
    square_bbox[:, 3] = square_bbox[:, 1] + max_side

    return square_bbox

def IoU(box, boxes):
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

    xx1 = np.maximum(box[0], boxes[:, 0])
    yy1 = np.maximum(box[1], boxes[:, 1])
    xx2 = np.minimum(box[2], boxes[:, 2])
    yy2 = np.minimum(box[3], boxes[:, 3])

    w = np.maximum(0, xx2 - xx1)
    h = np.maximum(0, yy2 - yy1)

    inter = w * h
    ovr = np.true_divide(inter, (box_area + area - inter))

    return ovr

def convert_image_to_tensor(image):
    return transform(image)

def convert_chwTensor_to_hwcNumpy(tensor):
    if isinstance(tensor, torch.FloatTensor):
        return np.transpose(tensor.detach().numpy(), (0, 2, 3, 1))
    else:
        raise Exception("Convert b*c*h*w tensor to b*h*w*c numpy error. This tensor must have 4 dimensions of float data type.")

def show_landmarks(image, landmarks):
    for i in landmarks:
        cv2.circle(image, (i[0], i[1]), 1, (255, 0, 0), 0)
    cv2.imshow('img', image)
    cv2.waitKey(0)

def show_tensor_landmarks(image, landmarks):
    image = image.numpy()
    image = np.transpose(image, (1, 2, 0))
    image = 255 * (image * 0.5 + 0.5)
    image = np.clip(image, 0, 255).astype('uint8')
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    landmarks = landmarks.numpy()
    landmarks = landmarks.reshape((-1, 2))
    h, w = image.shape[0:2]
    for i in landmarks:
        cv2.circle(image, (int(w * i[0]), int(h * i[1])), 1, (255, 0, 0), 1)
        cv2.imshow('img', image)
    cv2.waitKey(0)

def draw_tensor_landmarks(image, pred_landmarks, gt_landmarks=None):
    image = image.numpy()
    image = np.transpose(image, (1, 2, 0))
    image = 255 * (image * 0.5 + 0.5)
    image = image.astype('uint8')
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    pred_landmarks = pred_landmarks.numpy()
    pred_landmarks = pred_landmarks.reshape((-1, 2))
    h, w = image.shape[0:2]
    for i in pred_landmarks:
        cv2.circle(image, (int(w * i[0]), int(h * i[1])), 1, (255, 0, 0), 0)
    if gt_landmarks is not None:
        gt_landmarks = gt_landmarks.numpy()
        gt_landmarks = gt_landmarks.reshape((-1, 2))
        for i in gt_landmarks:
            cv2.circle(image, (int(w * i[0]), int(h * i[1])), 1, (255, 255, 0), 0)
    return image

def show_bbox_landmarks(image, bbox, landmarks):
    bbox = [int(b) for b in bbox]
    cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 3)
    landmarks = [(int(landmarks[2 * i]), int(landmarks[2 * i + 1])) for i in range(len(landmarks) // 2)]
    for i in landmarks:
        cv2.circle(image, (i[0], i[1]), 1, (255, 0, 0), 0)
    cv2.imshow('img', image)
    cv2.waitKey(0)

class AverageMeter(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
       
