# p2pQA-backend
 backend of p2pQA



# 文件结构

```python
p2pQA # 项目文件夹
|-manage.py
|-p2pQA # 项目主目录，主要是配置文件和路由文件
  |-__pycache__
  |-__init__.py
  |-settings.py # 配置文件
  |-urls.py # 路由
  |-wsgi.py
|-qabroadcast # app 文件夹
  |-__pycache__
  |-migrations # 数据库同步记录
  |-models.py # 数据库配置 将数据表转化为python对象 以及同步数据库
  |-broadcast.py # 提问回答功能  
  |-account.py # 登录注册功能
  |-adminOP # 某些特殊管理员操作
  |-... #其他自动创建未做修改的文件
```

