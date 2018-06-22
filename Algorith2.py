# -*- coding: utf-8 -*-
"""
Created on Thu May 17 18:28:07 2018

@author: peng
"""
from Astar import make_path
import copy
from Electricity import type2price,power_estimate,update_enemyInfo,attackEnemy,isOnAttack

#结束时，统计飞机总数，毁坏数量，总分数
def summary(UAVs,UAV_price,we_value):
    num=0
    destory=0
    value=0
    for u in UAVs:
        num+=1
        if u["status"]==1:
            destory += 1
        else:
            value += type2value(u["type"],UAV_price)
    value += we_value
    return num,destory,value
    
#将no标签转为列表索引，找不到的返回-1        
def no2index(no,lis):
    for i in range(len(lis)):
        if lis[i]["no"]==no:
            return i
    return -1

#基于UAV选择good，选择耗电小的、价值大的货物
def choose_good_base_uav(goods,uav,curTime,flyH):
    if not goods:
        return 0 #没goods可选
    curPos=[uav["x"],uav["y"],uav["z"]]
    availabe_good=[]
    for good in goods:
        if good["status"]==0:
            shorcut_dis = ((good["start_x"]-curPos[0])**2+(good["start_y"]-curPos[1])**2)**0.5/(2**0.5)+abs(curPos[2]-flyH)+flyH
            
            if (good["start_x"]-good["end_x"])==0 or (good["start_y"]-good["end_y"])==0:
                deliver_dis = abs(good["start_x"]-good["end_x"])+abs(good["start_y"]-good["end_y"])+flyH*2
            else:
                deliver_dis = ((good["start_x"]-good["end_x"])**2+(good["start_y"]-good["end_y"])**2)**0.5/(2**0.5)+flyH*2
            
            power_left = uav["remain_electricity"]-(deliver_dis+2)*good["weight"]
#            sum_dis = shorcut_dis + deliver_dis
            waitTime=(good["start_time"]+good["remain_time"])-(curTime+shorcut_dis)
            if waitTime>=0 and uav["load_weight"]>=good["weight"] and power_left>=0:   
                availabe_good.append([good["value"],waitTime,good,good["value"]*power_left])
#                availabe_good.append([good["value"],waitTime,good,good["value"]/deliver_dis])
    if availabe_good:
        return sorted(availabe_good, key = lambda x:(x[3],x[0]), reverse = True)[0][2] #降序
    else: 
        return 0 #没货物

#基于good 选择 uav，选择载重最接近货物、剩余电量大的uav
def choose_uav_base_good(good,uavs,curTime,flyH):
    if not uavs:
        return 0 #没uavs可选
    choise=[]
    for uav in uavs:
        curPos=[uav["x"],uav["y"],uav["z"]]
        shorcut_dis = ((good["start_x"]-curPos[0])**2+(good["start_y"]-curPos[1])**2)**0.5/(2**0.5)+abs(curPos[2]-flyH)+flyH
        waitTime=(good["start_time"]+good["remain_time"])-(curTime+shorcut_dis)
        diff=uav["load_weight"]-good["weight"]
          
        if (good["start_x"]-good["end_x"])==0 or (good["start_y"]-good["end_y"])==0:
            deliver_dis = abs(good["start_x"]-good["end_x"])+abs(good["start_y"]-good["end_y"])+flyH*2
        else:
            deliver_dis = ((good["start_x"]-good["end_x"])**2+(good["start_y"]-good["end_y"])**2)**0.5/(2**0.5)+flyH*2
        
        power_left = uav["remain_electricity"]-(deliver_dis+2)*good["weight"]
        if waitTime>=0 and diff>=0 and power_left>=0 and uav["remain_electricity"]==uav["capacity"]:#??????????
            choise.append([diff,waitTime,uav,-power_left])        
    if choise:
        return sorted(choise, key = lambda x:(x[0],x[3]), reverse = False)[0][2] #升序

    else: 
        return 0 #没可选的uav

#选择起飞的UAV：从最快获得并价值较大的货物中，选择载重最接近货物、剩余电量大的uav  
def pick_first_Uav(uavs,goods,curTime,flyH,parking):
    availabe_goods=[]
    curPos=[parking["x"],parking["y"],0]
    
    for good in goods:
        if good["status"]==0:
            if (good["start_x"]-curPos[0])==0 or (good["start_y"]-curPos[1])==0:
                shorcut_dis = abs(good["start_x"]-curPos[0]) + abs(good["start_y"]-curPos[1])+flyH*2
            else:
                shorcut_dis = ((good["start_x"]-curPos[0])**2+(good["start_y"]-curPos[1])**2)**0.5/(2**0.5)+flyH*2
            
            if (good["start_x"]-good["end_x"])==0 or (good["start_y"]-good["end_y"])==0:
                deliver_dis = abs(good["start_x"]-good["end_x"])+abs(good["start_y"]-good["end_y"])+flyH*2
            else:
                deliver_dis = ((good["start_x"]-good["end_x"])**2+(good["start_y"]-good["end_y"])**2)**0.5/(2**0.5)+flyH*2
            
            sum_dis = shorcut_dis + deliver_dis
