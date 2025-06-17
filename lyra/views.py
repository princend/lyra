import base64
import io
import requests
import pandas as pd
import pdfplumber
import docx
from django.shortcuts import render, redirect
from django.conf import settings
from django.apps import apps
from django.contrib.auth import authenticate, login
from django.contrib import messages

from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np

from lyra.face_recogntion_fn import recognize
# Spotify API credentials
client_id = settings.SPOTIFY_CLIENT_ID
client_secret = settings.SPOTIFY_CLIENT_SECRET


def get_access_token():
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(token_url, headers=headers, data=data)
    response_data = response.json()
    return response_data.get('access_token')

def search_spotify(query, access_token, market='TW'):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': query,
        'type': 'track,artist,album',
        'limit': 10,
        'market': market
    }
    response = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    return response.json()


def extract_text_from_file(file):
    text = ""
    file_extension = file.name.split('.')[-1]
    file_content = file.read()

    if file_extension == 'txt':
        text = file_content.decode('utf-8')
    elif file_extension == 'csv':
        df = pd.read_csv(io.BytesIO(file_content))
        text = df.to_string(index=False)
    elif file_extension == 'pdf':
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    elif file_extension == 'docx':
        doc = docx.Document(io.BytesIO(file_content))
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError("Unsupported file type")
    return text

def clean_text(text):
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    filtered_lines = [line for line in cleaned_lines if not line.startswith("#")]
    return "\n".join(filtered_lines)


 #取得關鍵字         
def analyze_text(text:str):
    try:
        MyAppConfig = apps.get_app_config('lyra')
        vectorizer = MyAppConfig.get_vectorizer()
        keyword_model=MyAppConfig.get_keyword_model()
        keywords = keyword_model.extract_keywords(text,vectorizer=vectorizer)
        keyword = keywords[0][0]
        return keyword
    except Exception as err:
        print('取得關鍵字錯誤',err) 

# deprecated
# def get_recommendations(track_id, access_token):
#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }
#     params = {
#         'seed_tracks': track_id,
#         'limit': 10
#     }
#     print("access_token",access_token)
#     print("trackid",track_id)
#     response = requests.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
    
#     print(response,"response")
#     return response.json()

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def search(request):
    if request.method == 'POST':   
        if 'upload' in request.POST:
            file = request.FILES.get('file')
            file_type= get_file_type(file)
            if file_type=='file':
                text = extract_text_from_file(file)
                cleaned_text = clean_text(text)
                analyzed_text = analyze_text(cleaned_text)
                access_token = get_access_token()

                if analyzed_text:
                    search_results = search_spotify(' '.join(analyzed_text), access_token)
                    if search_results['tracks']['items']:
                        first_track_id = search_results['tracks']['items'][0]['id']
                        print("break1")
                        # recommendations = get_recommendations(first_track_id, access_token)
                        recommendations=None
                        return render(request, 'results.html', {
                     'search_results': search_results,
                    #  'recommendations': recommendations,
                     'access_token': access_token
                })
                    else:
                        return render(request, 'index.html', {'error': "未能找到相關歌曲。"})
                else:
                    return render(request, 'index.html', {'error': "未能提取關鍵字。"})
            elif file_type=='image':
                file_bytes = file.read()
                npimg = np.frombuffer(file_bytes, np.uint8)
                image  = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
                MyAppConfig = apps.get_app_config('lyra')
                known_face_list = MyAppConfig.get_known_face_list()
                known_face_encodes = MyAppConfig.get_known_face_encodes()
                result= recognize(image,known_face_list,known_face_encodes,tolerance=0.6)
                singer_text = result
                access_token = get_access_token()
                if singer_text=='unknown' or singer_text==None:
                    return render(request, 'index.html',{'alert_message':'未能找到歌手'})
                elif singer_text :
                    search_results = search_spotify(' '.join(singer_text), access_token)
                    if search_results['tracks']['items']:
                        first_track_id = search_results['tracks']['items'][0]['id']
                        # recommendations = get_recommendations(first_track_id, access_token)
                        return render(request, 'results.html', {
                     'search_results': search_results,
                    #  'recommendations': recommendations,
                     'access_token': access_token
                })
            else:
                return  render(request, 'index.html', {'error': "未能找到檔案"})
        else:
            query = request.POST['query'].strip()
            if query:
                access_token = get_access_token()
                search_results = search_spotify(query, access_token)
                print("break1")
                # 確認是否需要取得推薦結果
                recommendations=None
                if search_results['tracks']['items']:
                    first_track_id = search_results['tracks']['items'][0]['id']
                    # recommendations = get_recommendations(first_track_id, access_token)
                else:
                    recommendations = None
                return render(request, 'results.html', {
                     'search_results': search_results,
                     'recommendations': recommendations,
                     'access_token': access_token
                })  
            else:
                return render(request, 'index.html', {'error': "未輸入關鍵字"})
    else:
        print('沒有關鍵字')
        return render(request, 'index.html')


# 取得檔案類型
def get_file_type(file ):
    file_name=file.name
    # 获取文件扩展名
    extension = file_name.rsplit('.', 1)[-1].lower()
    if extension in {'png', 'jpg', 'jpeg'}:
        return 'image'
    elif extension in {'csv', 'pdf', 'docx', 'txt'}:
        return 'file'
    else:
        return 'unknown'
    
# 打API取得歌手名稱    
def send_image_to_api(image_file):
    try:
        url = 'https://face-recognition-6hi5dai2gq-uc.a.run.app/predict'  
        files = {'image': image_file}
        response = requests.post(url, files=files)
        return response    
    except Exception as error:
        print('error is ',error)
        print('傳輸圖片檔案錯誤')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')  # 登入成功後導向首頁，可依需求修改
        else:
            messages.error(request, '帳號或密碼錯誤')
    return render(request, 'login.html')
        
