# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 23:39:08 2018

@author: peng
"""
#import random
#import pandas as pd
import time
import numpy as np
#import matplotlib.pyplot as plt

delta = [[-1,-1],#左上
         [-1, 0], #正上
         [-1, 1],#右上
         [ 0,-1], #左
         [ 0, 1], #右
         [ 1,-1], #左下
         [ 1, 0], #正下
         [ 1, 1]] #右下

# A* 算法
def search(grid,start,goal,Height,Width,flyH):
    '''
    Params:
        #grid: np.array,int地图信息 0可通行 1不可通行
        #start：list,起点,[x,y]
        #goal：list,目的地,[x,y]
        #Height：int,地图行数
        #Width：int，地图列数
    return:
        #path:list,起点到目的地最短路径，[[x0,y0],[x1,y1],...]

    '''
    closed = [[0  for col in range(Width)] for row in range(Height)]
    closed[start[0]][start[1]] = 1
 
    expand = [[-1  for col in range(Width)] for row in range(Height)]
    action = [[-1  for col in range(Width)] for row in range(Height)]
    
    cost = 1
    #初始化cheuristic
    heuristic=np.zeros((Height,Width))
    for rr in range(Height):
        for cc in range(Width):
            dist=abs(rr-goal[0])+abs(cc-goal[1])
            heuristic[rr][cc]=dist
#    heuristic=abs(heuristic-goal[0])+abs(heuristic-goal[1])
#    heuristic=((heuristic-goal[0])**2+(heuristic-goal[1])**2)**0.5/(2**0.5)
    r = start[0]
    c = start[1]

    g = 0
    h = heuristic[r][c]
    f = g+h
 
    opened = [[f, g, r, c]]
 
    found = False  # flag that is set when search is complete
    resign = False # flag set if we can't find expand
    count = 0
     
    while not found and not resign:
        if len(opened) == 0:
            resign = True
            return 'Fail'
        else:
            opened.sort()
            opened.reverse()
            next_p = opened.pop()
             
            r = next_p[2]
            c = next_p[3]
            g = next_p[1]
            f = next_p[0]
            expand[r][c]= count
            count += 1
             
            if r == goal[0] and c == goal[1]:
                found = True
            else:
                for i in range(len(delta)):
                    r2 = r + delta[i][0]
                    c2 = c + delta[i][1]
                  
                    if r2 >= 0 and r2 < Height and c2 >=0 and c2 < Width :
                        if closed[r2][c2] == 0 and grid[r2][c2] == 0:
                            g2 = g + cost
                            f2 = g2 + heuristic[r2][c2]
                            opened.append([f2, g2, r2, c2])
                            closed[r2][c2] = 1
                                 
                            # Memorize the sucessfull action for path planning
                            action[r2][c2] = i
            
#    print('\nA* Result:')

    #回溯路径
    path=[]
    while r != start[0] or c != start[1] :
        r2 = r-delta[action[r][c]][0]
        c2 = c-delta[action[r][c]][1]
        
        r = r2
        c = c2

        # Path
        path.append([r2, c2,flyH])
    path.reverse()
    path.append([goal[0],goal[1],flyH])
    return path 

 
# 网格制作
def make_grid(maps,building,h):
    '''
    Params:
        #maps: dict,地图信息 x,y,z
        #building：dict,建筑物信息
        #h：int,截取地图的高度
    return:
        #Height：int,地图行数
        #Width：int，地图列数
        #grid:array,高度为h的网格

    '''
    Height = maps["x"] #行 x
    Width = maps["y"] #列 y
    grid=np.zeros((Height,Width),dtype=int)

    for e in building:
        if h<=e["h"]-1:
            grid[e["x"]:(e["x"]+e["l"]), e["y"]:(e["y"]+e["w"])]=1
    
    return Height,Width,grid

def make_path(init,terminal,maps,building,flyH):
    Height,Width,grid=make_grid(maps,building,flyH)
    return search(grid,init,terminal,Height,Width,flyH)
    

#if __name__ == "__main__":
#    '''
#    Width = 5 #列 y
#    Height = 4 #行 x
#    Grid = [[0, 0, 0, 1, 0],
#            [0, 0, 0, 1, 0],
#            [0, 1, 1, 0, 0],
#            [0, 0, 1, 0, 0]]
#    '''
#    tic=time.time()
#     
#    maps={'x': 20, 'z': 10, 'y': 20}#地图信息
#    #xy表示建筑物的起始位置,l表示长度，w表示宽度，h表示高度,因此位置为x->x+l-1, y->y+w-1
#    building= [{'x': 2, 'h': 8, 'w': 14, 'l': 1, 'y': 3}, 
#               {'x': 3, 'h': 9, 'w': 1, 'l': 2, 'y': 9}, 
#               {'x': 5, 'h': 5, 'w': 14, 'l': 1, 'y': 3}, 
#               {'x': 9, 'h': 6, 'w': 14, 'l': 1, 'y': 3}, 
#               {'x': 13, 'h': 6, 'w': 14, 'l': 1, 'y': 3}, 
#               {'x': 14, 'h': 8, 'w': 2, 'l': 1, 'y': 6}, 
#               {'x': 15, 'h': 8, 'w': 1, 'l': 1, 'y': 5}, 
#               {'x': 16, 'h': 7, 'w': 1, 'l': 1, 'y': 4}, 
#               {'x': 17, 'h': 7, 'w': 1, 'l': 1, 'y': 3}, 
#               {'x': 15, 'h': 9, 'w': 2, 'l': 1, 'y': 8}, 
#               {'x': 16, 'h': 9, 'w': 2, 'l': 1, 'y': 10}, 
#               {'x': 17, 'h': 6, 'w': 2, 'l': 1, 'y': 12}, 
#               {'x': 18, 'h': 7, 'w': 2, 'l': 1, 'y': 14}, 
#               {'x': 19, 'h': 8, 'w': 2, 'l': 1, 'y': 16}]
#    h_low =7   #飞行最低高度
#
#    init = [0, 16]
#    terminal = [12,16]
#    Height,Width,grid=make_grid(maps,building,h_low)
#    path=search(grid,init,terminal,Height,Width,h_low)
##    path=make_path(init,terminal,maps,building,h_low)
#    toc=time.time()
#    print(path)
#    print('run time/ms:',(toc-tic)*1000)
#
#    plt.subplot(121)
#    plt.imshow(grid)
#    for i in path:
#        if grid[i[0],i[1]]==1:
#            print(i)
#        grid[i[0],i[1]]=2
#    plt.subplot(122)
#    plt.imshow(grid)
#    plt.show()



    