#            availabe_goods.append([good["value"]/sum_dis,good["value"],good])#机器人对战
            availabe_goods.append([good["value"]/deliver_dis,good["value"],good])#自我对战
            
    availabe_goods = sorted(availabe_goods, key = lambda x:(x[0],x[1]), reverse = True)#降序：最快获得并价值较大的货物排在首位
             
    uav_good= []
    for i in range(len(availabe_goods)):
        u=choose_uav_base_good(availabe_goods[i][2],uavs,curTime,flyH)
        if u:
            uav_good.append([u,availabe_goods[i][2]["no"]])
    if uav_good:
        return uav_good[0]
    else:
        return uav_good


#设置flag 和 target_no
def set_uav(uav,pstFlyPlane,flag=0,target_no=-1):
    for i in range(len(pstFlyPlane["astUav"])):
        if pstFlyPlane["astUav"][i]["no"]==uav["no"]:
            pstFlyPlane["astUav"][i]["flag"]=flag
            pstFlyPlane["astUav"][i]["target_no"]=target_no
#            pstFlyPlane["astUav"][i]["flyTime"]=flyTime
    return pstFlyPlane

#从goods中选择no的good，没有返回空 
def getGood(no,goods):
    for g in goods:
        if g["no"]==no:
            return g
    return {}

#截取要发送的 UAV_info 
def getResult(uavs):   #UAV_info 新"remain_electricity"
    rs=["no", "type","x", "y", "z", "remain_electricity","goods_no", "status"]
    result=[]
    for u in uavs:
        if u["status"] != 1:
            one={}
            for r in rs:
                one[r]=u[r]
            result.append(one) 
    return result

#获得其他未被选中的goods
def get_otherGoods(uavs,goods,targets_id=[]):
    oterGoods=[] #未被选中的goods
#    targets_id=[]
    for uav in uavs:
        if uav["target_no"] != -1:
            targets_id.append(uav["target_no"])
    
    if targets_id:
        for g in goods:
            if g["no"] not in targets_id:
                oterGoods.append(g)
    else:
        oterGoods=goods
    return oterGoods

#UAV转为价值
def type2value(Type,UAV_price):
    value=0
    for p in UAV_price:
        if p["type"]==Type:
            value = p["value"]
    return value

#检查是否我方uav是否在敌方上方，返回能否与敌机相撞
def check_aboveEnemy(good,enemys,UAV_price,myType,uav):
    canMeet = False
    for e in enemys:
        if e["status"]!=1 and e["status"]!=3:
            if uav["x"]==e["x"] and uav["y"]==e["y"]:
                value = type2value(e["type"],UAV_price)
                myValue = type2value(myType,UAV_price)
                if value+good["value"]>=myValue:
                    canMeet = True
    return canMeet

#我方uav飞往货物时，返回是否能来得及并且能否应当撞击敌机
def check_canMeetEnemy(good,enemys,UAV_price,lendis,myType,flyH):
    canMeet = False
    for e in enemys:
        if e["status"]!=1 and e["status"]!=3:
            if e["x"]==good["start_x"] and e["y"]==good["start_x"] and e["z"]<flyH:
                if lendis<=(flyH-e["z"]):
                    value = type2value(e["type"],UAV_price)
                    myValue = type2value(myType,UAV_price)
                    if value+good["value"]>=myValue:
                        canMeet = True
    return canMeet

#def setFlag1_and_search(uav):
#    uav["flag"]=1

def check_enemyOnEnd(endPos,enemyInfo,uavs):
    onEnd = False
    onAttack = False
    dis = 0
    for e in enemyInfo:
        if e["flag"]==5:
            if e["x"]==endPos[0] and e["y"]==endPos[1]:
                onEnd = True
                onAttack,dis = isOnAttack(e["no"],uavs)
                break
    return onEnd,dis
#不同状态下，uav下一步变化
def next_step(pstFlyPlane,flyH,goods,curTime,maps,building,enemys,UAV_price,parking,enemyAbove,enemyInfo):
    uavs = pstFlyPlane["astUav"]
    abovePark = check_abovePark(uavs,parking,flag=0)
    for uav in uavs:
        if uav["status"] != 1:
            
            if uav["flag"]==5: #5 直捣黄龙
                if uav["path"]:
                    nextPos=uav["path"].pop(0)
                    uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]  
                                
            elif uav["flag"]==-1:#停机坪，充电
                uav["remain_electricity"] = min(uav["capacity"],uav["remain_electricity"]+uav["charge"])
                
            elif uav["flag"]==0: #0 开始上升状态
                nextPos=uav["path"].pop(0)
                uav["goods_no"]=-1
                if nextPos[2]==flyH :
                    uav["flag"]=1
                uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
       
        
            elif uav["flag"]==1: # 1 在>=flyH处停留
               if uav["target_no"]==-1: #无目标货物，查找
                   otherGoods = get_otherGoods(uavs,goods)
                   H=max(flyH,uav["z"])#?????
                   g=choose_good_base_uav(otherGoods,uav,curTime,H)
                   if g: #找到
                       uav["target_no"]=g["no"]
                   else:
                       if uav["remain_electricity"]/uav["capacity"]<0.20:#电量小于25%，返回充电
                           uav["flag"]=6
                           uav["target_no"]=-1                           
                           init = [uav["x"],uav["y"]]
                           goal = [parking["x"],parking["y"]]
                           path = make_path(init,goal,maps,building,uav["z"])
                           temp=list(range(0,uav["z"]))
                           temp=temp[::-1]
                           pathB = [[parking["x"],parking["y"],i] for i in temp]
                           path = path + pathB
                           uav["path"]=path
                           nextPos=uav["path"].pop(0)
                           uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                           
               if uav["target_no"] != -1:#有目标货物，路径规划
                   init = [uav["x"],uav["y"]]
                   good = getGood(uav["target_no"],goods)
                   if good and good["status"] ==0:
                       goal=[good["start_x"],good["start_y"]]
               
                       H=max(flyH,uav["z"])
                       path = make_path(init,goal,maps,building,H)

                       path.pop(0)
                       temp=list(range(0,uav["z"]))
                       temp=temp[::-1]
                       pathB=[[goal[0],goal[1],i] for i in temp]
                       path=path+pathB
               
                       uav["path"]=path
                       nextPos=uav["path"].pop(0)
                       uav["flag"]=2
                       uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                   else:
                       otherGoods = get_otherGoods(uavs,goods,targets_id=[uav["target_no"]])
                       H=max(flyH,uav["z"])#?????
                       g=choose_good_base_uav(otherGoods,uav,curTime,H)
                       if g: #找到
                           uav["target_no"]=g["no"]
                       else:
                           pass
        
        
            elif uav["flag"]==2: # 2 飞向货物阶段
                curPath = uav["path"].copy()
                nextPos=uav["path"].pop(0)
                good = getGood(uav["target_no"],goods)
