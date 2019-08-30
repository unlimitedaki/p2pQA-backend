from django.shortcuts import render
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from . import models
import hashlib
import os
from django.db import transaction
from django.utils.encoding import smart_str

# 注册
@csrf_exempt
@transaction.atomic
def register(request):# request是前端发送的请求，包含请求类型(request.method),内容(request.body),cookies
    returnMessage = {}
    returnStatus = 401
    response = HttpResponse()# HttpResponse 是后端的回复，包含内容（response.content）,状态码(response.status_code)，cookies
    # HttpResponse会将request里的cookies原封不动地返回，除非后端进行了cookies更新
    if request.method == "POST":
        try:
            reqd = json.loads(request.body.decode('utf-8'))#这里我们使用了json格式的body，需要loads一下
            email = reqd['email']
            nickname = reqd['nickname']
            password = reqd['password']
            sameEmailUser = models.User.objects.filter(email = email)# 查找数据库
            if sameEmailUser :
                returnMessage['detail'] = "此邮箱已经被注册"
                returnStatus = 406
            elif nickname and password and email:
                new_user = models.User(email = email,nickname = nickname,password = password)# 新建数据对象，直接在初始化时保存数据
                new_user.accuracy = 0.0# 
                new_user.balance = 0
                new_user.score = 0
                new_user.rank = 0
                response.set_cookie('email',email)# 设置cookie
                token = hashlib.sha1(os.urandom(24)).hexdigest()
                new_user.token = token
                new_user.save()# 保存数据对象到数据库中
                response.set_cookie('token',token)
                returnMessage['detail']= "注册成功"
                returnStatus = 200#更新状态码
            else:
                returnMessage['detail'] = "表单内容有误"
                returnStatus = 406
        except Exception as ex:
            returnMessage['detail'] = str(ex)
            returnStatus = 406
    else:
        returnMessage['detail'] = "非post请求"
        returnStatus = 406
    response.status_code = returnStatus #设置状态码
    response.content = json.dumps(returnMessage,ensure_ascii=False)#设置回复内容
    return response # 这里返回的是一个HttpResponse,也可以返回一个网页(网页文件路径)，甚至是一个字符串

# 登录
@csrf_exempt
@transaction.atomic
def login(request):
    returnMessage = {}
    returnStatus = 200
    response = HttpResponse()
    try:
        if request.method == "POST":
            reqd = json.loads(request.body.decode("utf-8"))
            email = reqd['email']
            password = reqd['password']
            try:
                user = models.User.objects.get(email=email)
            except Exception as ex:
                user = None
            if not user:
                returnMessage['detail']= "用户未注册"
                returnStatus = 406
            elif password == user.password:
                returnMessage['detail'] = "登录成功"
                returnMessage['nickname'] = user.nickname
                returnMessage['email'] = user.email
                response.set_cookie('nickname',json.dumps(user.nickname))# 中文不支持latin-1，因此进行dump,前端需要loads
                response.set_cookie('email',email)
                token = hashlib.sha1(os.urandom(24)).hexdigest()
                # token= "token"
                user.token = token
                user.save()
                response.set_cookie('token',token)
            else:
                returnMessage['detail'] = "密码错误"
                returnStatus = 406

    except Exception as ex:
        returnMessage['detail'] = str(ex)
        returnStatus = 401
    response.status_code = returnStatus
    response.content = json.dumps(returnMessage,ensure_ascii=False)
    return response
    
# 不用管这个函数，估计不写了
@csrf_exempt
def logout(request):
    response = HttpResponse()
