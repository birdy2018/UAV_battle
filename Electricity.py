# -*- coding: utf-8 -*-
"""
Created on Tue Jun  5 10:55:08 2018

@author: peng
"""
from Astar import make_path
#from Algorith2 import getGood,type2value,no2index
import copy

#将no标签转为列表索引，找不到的返回-1        
def no2index(no,lis):
    for i in range(len(lis)):
        if lis[i]["no"]==no:
            return i
    return -1

#从goods中选择no的good，没有返回空 
def getGood(no,goods):
    for g in goods:
        if g["no"]==no:
            return g
    return {}

#UAV转为价值
def type2value(Type,UAV_price):
    value=0
    for p in UAV_price:
        if p["type"]==Type:
            value = p["value"]
    return value

def type2price(Type,UAV_price):
    value = 0
    capacity = 0
    charge = 0
    for p in UAV_price:
        if p["type"]==Type:
            value = p["value"]
            capacity = p["capacity"]
            charge = p["charge"]
    return value,capacity,charge

def power_estimate(init,terminal,maps,building,flyH,Gweight):
    pathA = make_path(init,terminal,maps,building,flyH)
    len_s2e = (flyH-1)*2+len(pathA)
    power = (len_s2e+2)*Gweight #误差2
    return power
'''
class Stack(object):
    def __init__(self,size=10):
        self.items=[]
        self._maxSize=size
    
    def isEmpty(self):
        return self.items==[]
    
    def getTop(self):
        return self.items[-1]
    
    def push(self,item):
        if len(self.items)>=self._maxSize:
            self.items.pop(0)
        self.items.append(item)
    
    def pop(self):
        return self.items.pop()
'''

#判断当前位置是否有货pos=[x,y]
def check_haveGood(pos,goods,start=True):
    haveGood = False
    gValue = 0
    for g in goods:
        if start:
            if g["start_x"]==pos[0] and g["start_y"]==pos[1]:
                haveGood = True
                gValue = g["value"]
                break
        else:
            if g["end_x"]==pos[0] and g["end_y"]==pos[1]:
                haveGood = True
                gValue = g["value"]
                break
    return haveGood,gValue

#检测敌机是否在放置货物位置            
def enemy_on_goodEnd(ei,e,uavs,goods,flyH):
    onEnd = False
    Gvalue = 0
    onEndxy = False
    
    for u in uavs:
        if u["flag"]==4 and u["status"]!=1:#送货状态，未毁坏
            good = getGood(u["target_no"],goods)
            if good:
                if e["x"]==good["end_x"] and e["y"]==good["end_y"]:
                    Gvalue = good["value"]
                    onEndxy = True
                    break
    if e["z"]<flyH and onEndxy:
        onEnd = True
    elif e["z"]==flyH and onEndxy and [e["x"],e["y"],e["z"]]==[ei["x"],ei["y"],ei["z"]]:
        onEnd = True
    return onEnd,Gvalue 

def update_enemyInfo(enemys,enemyInfo,flyH,goods,UAV_price,uavs):
    newInfo=[]
    for e in enemys:#当前
        found = False
        for ei in enemyInfo:#之前时刻
            if e["no"]==ei["no"]:#能匹配到指定的no
                if e["z"]<flyH and (ei["z"]-e["z"])==1 and e["goods_no"]==-1: #下降趋势，未装货，
                    haveGood,gValue= check_haveGood([e["x"],e["y"]],goods,start=True)
                    if haveGood :
                        ei["flag"]=0  #取货下降
                    else:
                        ei["flag"]=-1
                    ei["Gvalue"] = gValue
                    
                elif ((e["z"]<flyH and (ei["z"]-e["z"])==-1 and e["goods_no"]!=-1) or 
                      (ei["goods_no"]==-1 and e["goods_no"]!=-1)): #上升趋势，已装货，或无货到有货
                    ei["flag"]=1  #送货上升
                    good = getGood(e["goods_no"],goods)
                    ei["Gvalue"] = good["value"]
                
                elif e["z"]>=flyH and e["goods_no"]!=-1:#水平飞行，已装货
                    ei["flag"]=2  #送货途中
                    good = getGood(e["goods_no"],goods)
                    ei["Gvalue"] = good["value"]
                
                elif e["z"]<flyH and (ei["z"]-e["z"])==1 and e["goods_no"]!=-1: #下降趋势，已装货
                    ei["flag"]=3  #送货下降
                    good = getGood(e["goods_no"],goods)
                    ei["Gvalue"] = good["value"]
                    
                elif ((e["z"]<flyH and (ei["z"]-e["z"])==-1 and e["goods_no"]==-1) or
                    (ei["goods_no"]!=-1 and e["goods_no"]==-1)):#上升趋势，未装货,或有货到无货
                    ei["flag"]=4  #空载上升
                    ei["Gvalue"] = 0
              
                else:
                    ei["flag"]=-1 #未定义
                    ei["Gvalue"] = 0
                    
                if ei["flag"]==-1:
                    onEnd,Gvalue = enemy_on_goodEnd(ei,e,uavs,goods,flyH)
                    if onEnd:
                        ei["flag"]=5 #敌机堵截放货点
                        ei["Gvalue"] = Gvalue

                ei["x"]=e["x"]
                ei["y"]=e["y"]
                ei["z"]=e["z"]
                ei["goods_no"]=e["goods_no"]
                ei["remain_electricity"]=e["remain_electricity"]
                ei["status"] = e["status"]
                newInfo.append(ei)
                found = True
                break
        if not found:
            temp = copy.deepcopy(e)
            temp["flag"]=-1 #-1未定义
            temp["Uvalue"]=type2value(temp["type"],UAV_price) #UAV价值
            temp["Gvalue"]=0 #货物价值
            newInfo.append(temp)
            
    return newInfo

