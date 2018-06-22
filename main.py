# -*- coding:utf-8 -*-
import sys
import socket
import json
from Algorith2 import AlgorithmCalculationFun,summary
import time

#从服务器接收一段字符串, 转化成字典的形式
def RecvJuderData(hSocket):
    nRet = -1
    Message = hSocket.recv(1024 * 1024 * 4)
#    print(Message)
    len_json = int(Message[:8])
    str_json = Message[8:].decode()
    
    while len(str_json) != len_json:
        Message = hSocket.recv(1024 * 1024 * 4)
        str_json =str_json + Message.decode()
        
#    if len(str_json) == len_json:
    nRet = 0
    Dict = json.loads(str_json)
    return nRet, Dict

# 接收一个字典,将其转换成json文件,并计算大小,发送至服务器
def SendJuderData(hSocket, dict_send):
    str_json = json.dumps(dict_send)
    len_json = str(len(str_json)).zfill(8)
    str_all = len_json + str_json
#    print(str_all)
    ret = hSocket.sendall(str_all.encode())
    if ret == None:
        ret = 0
#    print('sendall', ret)
    return ret

#用户自定义函数, 返回字典FlyPlane, 需要包括 "UAV_info", "purchase_UAV" 两个key.
#def AlgorithmCalculationFun(a, b, c):
#    FlyPlane = c["astUav"]
#    return FlyPlane





def main(szIp, nPort, szToken):
    print("server ip %s, prot %d, token %s\n", szIp, nPort, szToken)

    #Need Test // 开始连接服务器
    hSocket = socket.socket()
    hSocket.connect((szIp, nPort))

    #接受数据  连接成功后，Judger会返回一条消息：
    nRet, _ = RecvJuderData(hSocket)
    if (nRet != 0):
        return nRet
    print("connect Judger ok")

    # // 生成表明身份的json
    token = {}
    token['token'] = szToken        
    token['action'] = "sendtoken"   
   
    #// 选手向裁判服务器表明身份(Player -> Judger)
    nRet = SendJuderData(hSocket, token)
    if nRet != 0:
        return nRet
    print("show Player id -> Judger  ok!")
    
    #//身份验证结果(Judger -> Player), 返回字典Message
    nRet, Message = RecvJuderData(hSocket)
    if nRet != 0:
        return nRet 
    if Message["result"] != 0:
        print("token check error\n")
        return -1
    print("Judger check id ok!")
    
    # // 选手向裁判服务器表明自己已准备就绪(Player -> Judger)
    stReady = {}
    stReady['token'] = szToken
    stReady['action'] = "ready"
    nRet = SendJuderData(hSocket, stReady)
    if nRet != 0:
        return nRet
    print("be ready!")
    
    # //对战开始通知(Judger -> Player)
    nRet, Message = RecvJuderData(hSocket)
    if nRet != 0:
        return nRet
    print("begin!")
    
    #初始化地图信息
    pstMapInfo = Message["map"]  
    
    #初始化比赛状态信息
    pstMatchStatus = {}
    pstMatchStatus["time"] = 0

    #初始化飞机状态信息
    pstFlyPlane = {}
    pstFlyPlane["nUavNum"] = len(pstMapInfo["init_UAV"])
    pstFlyPlane["astUav"] = []

    #每一步的飞行计划
    FlyPlane_send = {}
    FlyPlane_send["token"] = szToken
    FlyPlane_send["action"] = "flyPlane"

    for i in range(pstFlyPlane["nUavNum"]):
        pstFlyPlane["astUav"].append(pstMapInfo["init_UAV"][i])


    # // 根据服务器指令，不停的接受发送数据
    enemyPark =[]
    tim=[]
    enemyInfo=[]
    while True:
        tic=time.time()
        print("current time",pstMatchStatus["time"])
        
        if pstMatchStatus["time"]==1:
            enemyPark = [pstMatchStatus["UAV_enemy"][0]["x"],pstMatchStatus["UAV_enemy"][0]["y"]]
        # // 进行当前时刻的数据计算, 填充飞行计划，注意：1时刻不能进行移动，即第一次进入该循环时
        FlyPlane,pstFlyPlane,enemyInfo = AlgorithmCalculationFun(pstMapInfo,pstMatchStatus,pstFlyPlane,enemyPark,enemyInfo)
        FlyPlane_send['UAV_info'] = FlyPlane
        FlyPlane_send["purchase_UAV"] = pstFlyPlane["purchase_UAV"]
        
#        print(enemyInfo)
#        if len(pstFlyPlane["astUav"])>6:
#            print("设置的6：",pstFlyPlane["astUav"][6])
#            if pstFlyPlane["astUav"][7]["status"]!=1:
#                print("设置的6：",pstFlyPlane["astUav"][6])
#                print("设置的7：",pstFlyPlane["astUav"][7])
#                print("设置的8：",pstFlyPlane["astUav"][8])
#                print("flyH:",pstMapInfo["h_low"])
#            elif pstFlyPlane["astUav"][7]["status"]==1:
#                print("设置的6：",pstFlyPlane["astUav"][6])
#                print("设置的7：",pstFlyPlane["astUav"][7])
#                print("设置的8：",pstFlyPlane["astUav"][8])
#                raise 0==1

        toc=time.time()
        tim.append((toc-tic)*1000)
        print('running time/ms:',(toc-tic)*1000)
#        print(enemyPark)
        # //发送飞行计划
        nRet = SendJuderData(hSocket, FlyPlane_send)
        if nRet != 0:
            return nRet
        
#        print("here")
        
        # // 接受当前比赛状态
        nRet, pstMatchStatus = RecvJuderData(hSocket)
        if nRet != 0:
            return nRet
        
#        print("服务器返回的：",pstMatchStatus["UAV_we"][1],'\n')
        if pstMatchStatus["match_status"] == 1:
            print("game over, we value %d, enemy value %d\n", pstMatchStatus["we_value"], pstMatchStatus["enemy_value"])
            hSocket.close()
            
            num,des,v = summary(pstFlyPlane["astUav"],pstMapInfo["UAV_price"],pstMatchStatus["we_value"])
            print("max time:",max(tim))
            print("we summary: ",num,des,v)
            num,des,v = summary(pstMatchStatus["UAV_enemy"],pstMapInfo["UAV_price"],pstMatchStatus["enemy_value"])
            print("enemy summary: ",num,des,v)
            return 0

#        toc=time.time()
#        tim.append((toc-tic)*1000)
#        print('running time/ms:',(toc-tic)*1000)
        
if __name__ == "__main__":
    if len(sys.argv) == 4:
        print("Server Host: " + sys.argv[1])
        print("Server Port: " + sys.argv[2])
        print("Auth Token: " + sys.argv[3])
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    else:
        print("need 3 arguments")