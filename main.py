import base64
import json
import profile
from fastapi import FastAPI, File, UploadFile, responses
from fastapi.responses import StreamingResponse
from mcstatus import MinecraftServer, MinecraftBedrockServer
import requests

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