#                print(good)
                if not good :#货物消失
                    if uav["z"]<flyH:
                        #上升到最低
                        init = [uav["x"],uav["y"]]
                        path=[[init[0],init[1],i] for i in range(uav["z"]+1,flyH+1)]
                        npos = path.pop(0)
                        if path:
                            uav["flag"]=0
                        else:
                            uav["flag"]=1
                        uav["target_no"]=-1
                        uav["path"]=path
                        uav["x"],uav["y"],uav["z"]=npos[0],npos[1],npos[2]
                        
                    else:
                        #停留
                        uav["flag"]=1
                        uav["path"]=[]
                        uav["target_no"]=-1
                elif good["status"] != 0:#被敌人捡走
                    if uav["z"]>=flyH:
                        lendis = len(uav["path"])-flyH-abs(uav["z"]-flyH)
                        canMeet = check_canMeetEnemy(good,enemys,UAV_price,lendis,uav["type"],flyH)
                        if canMeet:
                            uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                        else:
                            #停留
                            uav["flag"]=1
                            uav["path"]=[]
                            uav["target_no"]=-1
                    else:
                       canMeet = check_aboveEnemy(good,enemys,UAV_price,uav["type"],uav) 
                       if canMeet:
                           uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                       else:
                           #上升到最低
                           init = [uav["x"],uav["y"]]
                           path=[[init[0],init[1],i] for i in range(uav["z"]+1,flyH+1)]
                           npos = path.pop(0)
                           if path:
                               uav["flag"]=0
                           else:
                               uav["flag"]=1
                           uav["target_no"]=-1
                           uav["path"]=path
                           uav["x"],uav["y"],uav["z"]=npos[0],npos[1],npos[2]
                        
                else:    #货物可用            
                    if nextPos[0]==good["start_x"] and nextPos[1]==good["start_y"] : 
                        if nextPos[2]==flyH:#恰在货物上方
                            init=[good["start_x"],good["start_y"]]
                            goal=[good["end_x"],good["end_y"]]
                            power = power_estimate(init,goal,maps,building,flyH,good["weight"])
                            if uav["remain_electricity"]>=power:#够电力，能运送
                                if good["start_time"] > curTime+uav["z"]:#未出现
                                    uav["path"] = curPath 
                                    nextPos = [uav["x"],uav["y"],uav["z"]]
                            else:
                                uav["flag"]=1
                                uav["target_no"]=-1
                                uav["path"] = []
                        elif nextPos[2]==0:#在货物处
                            uav["flag"]=3
                            uav["goods_no"]=uav["target_no"]#捡起货物
                            uav["remain_electricity"] = max(0,uav["remain_electricity"]-good["weight"])#新

                    uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
        
        
            elif uav["flag"]==3: # 3 在取货点 
                init = [uav["x"],uav["y"]]
                good = getGood(uav["target_no"],goods)

                goal=[good["end_x"],good["end_y"]]
            
                path=[[init[0],init[1],i] for i in range(1,flyH)]
                pathA = make_path(init,goal,maps,building,flyH)
    #            print("songHuo!!!!!!!!!",flyH)
                temp=list(range(0,flyH))
                temp=temp[::-1]
                pathB=[[goal[0],goal[1],i] for i in temp]
                path=path+pathA+pathB
            
                uav["path"]=path
                nextPos=uav["path"].pop(0)
                uav["flag"]=4
                uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                uav["remain_electricity"] = max(0,uav["remain_electricity"]-good["weight"])#新
                
        
            elif uav["flag"]==4:# 4 送货阶段
                nextPos=uav["path"][0]
                good = getGood(uav["target_no"],goods)
