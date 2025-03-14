import cv2
import numpy as np
import json
import face_recognition 
import os
from django.conf import settings
import time

tolerance = 0.6    

def preprocessing_encode():
    # 读取JSON文件
    singer_json_path = os.path.join(settings.MEDIA_ROOT, 'json', 'singer-map.json')
    with open(singer_json_path, 'r',encoding='utf-8') as file:
        known_face_list = json.load(file)

    # 将encode字段改为None
    for face in known_face_list:
        face['encode'] = None

    # load image data by large model of face landmarks
    for data in known_face_list:
        print(data)
        try:
            image_filename = data['filename']
            image_path = os.path.join(settings.MEDIA_ROOT, 'known_singer_image', image_filename)
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encoding = face_recognition.face_encodings(img, model='small')[0]  # use small model of face landmarks
            data['encode'] = encoding.tolist()
        except Exception as error:
            print('data is ',data,'error is ',error )

    singer_map_with_encodings_json_path = os.path.join(settings.MEDIA_ROOT, 'json', 'singer-map-with-encodings.json')
    with open(singer_map_with_encodings_json_path, 'w', encoding='utf-8') as file:
        json.dump(known_face_list, file, ensure_ascii=False, indent=4)

    return known_face_list, [data['encode'] for data in known_face_list]
    
#辨認    
def recognize(img_input, known_face_list, known_face_encodes, tolerance=0.6) -> str:
    img = cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB)
    cur_face_locs = face_recognition.face_locations(img)
    cur_face_encodes = face_recognition.face_encodings(img, cur_face_locs, model='small')

    if not cur_face_encodes:
        return 'unknown'
    
    results = []
    for cur_face_encode in cur_face_encodes:
        face_distance_list = face_recognition.face_distance(known_face_encodes, cur_face_encode)
        min_distance_index = np.argmin(face_distance_list)
        if face_distance_list[min_distance_index] < tolerance:
            result = known_face_list[min_distance_index]['name']
        else:
            result = 'unknown'
        results.append(result)    
    
    if len(results)>=1:
       return results[0]
    elif len(results)==0:
       return 'unknown'
    
        
def load_encodings(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Convert lists back to numpy arrays
    for face in data:
        face['encode'] = np.array(face['encode'])
    
    known_face_list = data
    known_face_encodes = [face['encode'] for face in data]
    return known_face_list, known_face_encodes                   


# 預載入歌手 encoding表
def load():
    start_time = time.time()  # 記錄開始時間
    print('execute load funcion ')
    json_file = os.path.join(settings.MEDIA_ROOT, 'json', 'singer-map-with-encodings.json')
    # global known_face_list, known_face_encodes
    if not os.path.exists(json_file):
       print(f'{json_file} not found. Running preprocessing_encode...')
       known_face_list, known_face_encodes = preprocessing_encode()
    else:
        print(f'{json_file} found. Loading encodings...')
        known_face_list, known_face_encodes = load_encodings(json_file)
    end_time = time.time()  # 記錄結束時間
    execution_time = end_time - start_time  # 計算執行時間
    print(f'Load function executed in {execution_time:.2f} seconds')
    return known_face_list,known_face_encodes
        