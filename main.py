import base64
import json
import profile
from fastapi import FastAPI, File, UploadFile, responses
from fastapi.responses import StreamingResponse
from mcstatus import MinecraftServer, MinecraftBedrockServer
import requests
from pydantic import BaseModel
import math
import sys
import yaml
import os

server = FastAPI()

class SkinFetch():

    __status: bool = False
    __playerID: str = ""
    __UUID: str = ""
    __profileB64: str = ""
    __profile: str = ""
    __skinURL: str = ""

    def __init__(self, playerID) -> None:
        self.__playerID = playerID
        pass

    def getUUID(self):
        url = "https://api.mojang.com/users/profiles/minecraft/"+self.__playerID
        reply = requests.get(url)
        if reply.status_code == 200:
            dict_data = json.loads(reply.text)
            self.__UUID = dict_data["id"]
            self.__status = True
        else:
            self.__status = False
    
    def getProfile(self):
        url = "https://sessionserver.mojang.com/session/minecraft/profile/"+self.__UUID
        reply = requests.get(url)
        dictData = json.loads(reply.text)
        self.__profileB64 = dictData["properties"][0]["value"]
        return self.__profileB64
    
    def decodeProfile(self):
        self.getProfile()
        profile = base64.b64decode(self.__profileB64)
        profile = profile.decode().replace(" ", "").replace("\n", "")
        self.__profile = profile
        return self.__profile
    
    def skinUrl(self):
        self.decodeProfile()
        self.__skinURL = json.loads(self.__profile)["textures"]["SKIN"]["url"]
        return self.__skinURL

    def getImg(self):
        self.skinUrl()
        url = self.__skinURL
        reply = requests.get(url)
        img = reply.content
        path = "/home/deer/viceDisk/api/cache/"+self.__playerID+".png"
        with open(path, "wb") as f:
            f.write(img)
        pass

    def playerExsist(self):
        return self.__status

class McServer():
    __JAVA = 0
    __BE = 1

    __online: bool = False
    __type: int = -1
    __players: int = -1
    __max: int = -1
    __playerList: list = []
    __version: str
    __ping: int

    def __init__(self, addr) -> None:
        self.serverAddr = addr
        try:
            self.server = MinecraftServer.lookup(self.serverAddr)
            self.status = self.server.status()
            self.__type = self.__JAVA
            self.__online = True
        except:
            try:
                self.server = MinecraftBedrockServer.lookup(self.serverAddr)
                self.status = self.server.status()
                self.__type = self.__BE
                self.__online = True
            except:
                self.__online = False
                pass
        self.__players = self.status.players.online
        self.__max = self.status.players.max
        self.__playerList = self.status.players.sample
        self.__version = self.status.version.name
        self.__ping = int(self.status.latency)
        pass

    def isOnline(self) -> bool:
        return self.__online

    def getType(self) -> str:
        if self.__type == self.__JAVA:
            return "Java"
        else:
            return "Bedrock"
    
    def getPlayers(self) -> int:
        return self.__players

    def getMax(self) -> int:
        return self.__max
    
    def getList(self )-> list:
        return self.__playerList
    
    def getVersion(self )-> str:
        return self.__version

    def getPing(self )-> int:
        return self.__ping
    


@server.get("/")
async def root():
    return {"message": "Hello, this is Deer's API.", 
            "more_info": "For more information you can visit http://blog.deercloud.site"}

@server.get("/mc")
async def mcHelp():
    return {"message": "Some apis about MineCraft.", 
            "usable": ["http://blog.deercloud.site/api/mc/isonline/<Server Address>",
                        "http://blog.deercloud.site/api/mc/howmany/<Server Address>",
                        "http://blog.deercloud.site/api/mc/list/<Server Address>"]}


@server.get("/mc/isonline/")
async def isMcOnline(addr: str):
    s = McServer(addr)
    return {"isOnline": s.isOnline()}

@server.get("/mc/howmany/")
async def mcPlayers(addr: str, type: str = "json"):
    s = McServer(addr)
    if s.isOnline:
        return {"players": s.getPlayers()}
    else:
        return {"err": "server is offline"}

@server.get("/mc/list/")
async def playerList(addr: str):
    s = McServer(addr)
    if s.isOnline:
        return {"playerList": s.getList()}
    else:
        return {"err": "server is offline"}

@server.get("/mc/bandge/")
async def getBandge(addr: str):
    s = McServer(addr)
    resp = {
        "schemaVersion": 1,
        "label": "在线人数：",
        "message": str(s.getPlayers),
        "color": "rgba(135,206,250,0.65)",
        "labelColor": "rgba(32,178,170,0.8)",
    }
    if s.isOnline:
        return resp
    else:
        resp["label"] = "服务器状态："
        resp["message"] = "离线"
        return resp

