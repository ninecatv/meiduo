from django.db import models

from meiduo_mall.utils.models import BaseModel
from users.models import User
# Create your models here.


class QQAuthUser(BaseModel):
    """QQ登陆用户数据"""
    user = models.ForeignKey(User, verbose_name='QQ关联用户', on_delete=models.CASCADE)
    openid = models.CharField(verbose_name='QQ用户唯一标识', max_length=64, db_index=True)  # db_index = True　　数据库索引

    class Meta:
        db_table = 'tb_qq_oauth'
        verbose_name = 'qq登陆用户数据'
        verbose_name_plural = verbose_name
