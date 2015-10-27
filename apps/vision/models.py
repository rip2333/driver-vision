#coding=utf-8
#
# Copyright (C) 2014  NianNian TECH Co., Ltd. All rights reserved.
# Created on Oct 19, 2015, by Junn
#

from core.models import BaseModel
from django.db import models
from utils import eggs, logs
from core.managers import BaseManager

class RoadManager(BaseManager):
    pass

class Road(BaseModel):
    name = models.CharField(u'路名', max_length=40, null=True, blank=True, default='') #作为医生时要显示真实姓名
    is_real = models.BooleanField(u'是真路名', default=False)
    
    is_valid = models.BooleanField(u'有效', default=True)
    

    objects = RoadManager()
    
    class Meta:
        verbose_name = u'路名'
        verbose_name_plural = u'路名'

    def __unicode__(self):
        return u'%s' % self.name
    
class TrialParamManager(BaseManager):
    pass   
    
class TrialParam(BaseModel):
    '''试验数据模型: 一次完整参数设置的试验'''
    
    road_num = models.IntegerField(u'路名条数',null=True, blank=True)
    
    is_tested = models.BooleanField(u'试验已执行', default=False)
    desc = models.CharField(u'描述', max_length=40, default='')

    #objects = TrialParamManager()
    
    class Meta:
        verbose_name = u'试验'
        verbose_name_plural = u'试验'

    def __unicode__(self):
        return u'%s' % self.name    
        

