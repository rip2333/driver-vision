#coding=utf-8
#
# Copyright (C) 2014  NianNian TECH Co., Ltd. All rights reserved.
# Created on Nov 8, 2015, by Junn
#
from vision.models import Demo, Block, Trial
from vision.algos import StepProcess, RstepProcess, NstepProcess, SstepProcess,\
    VstepProcess
from utils import times

'''
试验线程类
'''

from config import *
import threading
from vision.trials import Board, WatchPoint

  
class DemoThread(threading.Thread):
    '''父类试验线程对象.  为初始参数, 路牌,注视点等的容器
    '''
    is_started = False              #实验进行状态, 默认为未开始
    signal = threading.Event()
    
    param = None      #数据库读取的参数对象  
    wpoint = None     #注视点
    board = None      #多路牌时为Board对象列表结构, 单路牌时为Board对象结构    
    
    def __init__(self, gui, param):
        threading.Thread.__init__(self)
        
        self.gui = gui
        self.param = param
        self.wpoint = WatchPoint()
        self.board = self.build_board()

    def run(self):
        print('Demo thread started')
        self.is_started = True              #实验进行状态, 默认为未开始
        self.control_demo()
        
    def build_board(self):
        '''需要子类重载'''
        #return Board(self.param.eccent, self.param.init_angle, self.wpoint.pos)
        return Board(self.param.eccent, self.param.init_angle)  
    
    def control_demo(self):
        '''控制刺激过程. 阶梯过程包括: 数量阈值, 尺寸阈值, 关键间距, 动态敏感度
        首先以 静态单路牌 为例...
        '''
        
        demo = self.save_demo() #以备后用
        road_seats, target_seats = self.param.get_road_seats()
        
        # 关键间距        
        self.trial_querylist = [] #缓存trial model对象, 用于批量存储数据
        for tseat in target_seats:
            block_data = {
                'demo': demo, 
                'tseat': tseat, 
                'ee': self.board.get_ee(tseat, self.wpoint), 
                'angle': self.board.get_angle(tseat, self.wpoint), 
                'cate': 'R', 
                'N': len(road_seats)-1, 'S': self.param.road_size, 'V': 0.0
            }
            block = self.create_block(**block_data)
            self.board.load_roads(road_seats, tseat, self.param.road_size)
            for i in range(STEPS_COUNT):
                trial_data = {
                    'block': block,  
                    'cate':  block.cate, 
                    'steps_value': ','.join(self.board.calc_target_flanker_spacings()), 
                    'target_road': self.board.get_target_road()
                }
                self.append_trial(trial_data)
                
                self.tmp_begin_time = times.now() #记录刺激显示开始时间
                self.gui.draw_all(self.board, self.wpoint) #刺激显示
                self.wait() #等待用户按键判断
                
                #用户按键唤醒线程后刷新路名    
                self.board.load_roads(road_seats, tseat, self.param.road_size) 
                if not self.is_update_step_value:   #不更新阶梯变量, 则直接进行第2次刺激显示
                    continue
                
                # 更新阶梯变量: R
                self.board.update_flanker_poses(self.is_left_algo)
                
        #批量保存block数据                            
        Trial.objects.bulk_create(self.trial_querylist)
        
#         # 数量阈值            
#         block_querylist = []
#         self.trial_querylist = []    
#         for d in self.target_seats:
#             block = self.create_block(demo) # (demo, tseat, eccent, angle, cate, N, S, R, V)
#             NstepProcess(block).execute()
#         Block.objects.bulk_create(block_querylist)
#         Trial.objects.bulk_create(self.trial_querylist) #??             
#             
#         # 尺寸阈值
#         block_querylist = []
#         self.trial_querylist = []  
#         for d in self.target_seats:
#             block = self.create_block(demo) # (demo, tseat, eccent, angle, cate, N, S, R, V)
#             SstepProcess(block).execute()
#         Block.objects.bulk_create(block_querylist)
#         Trial.objects.bulk_create(self.trial_querylist) #??              
            
            
        # 动态敏感度            
        #for d in self.target_seats:
        #    block = self.create_block(demo) # (demo, tseat, eccent, angle, cate, N, S, R, V)
        #    VstepProcess(block).execute()
        
            
    def handle_judge(self, is_correct):
        '''处理用户判断成功, called by key_pressed_method in gui
        @param is_correct:  按键判断是否正确.
        is_left_algo: 表示阶梯值新值计算类型, True表示按流程图左侧算法进行计算, 否则按右侧算法.
        is_update_step_value: 是否更新阶梯变量值, 判断成功后该标记值取反, 判断失败后更新阶梯变量值
        
        '''
        if is_correct:
            self.is_update_step_value = not self.is_update_step_value 
            self.is_left_algo = True
        else:
            self.is_update_step_value = True    #需要更新阶梯变量, 以进行下一次刺激显示 
            self.is_left_algo = False           #按右侧方式更新阶梯变量值                
        
    def is_judge_correct(self):
        '''返回用户按键判断是否正确'''
        self.current_trial.is_correct = self.board.is_target_road_real()
        self.current_trial.resp_cost = times.time_cost(self.tmp_begin_time)
        return self.current_trial.is_correct                  
            
    def build_step_process(self):
        return StepProcess()            
    
    def save_demo(self): #TODO: 更新demo对象...
        demo = Demo(param=self.param)
        demo.save()
        return demo   
    
    def create_block(self, **data): #TODO...
        '''进入阶梯循环过程之前调用该方法, 根据调整后的时间复杂度, 立即save不会影响性能'''
        block = Block(data)
        block.save()
        return block
    
    def append_trial(self, **data): 
        '''暂存trial数据对象'''
        trial = Trial(data)
        self.trial_querylist.append(trial)
        self.current_trial = trial         #current_trial属性变化是否会影响到最终save DB的值?
        
    def wait(self):
        '''重置线程flag标志位为False, 以使得signal.wait调用有效.   
        等待1.6s, 以待用户进行键盘操作判断目标路名真/假并唤醒  
        '''
        self.signal.clear()                   
        self.signal.wait(show_interval)   
        
    def awake(self):
        self.signal.set()  
        
        
class StaticSingleDemoThread(DemoThread):
    '''静态单路牌'''
    
    pass

class StaticMultiDemoThread(DemoThread):
    '''静态多路牌'''
    
    def build_board(self):
        #TODO... build multi boards
        return Board()
    
class DynamicSingleDemoThread(DemoThread):
    '''动态单路牌'''
    pass

class DynamicMultiDemoThread(DemoThread):
    '''动态多路牌'''
    pass
    
        