@server.get("/mc/getskin/{playerID}")
async def getSkin(playerID: str):
    skin = SkinFetch(playerID)
    skin.getUUID()
    if skin.playerExsist():
        skin.getImg()
        path = "/home/deer/viceDisk/api/cache/"+playerID+".png"
        skin = open(path, "rb")
        return StreamingResponse(skin, media_type="image/png")
    else:
        return {"error": "Can't access Mojiang server or no such user!"}

class Item(BaseModel):
    Data: dict = None

#192.168.163.235:8000/api/eccom/tfapp/aifactory/eventpost
@server.post("/eccom/tfapp/aifactory/eventpost")
async def eventpost(item: Item):
    print(item)
    return {"success": "Online!",
            "item": item}


def findResidenceSavePath(serverRootPath: str, worldName: str) -> str:
    """
    根据需要生成领地存档文件的地址。
    :param serverRootPath:服务器根目录
    :param worldName:需要操作的世界
    :return: 对应存档文件地址
    """
    print("|正在查找领地存档文件。")
    resWorldYml = "res_" + worldName + ".yml"
    path = os.path.join(serverRootPath, "plugins/Residence/Save/Worlds", resWorldYml)
    # noinspection PyBroadException
    try:
        file = open(path, 'r', encoding="utf-8")
        file.close()
        print("|成功：领地存档地址为" + path)
    except:
        print("|错误：未找到配置文件，请确认已安装领地插件？")
        sys.exit("程序终止。")
    return path


def getResidencesArea(residenceSavePath: str) -> list:
    """
    获取领地配置文件中领地的区域两点坐标。
    :param residenceSavePath: 配置文件的位置
    :return: 所有领地区域的两点坐标（列表）
    """
    print("|正在分析配置文件。")
    resAreas: list = []

    resSaveFile = open(residenceSavePath, 'r', encoding="utf-8")
    resSaveData = resSaveFile.read()
    resSaveFile.close()

    resData = list(yaml.load(resSaveData, Loader=yaml.FullLoader)["Residences"].values())
    for residence in resData:
        coordinatesStrList = list(residence["Areas"].values())[0].split(':')
        resAreaCoordinate: dict = {"x1": int(coordinatesStrList[0]), "x2": int(coordinatesStrList[3]),
                                   "y1": int(coordinatesStrList[1]), "y2": int(coordinatesStrList[4]),
                                   "z1": int(coordinatesStrList[2]), "z2": int(coordinatesStrList[5])}
        resAreas.append(resAreaCoordinate)
    print("|共找到：" + str(len(resAreas)) + " 个领地。")
    return resAreas


def convertAreaToChunk(residenceAreaList: list) -> list:
    """
    将区域坐标转换为区块坐标。
    :param residenceAreaList: 领地区域两点（列表）
    :return: 有效的区块区域两点坐标（列表）
    """
    print("|正在将领地坐标转换为区块区域。")
    resChunks: list = []
    square: int = 0
    for area in residenceAreaList:
        chunkCoordinate: dict = {"x1": math.ceil(area["x1"] / 16), "x2": math.ceil(area["x2"] / 16),
                                 "z1": math.ceil(area["z1"] / 16), "z2": math.ceil(area["z2"] / 16)}
        resChunks.append(chunkCoordinate)
        square += abs(chunkCoordinate["x1"] - chunkCoordinate["x2"]) * abs(
            chunkCoordinate["z1"] - chunkCoordinate["z2"])
    print("|共有：" + str(square) + "个有效区块。")
    return resChunks

@server.get("/mc/isSafe/{pos}")
async def isSafe(pos:int, x:int, z:int):
    print(x,z)
    res_path = findResidenceSavePath("/home/deer/viceDisk/mcserver/PureSurvival","world")
    safe_cord = []
    res_area = []
    if res_area != getResidencesArea(res_path):
        res_area = getResidencesArea(res_path)
        chunck_area = convertAreaToChunk(res_area)
        region_area: list = []
        for area in chunck_area:
            regionCoordinate: dict = {"x1": math.ceil(area["x1"] / 32), "x2": math.ceil(area["x2"] / 32),
                                    "z1": math.ceil(area["z1"] / 32), "z2": math.ceil(area["z2"] / 32)}
            if regionCoordinate not in region_area:
                region_area.append(regionCoordinate)
        for area in region_area:
            cord: dict = {"x1": (area["x1"]-1)*32*16, "x2": (area["x2"]+1)*32*16,
                        "z1": (area["z1"]-1)*32*16, "z2": (area["z2"]+1)*32*16}
            print(cord)
            safe_cord.append(cord)
    for area in safe_cord:
        if x>=area["x1"] and x<=area["x2"] and z>=area["z1"] and z<=area["z2"]:
            return {"msg": "这个坐标在安全区域内，不会因为大更新被删除。"}
    return {"msg": "这个坐标不安全，在版本更新的时候地图数据会被删除，如果不想被删除可以在此区域圈一个小的临时领地。"}