#                print(good)
                if good:
                    if nextPos[0]==good["end_x"] and nextPos[1]==good["end_y"] and nextPos[2]==0:
                        uav["flag"]=0
                        uav["target_no"]=-1
                        init = [uav["x"],uav["y"]]
                        path=[[init[0],init[1],i] for i in range(1,flyH+1)]
                        uav["path"]=path
                    elif nextPos[0]==good["end_x"] and nextPos[1]==good["end_y"] and nextPos[2]>=flyH:
                        endPos=[good["end_x"],good["end_y"]]
                        onEnd,dis = check_enemyOnEnd(endPos,enemyInfo,uavs)
                        if onEnd:#敌机堵截在放货处
                            sumDis= len(uav["path"])+max(dis-flyH,0)+2
                            powerLeft = uav["remain_electricity"]-good["weight"]*sumDis
                            if powerLeft>=0:#电量够，等待
                                nextPos=[uav["x"],uav["y"],uav["z"]]
                            else:
                                uav["path"].pop(0)
                        else:
                            uav["path"].pop(0)
                    else:
                        uav["path"].pop(0)
                            
    #                print(uav)
                    uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                    uav["remain_electricity"] = max(0,uav["remain_electricity"]-good["weight"])#新
            
            elif uav["flag"]==6:# 6 返回充电
                nextPos=uav["path"][0]
                if nextPos[0]==parking["x"] and nextPos[1]==parking["y"] :
                    if nextPos[2]==0:
                        uav["flag"]=-1
                        uav["target_no"]=-1
                        uav["remain_electricity"] = min(uav["capacity"],uav["remain_electricity"]+uav["charge"])
                        
                        nextPos=uav["path"].pop(0)
                        uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                    else:
                        if enemyAbove or abovePark:#有敌机或我方机，停留
                            pass
                        else:
                            nextPos=uav["path"].pop(0) 
                            uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                else:
                   nextPos=uav["path"].pop(0) 
                   uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]
                
            elif uav["flag"]==7:# 7攻击敌军
                eNo = uav["target_uav"]
                i = no2index(eNo,enemyInfo)
                if uav["path"]:#有path
                    nextPos=uav["path"].pop(0)
                    if nextPos[2]==flyH-1:#将要下降
                        if i ==-1:#没有找到对应的
                            uav["flag"]=1
                            uav["path"]=[]
                            uav["target_no"]=-1
                            uav["target_uav"]=-1
                            nextPos=[uav["x"],uav["y"],uav["z"]]
                            
                        else:#找到对应的敌机
                            e = enemyInfo[i]
                            if uav["x"]==e["x"] and uav["y"]==e["y"] and uav["z"]>e["z"]:#在敌机上方
                                if e["flag"]==2:
                                    eValue = e["Uvalue"]
                                else:
                                    eValue = e["Uvalue"]+e["Gvalue"]
                                
                                if uav["value"]>eValue:
                                    uav["flag"]=1
                                    uav["path"]=[]
                                    uav["target_no"]=-1
                                    uav["target_uav"]=-1
                                    nextPos=[uav["x"],uav["y"],uav["z"]]
                                
                            else:#在其他地方
                                if uav["z"]<flyH and e["flag"] !=2:
                                    uav["flag"]=0
                                    uav["path"]=[[uav["x"],uav["y"],z] for z in range(uav["z"]+1,flyH+1)] 
                                    uav["target_no"]=-1
                                    uav["target_uav"]=-1
                                    nextPos=uav["path"].pop(0)
                    
                    uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2]            
                else:#无path
                    i = no2index(eNo,enemyInfo)
                    if i ==-1 or (i!=-1 and enemyInfo[i]["flag"]!=2 and enemyInfo[i]["flag"]!=3) :#要撞的敌机逃脱
                        uav["flag"]=0
                        uav["path"]=[[uav["x"],uav["y"],z] for z in range(uav["z"]+1,flyH+1)] 
                        uav["target_no"]=-1
                        uav["target_uav"]=-1
                        nextPos=uav["path"].pop(0)
                        uav["x"],uav["y"],uav["z"]=nextPos[0],nextPos[1],nextPos[2] 
            else:
                pass

    pstFlyPlane["astUav"]=uavs
    return pstFlyPlane

#根据UAV_we更新uav当前状态
def updata_uavState(UAV_we,uavs):
    for i in range(len(UAV_we)):
        uavs[i]["status"]=UAV_we[i]["status"]
    return uavs

#检测停机场上方是否有我方uav
def check_abovePark(uavs,parking,flag=0):#检测飞行飞机是否在上方 1在 ，0不在
    for uav in uavs:
        if uav["flag"] == flag:
            if uav["x"]==parking["x"] and uav["y"]==parking["y"]:
                return 1
    return 0

#获取其他能用的、未被选中的goods，以及未起飞的UAVs        
def otherIfo(uavs,goods,parking):
    otherUAVs=[] #未起飞的uavs
    oterGoods=[] #未被选中的goods
    targets_id=[]
    abovePark = 0 #检测飞行飞机是否在上方 1在 ，0不在
    for uav in uavs:
        if uav["flag"] == -1:#未起飞
            otherUAVs.append(uav)
        else:
            if uav["x"]==parking["x"] and uav["y"]==parking["y"]:
                abovePark = 1
        if uav["target_no"] != -1:
            targets_id.append(uav["target_no"])
    
    if targets_id:
        for g in goods:
            if g["no"] not in targets_id:
                oterGoods.append(g)
    else:
        oterGoods=goods
    
    return otherUAVs,oterGoods,abovePark

#上升或下降来改变路径        
def changePath(path,up=True):
    p = []
    if up:
        if path:
            p=[[e[0],e[1],e[2]+1] for e in path]
            p.append([p[-1][0],p[-1][1],0])
    else:
        if path:
            p=[[e[0],e[1],e[2]-1] for e in path]
            p.pop(-1)
    return p