def choose_uav_base_enemy(enemy,uavs,goods,flyH):
    if not uavs:
        return 0 #没uavs可选
    choise=[]
    for uav in uavs:
        if uav["flag"]==1 or uav["flag"]==6 and uav["z"]>=flyH and uav["target_uav"]==-1:
            curPos=[uav["x"],uav["y"],uav["z"]]
            if enemy["flag"]==2:
                good = getGood(enemy["goods_no"],goods)
                goal = [good["end_x"],good["end_y"]]
            else:
                goal = [enemy["x"],enemy["y"]]
            
            if uav["target_no"]!=-1:
                good = getGood(uav["target_no"],goods)
                if good:
                    myValue = good["value"]+uav["value"]
                else:
                    myValue = uav["value"]
            else:
                myValue = uav["value"]
            
            enemyValue = enemy["Gvalue"]+enemy["Uvalue"]
            
            if goal[0]==curPos[0] or goal[1]==curPos[1]:
                shorcut_dis = abs(goal[0]-curPos[0]) + abs(goal[1]-curPos[1])+abs(curPos[2]-flyH)
            else:
                shorcut_dis = ((goal[0]-curPos[0])**2+(goal[1]-curPos[1])**2)**0.5/(2**0.5)+abs(curPos[2]-flyH)
            
            len_dis=-1
            if enemy["flag"]==0 or enemy["flag"]==3:
                len_dis = enemy["z"]+flyH
            elif enemy["flag"]==1 or enemy["flag"]==4:
                len_dis = abs(flyH - enemy["z"])
            elif enemy["flag"]==2:
                if goal[0]==enemy["x"] or goal[1]==enemy["y"]:
                    len_dis = abs(goal[0]-enemy["x"]) + abs(goal[1]-enemy["y"])+abs(enemy["z"]-flyH)
                else:
                    len_dis = ((goal[0]-enemy["x"])**2+(goal[1]-enemy["y"])**2)**0.5/(2**0.5)+abs(enemy["z"]-flyH)
            
            if enemy["flag"]==5:
                if myValue < enemyValue:
                    choise.append([uav["value"],uav,goal,shorcut_dis])
            else:
                if myValue+int(0.25*myValue)<enemyValue and shorcut_dis<=len_dis:
                    choise.append([uav["value"],uav,goal,shorcut_dis])
               
    if choise:
        choise=sorted(choise, key = lambda x:(x[0],x[3]), reverse = False) #升序
        return choise[0][1],choise[0][2]
    else:
        return {},[]

def isOnAttack(enemyNo,uavs):
    onAttack = False
    dis = 0
    for u in uavs:
        if u["status"]!=1 and enemyNo==u["target_uav"]:
            onAttack = True
            dis = len(u["path"])
            break
    return onAttack,dis

def get_otherEnemy(uavs,enemyInfo):
    otherEnemy=[] #未被选中攻击的敌机
    target_uav=[]
    for u in uavs:
        if u["status"]!=1 and u["target_uav"]!=-1:
                target_uav.append(u["target_uav"])
    if target_uav:
        for e in enemyInfo:
            if e["no"] not in target_uav:
                otherEnemy.append(e)
    else:
        otherEnemy=enemyInfo
    return otherEnemy
            
def attackEnemy(uavs,enemyInfo,goods,maps,building,flyH):
    if not enemyInfo:
        return uavs
    
    otherEnemy = get_otherEnemy(uavs,enemyInfo)
    if not otherEnemy:
        return uavs
    
    for e in otherEnemy:
        if e["flag"]!=-1 and e["status"] ==0 :#可攻击
            onAttack,_ = isOnAttack(e["no"],uavs)
            if not onAttack:
                uav,goal = choose_uav_base_enemy(e,uavs,goods,flyH)
                if uav:
                    i=no2index(uav["no"],uavs)
                    uavs[i]["target_uav"]=e["no"]
                    uavs[i]["flag"]=7
                    
                    init = [uav["x"],uav["y"]]
                    path = make_path(init,goal,maps,building,uav["z"])
                    path.pop(0)
                    temp=list(range(0,uav["z"]))
                    temp=temp[::-1]
                    pathB=[[goal[0],goal[1],i] for i in temp]
                    path=path+pathB
                    
                    uavs[i]["path"]=path
    return uavs

#if __name__=="__main__":
#    path = Stack()
#    for i in range(133):
#        path.push([1,2,3])
#    path.push([4,5,6])
        