import json
import requests
import base64

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

deer = SkinFetch("Deer")
deer.getUUID()
print(deer.playerExsist())