#检测我方相互间的碰撞，返回uav两两碰撞的索引
def check_weMeet(curUAVs,nextUAVs):
    n=len(curUAVs)
    weMeet=[]
    for i in range(n-1):
        nextuav = nextUAVs[i]
        curuav = curUAVs[i]
        if curuav["flag"] != -1 and curuav["status"] != 1: #已经起飞
            for j in range(i+1,n):
                nextother = nextUAVs[j]
                curother = curUAVs[j]
                if curother["flag"] != -1 and curother["status"] != 1: #已经起飞
                    if ((nextuav["x"]== nextother["x"] and nextuav["y"]== nextother["y"] and nextuav["z"]== nextother["z"]) or  #位置重叠
                        ((nextuav["x"]== curother["x"] and nextuav["y"]== curother["y"] and nextuav["z"]== curother["z"]) and #位置互换
                         (curuav["x"]== nextother["x"] and curuav["y"]== nextother["y"] and curuav["z"]== nextother["z"]))):
                        weMeet.append([i,j])
                    elif((curuav["z"]==nextuav["z"] and curother["z"]==nextother["z"] and curuav["z"]==curother["z"]) and
                         (abs(curuav["x"]-nextuav["x"])==1 and abs(curuav["y"]-nextuav["y"])==1 and abs(curother["x"]-nextother["x"])==1 and abs(curother["y"]-nextother["y"])==1) and
                         (curuav["x"]+nextuav["x"])/2==(curother["x"]+nextother["x"])/2 and (curuav["y"]+nextuav["y"])/2==(curother["y"]+nextother["y"])/2):#交叉
                        weMeet.append([i,j])
    return weMeet

#处理我方相互间的碰撞
def deal_weMeet(curUAVs,nextUAVs,weMeet,flyH,h_high,maps):    
    if weMeet:
        hmax = min(h_high,maps["z"]-1)
        for e in weMeet:
            i,j=e[0],e[1]
            if curUAVs[i]["z"]<flyH or curUAVs[i]["flag"]==4:#i低于flyH 或 处于送货阶段
                curpath=nextUAVs[j]["path"].copy()
                curpath.insert(0,[nextUAVs[j]["x"],nextUAVs[j]["y"],nextUAVs[j]["z"]])
                if nextUAVs[j]["z"]<hmax and curUAVs[j]["z"]<hmax:
                    nextUAVs[j]["path"] = changePath(curpath)
                    nextUAVs[j]["x"]=curUAVs[j]["x"]
                    nextUAVs[j]["y"]=curUAVs[j]["y"]
                    nextUAVs[j]["z"]=curUAVs[j]["z"]+1
                else:
                    nextUAVs[j]["path"] = changePath(curpath,up=False)
                    nextUAVs[j]["x"]=curUAVs[j]["x"]
                    nextUAVs[j]["y"]=curUAVs[j]["y"]
                    nextUAVs[j]["z"]=curUAVs[j]["z"]-1
                
           
            elif curUAVs[j]["z"]<flyH or curUAVs[j]["flag"]==4:#j低于flyH 或 处于送货阶段
                curpath=nextUAVs[i]["path"].copy()
                curpath.insert(0,[nextUAVs[i]["x"],nextUAVs[i]["y"],nextUAVs[i]["z"]])
                if nextUAVs[i]["z"]<hmax and curUAVs[i]["z"]<hmax:
                    nextUAVs[i]["path"] = changePath(curpath)
                    nextUAVs[i]["x"]=curUAVs[i]["x"]
                    nextUAVs[i]["y"]=curUAVs[i]["y"]
                    nextUAVs[i]["z"]=curUAVs[i]["z"]+1
                else:
                    nextUAVs[i]["path"] = changePath(curpath,up=False)
                    nextUAVs[i]["x"]=curUAVs[i]["x"]
                    nextUAVs[i]["y"]=curUAVs[i]["y"]
                    nextUAVs[i]["z"]=curUAVs[i]["z"]-1
            
            elif curUAVs[i]["flag"]==2 and curUAVs[i]["target_no"]!=-1 and curUAVs[j]["flag"]==1:
                curpath=nextUAVs[j]["path"].copy()
                curpath.insert(0,[nextUAVs[j]["x"],nextUAVs[j]["y"],nextUAVs[j]["z"]])
                if nextUAVs[j]["z"]<hmax and curUAVs[j]["z"]<hmax:
                    nextUAVs[j]["path"] = changePath(curpath)
                    nextUAVs[j]["x"]=curUAVs[j]["x"]
                    nextUAVs[j]["y"]=curUAVs[j]["y"]
                    nextUAVs[j]["z"]=curUAVs[j]["z"]+1
                else:
                    nextUAVs[j]["path"] = changePath(curpath,up=False)
                    nextUAVs[j]["x"]=curUAVs[j]["x"]
                    nextUAVs[j]["y"]=curUAVs[j]["y"]
                    nextUAVs[j]["z"]=curUAVs[j]["z"]-1
            
            elif curUAVs[j]["flag"]==2 and curUAVs[j]["target_no"]!=-1 and curUAVs[i]["flag"]==1: 
                curpath=nextUAVs[i]["path"].copy()
                curpath.insert(0,[nextUAVs[i]["x"],nextUAVs[i]["y"],nextUAVs[i]["z"]])
                if nextUAVs[i]["z"]<hmax and curUAVs[i]["z"]<hmax:
                    nextUAVs[i]["path"] = changePath(curpath)
                    nextUAVs[i]["x"]=curUAVs[i]["x"]
                    nextUAVs[i]["y"]=curUAVs[i]["y"]
                    nextUAVs[i]["z"]=curUAVs[i]["z"]+1
                else:
                    nextUAVs[i]["path"] = changePath(curpath,up=False)
                    nextUAVs[i]["x"]=curUAVs[i]["x"]
                    nextUAVs[i]["y"]=curUAVs[i]["y"]
                    nextUAVs[i]["z"]=curUAVs[i]["z"]-1
            
            else:
                curpath=nextUAVs[j]["path"].copy()
                curpath.insert(0,[nextUAVs[j]["x"],nextUAVs[j]["y"],nextUAVs[j]["z"]])
                if nextUAVs[j]["z"]<hmax and curUAVs[j]["z"]<hmax:
                    nextUAVs[j]["path"] = changePath(curpath)
                    nextUAVs[j]["x"]=curUAVs[j]["x"]
                    nextUAVs[j]["y"]=curUAVs[j]["y"]
                    nextUAVs[j]["z"]=curUAVs[j]["z"]+1
                else:
                    nextUAVs[j]["path"] = changePath(curpath,up=False)
                    nextUAVs[j]["x"]=curUAVs[j]["x"]
                    nextUAVs[j]["y"]=curUAVs[j]["y"]
                    nextUAVs[j]["z"]=curUAVs[j]["z"]-1
                
    return nextUAVs

