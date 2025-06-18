from django.apps import AppConfig
from sklearn.feature_extraction.text import CountVectorizer
from keybert import KeyBERT
import jieba
from lyra.face_recogntion_fn import    load
class LyraAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lyra"

    def ready(self):
        LyraAppConfig.vectorizer =CountVectorizer(tokenizer=lambda text:jieba.lcut_for_search(text))
        LyraAppConfig.kw_model = KeyBERT(model='distiluse-base-multilingual-cased-v1')
        load();
        # known_face_list,known_face_encodes=load()
        # LyraAppConfig.known_face_list=known_face_list
        # LyraAppConfig.known_face_encodes=known_face_encodes
        
        # 可以将 `vectorizer` 存储在某个地方以便后续使用
        # 例如，将其存储在全局变量或通过 Django 信号传递
    @classmethod
    def get_vectorizer(cls)->CountVectorizer:
        return cls.vectorizer
    @classmethod
    def get_keyword_model(cls)->KeyBERT:
        return cls.kw_model
    
    @classmethod
    def get_known_face_list(cls):
        return cls.known_face_list
    
    @classmethod
    def get_known_face_encodes(cls):
        return cls.known_face_encodes