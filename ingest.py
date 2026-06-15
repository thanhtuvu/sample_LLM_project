import requests
from elasticsearch import Elasticsearch
import elasticsearch

def load_faq_data():
    faq_url = 'https://datatalks.club/faq/json/courses.json'
    faq_data = requests.get(faq_url).json()

    faq_content = []
    prefix = 'https://datatalks.club/faq'

    for i in faq_data:
        course_url = f'{prefix}{i['path']}'
        course_faq_content = requests.get(course_url).json()
        faq_content.extend(course_faq_content)

    return faq_content

