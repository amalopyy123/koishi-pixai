#运行:python app.py
#常时运行，一直监听
from flask import Flask,render_template,url_for,request,make_response,jsonify 
import requests
from Pix_Chan import PixAI
import time
import math
import random
import json
from io import BytesIO
import base64
from settings import accounts,proxies 

app=Flask(__name__)

timeout_limit=300
pixai_items=[]

def init_pixai_items(sleep:int=0):
    for account in accounts:
        pixai_item = {
            'email':account["email"],
            'password':account["password"],
        }
        time.sleep(sleep)
        login(pixai_item)
        pixai_items.append(pixai_item)
def login(pixai_item):
    #pixai={}
    pixai=PixAI(pixai_item["email"], pixai_item["password"], login=True, proxy=proxies)
    pixai_item['pixai']=pixai
    pixai_item['login_time']=math.floor(time.time())
    pixai_item['is_locked']=False

def lock_availabe_pix_item():
    available_items=[]
    for pixai_item in pixai_items:
        if(pixai_item['login_time']+86400<time.time()):
            login(pixai_item)
        if(not pixai_item['is_locked']):
            available_items.append(pixai_item)
            pass
            
    if(len(available_items)==0):
        return None
    item=random.choice(available_items)
    item['is_locked']=True
    return item

def free_pix_item(pixai_item):
    pixai_item['is_locked']=False
    return None
def image_to_base64(image_url):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json",
        "Origin": "https://pixai.art",
        "Priority": "u=1, i",
        "Referer": "https://pixai.art/",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"128\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"128\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)  AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.1.0.0  Safari/537.36"
    }
    try:
        response = requests.get(image_url, stream=True,headers=headers,proxies=proxies)  # 使用stream=True以提高效率
        response.raise_for_status()  # 检查HTTP状态码，如果不是200，则抛出异常

        image = BytesIO(response.content)  # 将图片内容加载到 BytesIO 对象

        # 将 BytesIO 对象的内容编码为 Base64
        base64_image = base64.b64encode(image.getvalue()).decode('utf-8')
        return base64_image

    except requests.exceptions.RequestException as e:
        print(f"Failed to download image：{e}")
        return None
    except Exception as e:
        print(f"Failed to convert to base64：{e}")
    return None

@app.route('/generate',methods=['GET','POST'])
def generate():
    #获取当前时间戳
    #timestamp = time.time()
    if(request.method=='POST'):
        # json_data = request.get_json()
        # print("request json:")
        # print(json_data)
        # return jsonify(json_data), 200
        #print(type(request.data))
        #print(request.data)
        if not request.is_json:
            return jsonify({"error": "Invalid Content-Type, must be application/json"}), 400
        
        json_data = request.get_json() # same as request.json but can handle errors
        if json_data is None:
            return jsonify({"error": "Invalid JSON data"}), 400
        if not json_data['parameters']:
            return jsonify({"error": "Missing parameters"}), 400
            
        pix_item=lock_availabe_pix_item()
        if(not pix_item):
            return jsonify({"error": "Service Busy"}), 400
        
    #     parameters={
    #     "prompts": "Komeiji Koishi",
    #     "extra": {},
    #     "priority": 1000,
    #     "width": 512,
    #     "height": 768,
    #     "modelId": "1631191708426527449",
    #     "negativePrompts": "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry",
    #     "samplingSteps": 20,
    #     "samplingMethod": "Euler a",
    #     "cfgScale": 6,
    #     "seed": "",
    #     "clipSkip": 2,
    #     "controlNets": [],
    #     "lightning": False
    # }
        parameters=json_data['parameters']
        try:
            query_id=pix_item['pixai'].generate_image("",parameters=parameters)
            global timeout_limit
            time_current=0
            while True:
                media_ids=pix_item['pixai'].get_task_by_id(query_id)
                time_current+=15
                if media_ids or time_current>timeout_limit:
                    break
                time.sleep(15)       
            if time_current>timeout_limit:
                return jsonify({"error": "Timeout"}), 400
            if(not len(media_ids)):
                return jsonify({"error": "Can not retrive media ids"}), 400
            free_pix_item(pix_item)
            img_url=pix_item['pixai'].get_media(media_ids[0])
            base64_data=image_to_base64(img_url)
            resp = make_response(base64_data, 200)
            return resp
        except Exception as e:
            free_pix_item(pix_item)
            print(e)
            return make_response(e, 400)
    else:
        resp = make_response("Invalid Method", 400)
        resp.headers['X-Something'] = 'Invalid Invalid Method'
        return resp

if  __name__=='__main__':
    pass
    init_pixai_items(sleep=4)
    app.run(host='0.0.0.0',port=5000,debug=False)

def test():
    init_pixai_items()
    pix_item=lock_availabe_pix_item()
    print(pix_item['email'])
    if(pix_item):
        parameters={
        "prompts": "Komeiji Koishi",
        "extra": {},
        "priority": 1000,
        "width": 512,
        "height": 768,
        "modelId": "1631191708426527449",
        "negativePrompts": "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry",
        "samplingSteps": 20,
        "samplingMethod": "Euler a",
        "cfgScale": 6,
        "seed": "",
        "clipSkip": 2,
        "controlNets": [],
        "lightning": False
    }
        query_id=pix_item['pixai'].generate_image("",parameters=parameters)
        while True:
            media_ids=pix_item['pixai'].get_task_by_id(query_id)
            if media_ids:
                break
            time.sleep(10)
        for media_id in media_ids:
            #https://images-ng.pixai.art/images/orig/313b290d-005f-4de6-8225-76571053192d
            print(pix_item['pixai'].get_media(media_id))
        free_pix_item(pix_item)
#run()
#exit()