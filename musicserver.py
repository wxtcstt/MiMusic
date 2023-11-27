#-*- coding:utf8 -*-
import os
import sys
from flask import  Flask,request
from flask_cors import CORS
import tool 
import cache
from threading import Thread
import xiaoaiservice
import json
currpath=os.path.dirname(os.path.realpath(__file__))
app =  Flask(__name__,static_url_path='')
cors = CORS(app,resources = {r"/api/*":{"origins":"*"}})
cors = CORS(app,supports_credentials= True)
WifiIP=""
ServerPORT="15005"

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("收到文件上传")
        file = request.files['file']
        filename = request.form['filename']
        indexname,wakenames,author,puremusicname=tool.musicIndexName(filename)
        if indexname not in cache.music_index:
            savefilename='./static/music/'+indexname
            file.save(savefilename)
          
            duration=tool.get_duration(savefilename)
           
            for _name in wakenames:
                cache.music_collection[_name]=f"http://{WifiIP}:{ServerPORT}/music/{indexname}" 
            with open("./musicconfig",'a',encoding='utf8') as f :
                f.write(indexname+" " +",".join(wakenames)+" "+author+" "+puremusicname+" "+ str(duration)+"\n")  
            cache.music_index[indexname]={"author":author,"musicname":puremusicname,"duration":duration,"wakenames":wakenames}
            cache.musicurl_duration[f"http://{WifiIP}:{ServerPORT}/music/{indexname}"]=duration
        else:
            return "-1"
        return   json.dumps({"author":author,"musicname":puremusicname,"duration":duration},ensure_ascii=False)
    except Exception as e:
        print(e)
        return  "-1"
    
@app.route('/allmusics', methods=['GET'])
def allmusics():
    try:
        pageCurrent,pageSize=int(request.args.get("pageCurrent")),int(request.args.get("pageSize"))
        musics=[]
        i=0
        for values in cache.music_index.values():
            if i>=pageCurrent*pageSize and i<(pageCurrent+1)*pageSize:
                musics.append({"author":values["author"],"musicname":values["musicname"],"duration":values["duration"]})
            i+=1
           
        return json.dumps(musics,ensure_ascii=False)
    except Exception as e:
        print(e)
        return json.dumps([],ensure_ascii=False)
    
@app.route('/searchMusic', methods=['GET'])
def searchMusic():
    try:
        info=request.args.get("info")
        musics=[]
        for values in cache.music_index.values():
            author,musicname,duration=values["author"],values["musicname"],values["duration"]
            if info in author or info in musicname:
                musics.append({"author":values["author"],"musicname":values["musicname"],"duration":values["duration"]})
           
        return json.dumps(musics,ensure_ascii=False)
    except Exception as e:
        print(e)
        return json.dumps([],ensure_ascii=False)
    
@app.route('/deleteMusic', methods=['GET'])
def deleteMusic():
    try:
        request_musicname,request_author=request.args.get("musicname"),request.args.get("author")
        remainResult=[]
        deletekey=None
        deletewakenames=None
        for key,values in cache.music_index.items():
            author,musicname,duration,wakenames=values["author"],values["musicname"],values["duration"],values["wakenames"]
            if not (author==request_author and request_musicname==musicname):
               remainResult.append({"author":values["author"],"musicname":values["musicname"],"duration":values["duration"]})
            else:
               deletekey=key
               deletewakenames=wakenames
        if deletekey:
            cache.music_index.pop(deletekey)
            for key in deletewakenames:
               cache.music_collection.pop(key)  
            with open("./musicconfig",'w',encoding='utf8') as f :
                for indexname,values in cache.music_index.items():
                    author,puremusicname,duration,wakenames=values["author"],values["musicname"],values["duration"],values["wakenames"]
                    f.write(indexname+" " +",".join(wakenames)+" "+author+" "+puremusicname+" "+ str(duration)+"\n")  
                
        return json.dumps(remainResult,ensure_ascii=False)
    except Exception as e:
        print(e)
        return json.dumps([],ensure_ascii=False)
    

@app.route('/playMusic', methods=['GET'])
def playMusic():
    try:
        request_musicname,request_author=request.args.get("musicname"),request.args.get("author")
        cache.musicplayqueue.put((request_author,request_musicname))
        return "1"
    except Exception as e:
        print(e)
        return "-1"
@app.route('/musicNumber', methods=['GET'])
def musicNumber():
    try:
        return str(len(cache.music_index))
    except Exception as e:
        return "0"
    
def initMusicConfig(): 
    try:
        with open("./musicconfig",'r',encoding='utf8') as f :
            for line in f.readlines():
                linearray=line.split(" ")
                indexname,wakenames,author,musicname,duration=linearray[0].strip(),linearray[1].strip().split(","),linearray[2].strip(),linearray[3].strip(),linearray[4].strip()
                if indexname not in cache.music_index:
                 
                    for _name in wakenames:
                        cache.music_collection[_name]=f"http://{WifiIP}:{ServerPORT}/music/{indexname}"
                    cache.music_index[indexname]={"author":author,"musicname":musicname,"duration":float(duration),"wakenames":wakenames}
                    cache.musicurl_duration[f"http://{WifiIP}:{ServerPORT}/music/{indexname}"]=float(duration)
    except Exception as e:
        print(e)
                     
if __name__ =='__main__':
    try:
        WifiIP="192.168.0.107"  #此处用户必须修改为自己电脑的IP地址
        initMusicConfig()
        xiaoaithread=Thread(target=xiaoaiservice.appthread)
        xiaoaithread.start()
        print("web server started......")
        app.run(host='0.0.0.0',port=ServerPORT) 
    except Exception as e:
        print(e)
    except KeyboardInterrupt as e:
        print(e)




        
        


