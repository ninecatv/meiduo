from django.db import models


class BaseModel(models.Model):
    """模型基类"""

    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)  # auto_now_add为创建时的时间，更新对象时不会有变动
    update_time = models.DateTimeField(verbose_name='修改时间', auto_now=True)  # auto_now无论是你添加还是修改对象，时间为你添加或者修改的时间

    class Meta:
        abstract = True  # abstract = True 表示此模型是一个抽象模型,将来迁移建表时,不会对它做迁移建表动作,它只用当其它模型的基类
