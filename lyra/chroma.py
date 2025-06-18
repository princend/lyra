from typing import Collection
import chromadb
import json
from django.conf import settings
import os

chroma_client = chromadb.Client()

collection:Collection = chroma_client.create_collection(
    name="my_collection",
    metadata={"hnsw:space": "l2"} # l2 is the default,other choices are cosine ,ip
)

def storeToDb(known_face_list):
    print('store to db')
    try:
        json_file = os.path.join(settings.MEDIA_ROOT, 'json', 'singer-map-with-encodings.json')
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        encoded_vectors = [x['encode'] for x in data]
        metadatas = [{"name":x['name']} for x in known_face_list]
        ids = [str(i) for i,x in enumerate(known_face_list) ]
        collection.add(
            ids=ids,  # 給每個向量一個唯一的ID
            embeddings=encoded_vectors,
            metadatas=metadatas  # 可以為每個向量添加元數據
        )
        return collection
    except Exception as error:
        print("[storeToDb] error is ",error)
        raise error

# 查詢與指定向量最接近的向量
def query(face_encode:list):
    try:
        query_vector = face_encode  
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=1  # 查詢返回1個最相似的結果
        )
        return results
    except Exception as error:
        print("[test] error is ",error)
        raise error
   