#基于货物购买UAV，选择价格低的、最接近货物重量的uav
def buy_UAV_base_good(good,UAV_price,we_value,parking,flyH,curTime):
#    curPos=[parking["x"],parking["y"],0]
    choise=[]
    for uav in UAV_price:
#        shorcut_dis = ((good["start_x"]-curPos[0])**2+(good["start_y"]-curPos[1])**2)**0.5/(2**0.5)+flyH*2
#        waitTime=(good["start_time"]+good["remain_time"])-(curTime+shorcut_dis+1)
        diff=uav["load_weight"]-good["weight"]
        if we_value>=uav["value"] and diff>=0 :
            choise.append([uav["value"],diff,uav])        
    if choise:
        return sorted(choise, key = lambda x:(x[0],x[1]), reverse = False)[0][2] 
    else: 
        return {} #没可选的uav

#检查敌机是否在停机场上方
def check_enemyAbovePark(enemys,parking,flyH):
    enemyAbove = False
    for e in enemys:
        if e["x"]==parking["x"] and e["y"]==parking["x"] and e["z"]<flyH:
            enemyAbove = True
    return enemyAbove

#购买最低价的uav        
def buyMinUAV(UAV_price,we_value):
    minUAV = UAV_price[0]
    for u in UAV_price:
        if minUAV["value"]>u["value"]:
            minUAV = u
    minPrice = minUAV["value"]

    purchase_UAV=[]
    
    if we_value>=minPrice:
        r={}
        r["purchase"]=minUAV["type"]
        purchase_UAV.append(r)
    return purchase_UAV

#正常购买uav，选择买了就能投入使用的uav
def buyUAV(UAV_price,we_value,goods,parking,flyH,curTime):
    availabe_goods=[]
    curPos=[parking["x"],parking["y"],0]
    for good in goods:
        if good["status"]==0:
            if (good["start_x"]-curPos[0])==0 or (good["start_y"]-curPos[1])==0:
                shorcut_dis = abs(good["start_x"]-curPos[0]) + abs(good["start_y"]-curPos[1])+flyH*2
            else:
                shorcut_dis = ((good["start_x"]-curPos[0])**2+(good["start_y"]-curPos[1])**2)**0.5/(2**0.5)+flyH*2
            
            if (good["start_x"]-good["end_x"])==0 or (good["start_y"]-good["end_y"])==0:
                deliver_dis = abs(good["start_x"]-good["end_x"])+abs(good["start_y"]-good["end_y"])+flyH*2
            else:
                deliver_dis = ((good["start_x"]-good["end_x"])**2+(good["start_y"]-good["end_y"])**2)**0.5/(2**0.5)+flyH*2
            
            sum_dis = shorcut_dis + deliver_dis
            availabe_goods.append([-deliver_dis,good["value"],good])#改改改改改改改改改改
    availabe_goods = sorted(availabe_goods, key = lambda x:(x[0],x[1]), reverse = True)#降序
    
    purchase_UAV=[]
    
    if availabe_goods:
        uav_good= []
        for g in availabe_goods:
            uav_buy=buy_UAV_base_good(good,UAV_price,we_value,parking,flyH,curTime)
            if uav_buy:
                uav_good.append(uav_buy)
            
        if uav_good:
#            uav_good = sorted(uav_good, key = lambda x:x[0], reverse = True)
            r={}
            r["purchase"]=uav_good[0]["type"]
            purchase_UAV.append(r)
            return purchase_UAV
    return purchase_UAV

#添加新的uav
def addUAV(uavs,newuavs,parking,flyH,UAV_price):
    n = len(uavs)
    nn = len(newuavs)
    if n<nn:
        path=[[parking["x"],parking["y"],i] for i in range(1,flyH+1)]
        for i in range(n,nn):
            u = newuavs[i]
            u["path"]=path
