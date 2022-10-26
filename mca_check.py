import sys
import yaml
import os
import math
import time
import shutil
from tqdm import tqdm


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


# def findWorldMCAPath(serverRootPath: str, worldName: str) -> str:
#     """
#     根据需要生成世界存档文件的地址。
#     :param serverRootPath:服务器根目录
#     :param worldName:需要操作的世界
#     :return: 对应存档文件地址
#     """
#     print("|正在查找世界存档文件。")
#     path = os.path.join(serverRootPath, worldName)
#     # noinspection PyBroadException
#     if os.path.exists(path):
#         print("|成功：世界存档地址为" + path)
#         return path
#     else:
#         print("|错误：未找到配置文件，请确认根目录与世界名是否正确？")
#         sys.exit("程序终止。")


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


def generateMcaWhitelist(chunkAreaList: list) -> list:
    """
    根据传入的有效区块计算哪些mca文件是需要被保护的。
    :param chunkAreaList: 需要被保护的区块两点坐标（列表）
    :return: mca文件白名单（列表）
    """
    print("|正在生成白名单 mca 文件。")
    regionFiles: list = []
    for area in chunkAreaList:
        regionCoordinate: dict = {"x1": math.ceil(area["x1"] / 32), "x2": math.ceil(area["x2"] / 32),
                                  "z1": math.ceil(area["z1"] / 32), "z2": math.ceil(area["z2"] / 32)}
        for x in range(regionCoordinate["x1"] - 2, regionCoordinate["x2"] + 2):
            for z in range(regionCoordinate["z1"] - 2, regionCoordinate["z2"] + 2):
                usedRegion: str = str(x) + '.' + str(z)
                regionFileName: str = "r." + usedRegion + ".mca"
                if regionFileName not in regionFiles:
                    regionFiles.append(regionFileName)
    print("|共计 " + str(len(regionFiles)) + " 个白名单mca。")
    return regionFiles


def backupRegionFiles(worldSavePath: str):
    """
    自动备份一个世界的region文件至世界目录下的regionBackup文件夹中。
    :param worldSavePath: 世界目录。
    """
    regionPath = os.path.join(worldSavePath, "region")
    mcaFileList = os.listdir(regionPath)
    print("|准备备份 " + str(len(mcaFileList)) + " 个mca文件，备份将保存在世界目录下的'regionBackup'文件夹中。")
    input(">对于存档较大的世界可能会花费较长的时间，按下回车确认开始。")
    currentTime = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
    # noinspection PyBroadException
    try:
        os.mkdir(os.path.join(worldSavePath, "regionBackup"))
    except:
        print("|监测到目录存在，跳过regionBackup目录创建。")
    backupLocation = os.path.join(worldSavePath, "regionBackup", str(currentTime))
    os.mkdir(backupLocation)
    for file in tqdm(mcaFileList):
        shutil.copy(os.path.join(regionPath, file), backupLocation)
    print("|备份完成！")


def getAllWorlds(serverRootPath: str) -> list:
    """
    在服务器根目录中搜索所有的世界存档（以level.dat为关键对象）。
    :param serverRootPath: 服务器根目录。
    :return: 返回一个包含所有世界名的列表。
    """
    print("|正在检索所有世界目录。")
    # noinspection PyBroadException
    try:
        allFile = os.listdir(serverRootPath)
        worldName = []
        for content in allFile:
            if os.path.isdir(os.path.join(serverRootPath, content)):
                files = os.listdir(os.path.join(serverRootPath, content))
                if "level.dat" in files:
                    worldName.append(content)
        print("|总共找到 " + str(len(worldName)) + " 个世界。")
        return worldName
    except:
        print("|错误：请确认根目录是否正确？")
        sys.exit("程序终止。")


def deleteUnusedMca(worldSavePath: str, mcaWhitelist: list):
    """
    删除未使用的多余 mca 文件。
    :param worldSavePath: 需要操作的世界存档目录。
    :param mcaWhitelist: 文件白名单。
    """
    regionBackupPath = os.path.join(worldSavePath, "regionBackup")
    regionPath = os.path.join(worldSavePath, "region")
    mcaFileList = os.listdir(regionPath)
    userInput: str = ''
    mcaBlackList = []
    while userInput != 'Y' and userInput != 'N':
        if not os.path.exists(regionBackupPath):
            userInput = input(">警告：没有监测到任何存档备份，在开始清理mca前强烈建议备份！（N：取消/Y：继续/B：备份）")
            if userInput == 'B':
                backupRegionFiles(worldSavePath)
        else:
            userInput = input(">注意：已准备就绪清理无用mca文件！（N：取消/Y：继续）")
        if userInput != 'Y' and userInput != 'N':
            print("|输入错误，请重试（N：取消/Y：继续）")
    if userInput == 'Y':
        mcaBlackList = mcaFileList
        for white in mcaWhitelist:
            mcaBlackList.remove(white)
        for mca in tqdm(mcaBlackList):
            # noinspection PyBroadException
            try:
                if mca not in mcaWhitelist:
                    removePath = os.path.join(regionPath, mca)
                    os.remove(removePath)
                else:
                    print("|跳过白名单： " + mca)
            except:
                print("|警告：未找到文件 " + mca)
    else:
        print("|已取消操作。")
        return


