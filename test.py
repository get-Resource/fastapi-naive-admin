import json

import cv2
import numpy as np
from paddleocr import PaddleOCR

# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

def preprocess_image(image_path):
    # 读取图片
    image = cv2.imread(image_path)
    
    # 图像增强：调整亮度和对比度
    alpha = 1.5  # 对比度系数
    beta = 30    # 亮度系数
    enhanced_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    
    # 转换为灰度图
    gray_image = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2GRAY)
    
    # 使用高斯模糊去噪
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    
    return blurred_image

def extract_text(image):
    result = ocr.ocr(image, cls=True)
    text_info = []
    print(result)
    for line in result:
        text_info.append(line[1][0])
    return text_info

def parse_data(text_info):
    data = {
        "品牌": "",
        "车型": "",
        "制造国": "",
        "发动机型号": "",
        "发动机排量": "",
        "最大总质量": "",
        "乘坐人数": "",
        "生产厂商": "",
        "制造厂专用号": "",
        "制造年月": "",
        "车辆识别代号": ""
    }
    print(text_info)
    for text in text_info:
        if "品牌" in text:
            data["品牌"] = text.split(" ")[1]
        elif "车型" in text:
            data["车型"] = text.split(" ")[1]
        elif "制造国" in text:
            data["制造国"] = text.split(" ")[1]
        elif "发动机型号" in text:
            data["发动机型号"] = text.split(" ")[1]
        elif "发动机排量" in text:
            data["发动机排量"] = text.split(" ")[1]
        elif "最大总质量" in text:
            data["最大总质量"] = text.split(" ")[1]
        elif "乘坐人数" in text:
            data["乘坐人数"] = int(text.split(" ")[1])
        elif "生产厂商" in text:
            data["生产厂商"] = text.split(" ")[1]
        elif "制造厂专用号" in text:
            data["制造厂专用号"] = text.split(" ")[1]
        elif "制造年月" in text:
            data["制造年月"] = text.split(" ")[1]
        elif "车辆识别代号" in text:
            data["车辆识别代号"] = text.split(" ")[1]
    
    return data

def main(image_path):
    preprocessed_image = preprocess_image(image_path)
    text_info = extract_text(preprocessed_image)
    structured_data = parse_data(text_info)
    print(json.dumps(structured_data, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    image_path = r'nameplate\1190719A33481_0105.jpg'  # 替换为你的图片路径
    main(image_path)