#            u["flyTime"] = -1 
            u["target_no"] = -1
            u["flag"] = -1
            #新
            value,capacity,charge = type2price(u["type"],UAV_price)
            u["value"] = value
            u["capacity"] = capacity
            u["charge"] = charge
            u["target_uav"] = -1
            uavs.append(u)
    return uavs

#统计flag=5的uav数目
def countFlag5(uavs):
    count = 0
    for u in uavs:
        if u["status"] != 1 and u["flag"]==5:
            count+=1         
    return count           

#检测与敌机的碰撞，返回敌机是否在附近、能否与敌机碰撞
def check_enemyOnWay(enemys,UAV_price,maps,myuav,goodValue):
    onWay = False
    canMeet = False
    uav_no = -1
    for e in enemys:
        if e["status"]==0:
            if myuav["x"]==e["x"] and myuav["y"]==e["y"] and e["z"] == myuav["z"]-1:#敌机在下
                onWay = True
            if e["z"] == myuav["z"]:
                xmin = max(myuav["x"]-1,0)
                xmax = min(myuav["x"]+1,maps["x"]-1)
                
                ymin = max(myuav["y"]-1,0)
                ymax = min(myuav["y"]+1,maps["y"]-1)
                
                if (xmin<=e["x"] and e["x"]<=xmax) and (ymin<=e["y"] and e["y"]<=ymax):
                    onWay = True
            if onWay:
                eValue = type2value(e["type"],UAV_price)
#                myValue = type2value(myuav["type"],UAV_price)
                if eValue > (myuav["value"]+goodValue):
                    canMeet = True
                    uav_no = e["no"]
                
#    print(onWay)
    return onWay,canMeet,uav_no

#处理与敌机的可能碰撞
def deal_enemyMeet(curUAVs,nextUAVs,enemys,UAV_price,goods,maps,flyH,h_high):
    nums =  len(nextUAVs)
    hmax = min(h_high,maps["z"]-1)
    for i in range(nums):
         if nextUAVs[i]["status"]==0 or nextUAVs[i]["status"]==2:
             my = nextUAVs[i]
             if my["z"]>=flyH:
                 goodValue = 0
                 if my["goods_no"]!=-1:
                    good = getGood(my["goods_no"],goods)
                    if good:
                        goodValue = good["value"]
                
                 onWay,canMeet,uav_no = check_enemyOnWay(enemys,UAV_price,maps,my,goodValue)
#                 print("canMeet",canMeet)
                 if onWay and not canMeet:
                     curpath=my["path"].copy()
                     curpath.insert(0,[my["x"],my["y"],my["z"]])
                
                     if my["z"]<hmax and curUAVs[i]["z"]<hmax:#当前和下一步均小于最大飞行高度
                        nextUAVs[i]["path"] = changePath(curpath)
                        nextUAVs[i]["x"]=curUAVs[i]["x"]
                        nextUAVs[i]["y"]=curUAVs[i]["y"]
                        nextUAVs[i]["z"]=curUAVs[i]["z"]+1
                     else:
                        nextUAVs[i]["path"] = changePath(curpath,up=False)
                        nextUAVs[i]["x"]=curUAVs[i]["x"]
                        nextUAVs[i]["y"]=curUAVs[i]["y"]
                        nextUAVs[i]["z"]=curUAVs[i]["z"]-1
                 elif onWay and canMeet:
                     nextUAVs[i]["target_uav"] = uav_no
    return nextUAVs

           
def AlgorithmCalculationFun(pstMapInfo,pstMatchStatus,pstFlyPlane,enemyPark,enemyInfo):
    UAV_price = pstMapInfo["UAV_price"]
    
    if pstMatchStatus["time"] == 0:
        path=[[pstMapInfo["parking"]["x"],pstMapInfo["parking"]["y"],i] for i in range(1,pstMapInfo["h_low"]+1)]
        for i in range(len(pstFlyPlane["astUav"])):
            pstFlyPlane["astUav"][i]["path"]=path
#            pstFlyPlane["astUav"][i]["flyTime"] = -1 #起飞时间点,删删删删删删删删删删删删删删删删
            pstFlyPlane["astUav"][i]["target_no"] = -1
            pstFlyPlane["astUav"][i]["flag"] = -1
            #新增
            value,capacity,charge = type2price(pstFlyPlane["astUav"][i]["type"],UAV_price)
            pstFlyPlane["astUav"][i]["value"] = value
            pstFlyPlane["astUav"][i]["capacity"] = capacity
            pstFlyPlane["astUav"][i]["charge"] = charge
            pstFlyPlane["astUav"][i]["target_uav"] = -1 #要撞击的敌机 -1无,目的地[x,y]]
            
        pstFlyPlane["purchase_UAV"] = []
        FlyPlane = getResult(pstFlyPlane["astUav"])
        return FlyPlane,pstFlyPlane,enemyInfo
    
    
    flyH = pstMapInfo["h_low"]
    h_high = pstMapInfo["h_high"]
    goods = pstMatchStatus["goods"]
    curTime = pstMatchStatus["time"] 
    maps = pstMapInfo["map"]
    building = pstMapInfo["building"]
    parking = pstMapInfo["parking"]
    enemys = pstMatchStatus["UAV_enemy"]
  
    
    if curTime == 1:        
        enemyInfo=copy.deepcopy(enemys)
        for i in range(len(enemyInfo)):
            enemyInfo[i]["falg"]=-1#-1未定义
            enemyInfo[i]["Uvalue"]=type2value(enemyInfo[i]["type"],UAV_price) #UAV价值
            enemyInfo[i]["Gvalue"]=0 #货物价值
            
        enemyAbove = check_enemyAbovePark(enemys,parking,flyH)
        pstFlyPlane["astUav"] = updata_uavState(pstMatchStatus["UAV_we"],pstFlyPlane["astUav"])
        pstFlyPlane = next_step(pstFlyPlane,flyH,goods,curTime,maps,building,enemys,UAV_price,parking,enemyAbove,enemyInfo)
                   
        FlyPlane = getResult(pstFlyPlane["astUav"])
        return FlyPlane,pstFlyPlane,enemyInfo
    
    
    if curTime > 1:
