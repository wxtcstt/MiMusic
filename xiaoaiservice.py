'''测试流式问答2'''
from miservice import MiAccount
from miservice import MiNAService
from aiohttp     import   ClientSession
from pathlib     import   Path
import os,json,asyncio,time
from http.cookies import SimpleCookie
from requests.utils import cookiejar_from_dict
from queue import Queue
from threading import Thread,Lock
import cache
import re
readlock=Lock()
askQueue=Queue(maxsize=1)
def get_last_timestamp_and_record(data):
        if "data" in data:
            d= data.get("data")
            records = json.loads(d).get("records")
            if not records:
                return 0, None
            last_record = records[0]
            timestamp = last_record.get("time")
            return timestamp, last_record["query"]
        else:
             return 0, None
def parse_cookie_string(cookie_string):
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    cookies_dict = {}
    cookiejar = None
    for k, m in cookie.items():
        cookies_dict[k] = m.value
        cookiejar = cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
    return cookiejar


Iservice=None
Ideviceid=""

async def main():
    global Iservice,Ideviceid
    is_gptmode=False
    
    try:
        #-------------------------用户配置
        hardware,user_id,password="L15A","179404957","wxtcstt321="
        wifispeaker_name="客厅小米音箱"
        LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
        COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"
        lastTimeStamp=int(time.time()* 1000)
        
        async with ClientSession() as session:
            account = MiAccount(session,user_id,password,os.path.join(str(Path.home()),".mi.token"),)
            await account.login("micoapi")
            service = MiNAService(account)#通过这个发送消息
            Iservice=service
            deviceresult = await service.device_list()
            if not isinstance(deviceresult, str):
                deviceid=None
                for h in deviceresult:
                  if h.get("name", "") == wifispeaker_name:
                    deviceid = h.get("deviceID")
                    Ideviceid=deviceid
                if not deviceid:
                    print("无法找到设备，已退出")
                print("deviceid:",deviceid)
                with open(os.path.join(str(Path.home()), ".mi.token")) as f:
                    user_data=json.loads(f.read())
                service_token=user_data.get("micoapi")[1]
                cookiestr=COOKIE_TEMPLATE.format(
                device_id=deviceid,
                service_token=service_token,
                user_id=user_id,
                )
                cookie = parse_cookie_string(cookiestr)
           
            async def get_if_xiaoai_is_playing(): #测试音乐播放
                        playing_info = await service.player_get_status(deviceid)
                        is_playing = (
                            json.loads(playing_info.get("data", {}).get("info", "{}")).get("status", -1) == 1
                        )
                        return is_playing       
            
           
            # songurl="http://192.168.0.104:15004/"+"xiangwo.flac"
            # await service.play_by_url(deviceid,songurl)    
            while True:
                r = await session.get(
                    LATEST_ASK_API.format(
                        hardware=hardware, timestamp=str(int(time.time()* 1000))
                    ),
                    cookies=parse_cookie_string(cookie))
                chatmsg=await r.json()
                new_timestamp, last_record = get_last_timestamp_and_record(chatmsg)
                # print("最后的问答：",last_record,end="\r")
               
                if last_record and new_timestamp>lastTimeStamp:
                    lastTimeStamp=new_timestamp
                    print("有新的提问出现...")
                    
                    if last_record=="大头模式" or last_record=="进入大头模式" :
                        is_gptmode=True
                        await service.text_to_speech(deviceid, "我爱大头")
                        await asyncio.sleep(0.5)
                        continue
                    elif last_record=="退出大头模式" or last_record=="退出大头" :
                        await service.text_to_speech(deviceid, "好的")
                        await asyncio.sleep(0.5)
                        is_gptmode=False
                        continue
                    if is_gptmode==True:
                        if   "停止" in last_record or "休息"==last_record or  "休息一下"==last_record or  "声音调到" in last_record and\
                            "关闭"== last_record or "停止回答" in last_record or "停止播放" in last_record :
                                message="GPT 清除历史消息"
                                continue        
                        elif  "播放" in  last_record:
                            prefixindex=last_record.find("播放")
                            songname=last_record[prefixindex+2:]
                            if songname:
                                if songname in cache.music_collection:
                                    await asyncio.sleep(1) 
                                    await service.text_to_speech(deviceid, "好的")
                                    await asyncio.sleep(0.5) 
                                    print("@@@@@@@@@@@@@播放音乐:",songname)
                                    songurl=cache.music_collection[songname]
                                    if songurl:
                                       await service.play_by_url(deviceid,songurl)  
                            continue 
                else:
                    try:
                        author,songname=cache.musicplayqueue.get_nowait()
                        songurl=""
                        if (author+"的"+songname) in cache.music_collection:
                            songurl=cache.music_collection[author+"的"+songname]
                        elif songname in cache.music_collection:
                            songurl=cache.music_collection[songname]
                        if songurl:
                            await service.play_by_url(deviceid,songurl)
                                                  
                    except Exception as e:
                        pass
                await asyncio.sleep(0.3)                 
    except Exception as e:
        print(e)
        
async def appmain():
    print(f"Starting Tasks: {time.strftime('%X')}")
    task1 = asyncio.create_task(main())
    #task2 = asyncio.create_task(loop_say_something())
    await task1
   # await task2
    print(f"Finished Tasks: {time.strftime('%X')}")


def  appthread():
    asyncio.run(appmain())
if __name__ == "__main__":
    asyncio.run(appmain())
   