import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../models/research/"))


import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
import requests
from object_detection.utils import label_map_util
from datetime import datetime


MODEL_ROOT = os.path.join(os.path.dirname(__file__), "../model_weights/ssd_mobilenet_v1_coco_11_06_2017/")
MODEL_PATH = os.path.join(MODEL_ROOT, "frozen_inference_graph.pb")
LABEL_PATH = os.path.join(MODEL_ROOT, "mscoco_label_map.pbtxt.txt")
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "static/_images")
IMAGE_SIZE = 150
NUM_CLASSES = 90

label_map = label_map_util.load_labelmap(LABEL_PATH)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
CATEGORY_INDEX = label_map_util.create_category_index(categories)

GRAPH = tf.Graph()
with GRAPH.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(MODEL_PATH, "rb") as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name="")


def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)


def cut(image, boxes, scores, classes, category_index, min_score_thresh=0.7):
    result = ()
    size = (IMAGE_SIZE, IMAGE_SIZE)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + size, fill=255)

    for i, s in enumerate(scores):
        if s > min_score_thresh:
            box = tuple(boxes[i].tolist())
            ymin, xmin, ymax, xmax = box

            im_width, im_height = image.size
            (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                          ymin * im_height, ymax * im_height)

            croped = image.crop((left, top, right, bottom))
            length = min(croped.size)
            (left, right, top, bottom) = ((im_width - length) / 2, (im_width + length) / 2,
                                          (im_height - length)/2, (im_height + length)/2)
            croped = image.crop((left, top, right, bottom))  # to square
            croped.thumbnail(size, Image.ANTIALIAS)
            name = category_index[classes[i]]["name"]
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            path = os.path.join(IMAGE_PATH, "{}_{}.png".format(timestamp, name))
            masked = ImageOps.fit(croped, mask.size, centering=(0.5, 0.5))
            masked.putalpha(mask)
            masked.save(path)
            result = (path, name)
    return result


def detect_kemono(image_url, rotate=False):
    r = requests.get(image_url)
    if not r.ok:
        return []
    
    image = Image.open(BytesIO(r.content)).convert("RGB")
    if rotate:
        image = image.rotate(-90)

    with tf.Session(graph=GRAPH) as sess:
        image_tensor = GRAPH.get_tensor_by_name("image_tensor:0")
        detection_boxes = GRAPH.get_tensor_by_name("detection_boxes:0")
        detection_scores = GRAPH.get_tensor_by_name("detection_scores:0")
        detection_classes = GRAPH.get_tensor_by_name("detection_classes:0")
        num_detections = GRAPH.get_tensor_by_name("num_detections:0")

        image_np = load_image_into_numpy_array(image)
        image_np_expanded = np.expand_dims(image_np, axis=0)
        (boxes, scores, classes, num) = sess.run(
            [detection_boxes, detection_scores, detection_classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})

        return cut(image, np.squeeze(boxes), np.squeeze(scores), np.squeeze(classes), CATEGORY_INDEX)
