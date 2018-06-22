本人第一个github 项目，代码为海康威视2018软件精英挑战赛复赛时候的比赛代码。复赛在初赛的基础上增加电量内容，该代码在初赛基础上（初赛排前11）增加电量功能，没进复赛（尴尬），哈哈。。。代码能力有限，酌情观看，欢迎指点

### 思路
'''
无人机以捡货为主，辅以防守和攻击，充满电才起飞。
无人机的下一步规划：将无人机划分为多个状态，包括上升、取货、送货、返回充电、攻击敌方停机坪、攻击敌方价值大的无人机等等，路径根据状态改变并存起来，下一步直接pop掉。
碰撞检测与处理：检测我方下一步是否将要与敌方当前步有碰撞的可能；检测我方无人机相互碰撞的可能。
攻击：检测敌机状态，并根据敌机价值派出我方廉价并空闲的无人机与之相撞
保护：敌机在我方停机坪的攻击，以及在送货目的地的攻击
'''

### 注意事项
```
Python版本：3.6.5
```
#### 1、入口__main__在main.py中，请不要变更此文件名，更不要将__main__入口变更至别的文件；
#### 2、您的依赖包请写在Makefile3文件中，注意M大写；
#### 3、Makefile3文件格式：
```
每行一个依赖包
依赖包格式：库名字==版本号，例如numpy==1.14.2
```
#### 4、评测命令：python3 main.py 39.106.111.130 4010 ABC123DEFG
```
参数1：39.106.111.130，是裁判服务器的IP，您在本地调试时，可在“我的对战”中获取；正式评测时，由评测调度程序生成；
参数2：4010，是裁判服务器允许您连接的端口，您在本地调试时，可在“我的对战”中获取；正式评测时，由评测调度程序生成；
参数3：字符串，是本次运行的令牌，以便校验您的资格，您在本地调试时，可在“我的对战”中获取；正式评测时，由评测调度程序生成。
```
#### 5、评测系统已经安装的依赖包
```
numpy==1.14.2
scipy==1.0.1
matplotlib==2.2.2
scikit-learn==0.19.1
simpleai==0.8.1
tensorflow==1.7.0
注意，由于正式评测时每位选手只有8核16G的单台服务器，请谨慎使用机器学习框架中的分布式功能。
```