def restoreRegionBackup(worldSavePath: str):
    """
    恢复世界存档备份。
    :param worldSavePath: 需要操作的世界存档目录。
    :return:
    """
    regionPath = os.path.join(worldSavePath, "region")
    regionBackupPath = os.path.join(worldSavePath, "regionBackup")
    backupList: list = []
    # noinspection PyBroadException
    try:
        backupList = os.listdir(regionBackupPath)
    except:
        print("|您还没有进行过任何备份")
        pass
    if len(backupList) == 0:
        print("|警告：您的备份已被删除或神秘消失了，操作终止。")
        return
    else:
        print("|找到了这个世界有如下备份记录：")
        i = 0
        for backup in backupList:
            print("   " + str(i) + " : " + backup)
            i += 1
        userInput = int(input("请输入备份前的编号以开始恢复："))
        selectedBackupPath = os.path.join(regionBackupPath, backupList[userInput])
        # noinspection PyBroadException
        try:
            print("|删除旧文件：")
            for mca in tqdm(os.listdir(regionPath)):
                os.remove(os.path.join(regionPath, mca))
            print("|开始恢复备份：")
            for mca in tqdm(os.listdir(selectedBackupPath)):
                shutil.copy(os.path.join(selectedBackupPath, mca), regionPath)
            print("|恢复备份 " + backupList[userInput] + " 完成！")
        except:
            print("|警告：遇到未知错误。")


def deleteRegionBackup(worldSavePath: str):
    """
    删除世界存档备份。
    :param worldSavePath: 需要操作的世界存档目录
    :return:
    """
    regionBackupPath = os.path.join(worldSavePath, "regionBackup")
    backupList: list = []
    # noinspection PyBroadException
    try:
        backupList = os.listdir(regionBackupPath)
    except:
        print("|您还没有进行过任何备份")
        pass
    if len(backupList) == 0:
        print("|警告：您的备份已被删除或神秘消失了，操作终止。")
        return
    else:
        print("|找到了这个世界有如下备份记录：")
        i = 0
        for backup in backupList:
            print("   " + str(i) + " : " + backup)
            i += 1
        userInput = int(input(">请输入备份前的编号以删除："))
        selectedBackupPath = os.path.join(regionBackupPath, backupList[userInput])
        # noinspection PyBroadException
        try:
            for mca in tqdm(os.listdir(selectedBackupPath)):
                os.remove(os.path.join(selectedBackupPath, mca))
            shutil.rmtree(selectedBackupPath)
            print("|删除备份 " + backupList[userInput] + " 完成！")
        except:
            print("|警告：遇到未知错误。")


def menu(menuList: list, displayInfo: str) -> str:
    for tag in range(len(menuList)):
        print("   " + str(tag) + " : " + menuList[tag])
    inputTag = ''
    while True:
        # noinspection PyBroadException
        try:
            inputTag = int(input('>' + displayInfo + '：'))
        except:
            inputTag = ''
        finally:
            if inputTag != '':
                break
    while True:
        if inputTag >= len(menuList) or inputTag < 0:
            inputTage = int(input(">编号错误，请重新输入："))
        else:
            break
    print("|当前的选择是：" + menuList[inputTag])
    return menuList[inputTag]


def requestRootPath() -> str:
    # noinspection PyBroadException
    try:
        while True:
            serverRootPath = input(">请输入您的服务器根目录位置：")
            allFile = os.listdir(serverRootPath)
            if "eula.txt" in allFile:
                return serverRootPath
            else:
                print("|地址有误。")
    except:
        print("|错误：请不要输入奇怪的东西！")
        sys.exit("程序终止。")


def locateWorldSavePath(worldFolderPath: str) -> str:
    """
    定位 region 文件夹所在的位置
    @param worldFolderPath:
    @return:
    """
    fileList = os.listdir(worldFolderPath)
    if "region" in fileList:
        return worldFolderPath
    else:
        for folder in fileList:
            if 'DIM' in folder:
                return os.path.join(worldFolderPath, folder)
        return "null"


# Mainframe
if __name__ == '__main__':
    rootPath = requestRootPath()
    worldList = getAllWorlds(rootPath)
    while True:
        worldSelected = menu(worldList, "请输入世界前的编号选择想要操作的世界")
        os.system("clear")
        modeList = ["备份", "清除无用区块", "还原备份", "删除备份"]
        modeSelected = menu(modeList, "请输入需要进行的操作")
        worldFolder = os.path.join(rootPath, worldSelected)
        worldPath = locateWorldSavePath(worldFolder)
        if modeSelected == modeList[0]:
            os.system("clear")
            backupRegionFiles(worldPath)
            pass
        elif modeSelected == modeList[1]:
            os.system("clear")
            resPath = findResidenceSavePath(rootPath, worldSelected)
            residences = getResidencesArea(resPath)
            chunks = convertAreaToChunk(residences)
            whiteList = generateMcaWhitelist(chunks)
            deleteUnusedMca(worldPath, whiteList)
            pass
        elif modeSelected == modeList[2]:
            os.system("clear")
            restoreRegionBackup(worldPath)
            pass
        elif modeSelected == modeList[3]:
            os.system("clear")
            deleteRegionBackup(worldPath)
            pass