#        enemyInfo = update_enemyInfo(enemys,enemyInfo,flyH,goods,UAV_price,pstFlyPlane["astUav"])
        
        pstFlyPlane["astUav"] = addUAV(pstFlyPlane["astUav"],pstMatchStatus["UAV_we"],parking,flyH,UAV_price)
        
        curUAVs = copy.deepcopy(pstFlyPlane["astUav"])
        
        uavs=pstFlyPlane["astUav"]
        otherUAVs,oterGoods,abovePark=otherIfo(uavs,goods,parking)#未起飞uav，未选择的good
        enemyAbove = check_enemyAbovePark(enemys,parking,flyH)
        abovePark = check_abovePark(uavs,parking,flag=6)
        if len(otherUAVs)>0:#有未起飞的
            if enemyAbove:#敌人在我方机场上方
#            if curTime<50:
                count = countFlag5(pstFlyPlane["astUav"])
                if count ==0:
                    low_price = sorted(UAV_price, key = lambda x:x["value"], reverse = False)[0]["value"]
                    minUAV = []
                    for u in otherUAVs:
                        if u["value"]<=low_price:
                            minUAV.append(u)
                    if minUAV:
                        firstUAV = minUAV[0]
                        pstFlyPlane = set_uav(firstUAV, pstFlyPlane, flag=5,target_no=-1)
                    
                        init = [parking["x"],parking["y"]]
                        goal=enemyPark
                        path=[[init[0],init[1],i] for i in range(1,flyH)]
                        pathA = make_path(init,goal,maps,building,flyH)
                        path=path+pathA
                        path.append([enemyPark[0],enemyPark[1],flyH-1])
                    
                        i=no2index(firstUAV["no"],pstFlyPlane["astUav"])
                        pstFlyPlane["astUav"][i]["path"]=path
                    
            elif not abovePark:
                uav_good = pick_first_Uav(otherUAVs,oterGoods,curTime,flyH,parking)
                if uav_good:
                    firstUAV = uav_good[0]
                    target_no = uav_good[1]
                    pstFlyPlane = set_uav(firstUAV, pstFlyPlane, flag=0,target_no=target_no)
                    path=[[pstMapInfo["parking"]["x"],pstMapInfo["parking"]["y"],i] for i in range(1,flyH+1)]
                    for i in  range(len(pstFlyPlane["astUav"])):
                        if pstFlyPlane["astUav"][i]["no"]==firstUAV["no"]:
                            pstFlyPlane["astUav"][i]["path"]=path
                    
        pstFlyPlane["astUav"] = updata_uavState(pstMatchStatus["UAV_we"],pstFlyPlane["astUav"])
        
        otherGoods = get_otherGoods(pstFlyPlane["astUav"],goods)
        
        #购买UAV
#        if enemyAbove:
        if curTime<150:#150
            purchase_UAV = buyMinUAV(UAV_price,pstMatchStatus["we_value"])             
        elif enemyAbove:
            purchase_UAV = buyMinUAV(UAV_price,pstMatchStatus["we_value"])   
        else:
            purchase_UAV = buyUAV(UAV_price,pstMatchStatus["we_value"],otherGoods,parking,flyH,curTime)

        
        enemyInfo = update_enemyInfo(enemys,enemyInfo,flyH,goods,UAV_price,pstFlyPlane["astUav"])
        #攻击
        canUse=0
        for u in pstFlyPlane["astUav"]:
            if u["status"]!=1:
                canUse+=1
        if canUse>3:
            pstFlyPlane["astUav"] = attackEnemy(pstFlyPlane["astUav"],enemyInfo,goods,maps,building,flyH)
        
        #下一步
        pstFlyPlane = next_step(pstFlyPlane,flyH,goods,curTime,maps,building,enemys,UAV_price,parking,enemyAbove,enemyInfo)
        nextUAVs = copy.deepcopy(pstFlyPlane["astUav"])
    
        #处理与敌方的碰撞
        nextUAVs = deal_enemyMeet(curUAVs,nextUAVs,enemys,UAV_price,goods,maps,flyH,h_high)
        pstFlyPlane["astUav"] = copy.deepcopy(nextUAVs)#????
  
        #处理我方的碰撞
        weMeet = check_weMeet(curUAVs,nextUAVs)
        if weMeet:
            nextUAVs = deal_weMeet(curUAVs,nextUAVs,weMeet,flyH,h_high,maps)
            pstFlyPlane["astUav"] = nextUAVs
#            print("weMeet:",weMeet)
        
        
        pstFlyPlane["purchase_UAV"] = purchase_UAV
        FlyPlane = getResult(pstFlyPlane["astUav"])                
        return FlyPlane,pstFlyPlane,enemyInfo