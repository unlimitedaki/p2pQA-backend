from django.shortcuts import render
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from . import models
import hashlib
import os
from django.db import transaction
import time
import datetime

# 手动保存用户的问答记录
@csrf_exempt
def checkPoint(request):
    response = HttpResponse()
    code = 200
    message = {}
    if request.method == "GET":
        with open('checkPoints.log','a',encoding = 'utf-8') as f:
            users = models.User.objects.all()
            f.write("--Check Point-- time {:s}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            for user in users:
                questions = models.Question.objects.filter(user = user.email)
                qcnt = len(questions)
                qaedcnt = len(models.Question.objects.filter(user = user.email,status = 1))+len(models.Question.objects.filter(user = user.email,status = 2))
                acnt = len(models.Answer.objects.filter(user = user.email))
                aacccnt = len(models.Answer.objects.filter(user = user.email,status = 1))
                f.write("user:{:s}\t queries:{:d}\t answered queries:{:d}\t answers:{:d}\t answer accepted:{:d} \n".format(user.email,qcnt,qaedcnt,acnt,aacccnt))
        message['detail'] = 'ok'
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code
    return response

# 备份一下现在已经有的问答数据
# 有机会再导入回去，不过是不希望有机会了
@csrf_exempt
def backup(request):
    response = HttpResponse()
    code = 200
    message = {}
    if request.method == "GET":
        with open('p2pQAdata.json','w',encoding = 'utf8') as f:
            data = []
            # data = [{question:str,questionid:int,status:int,answers:[{answerid:int,answer:str,status:int},]},]
            questions = models.Question.objects.all()
            for q in questions:
                item = {}
                item['questionid'] = q.questionid
                item['questiontext'] = q.text
                item['status'] = q.status
                item['answers'] = []
                item['user'] = q.user
                answers = models.Answer.objects.filter(questionid = q.questionid)
                for a in answers:
                    ans = {}
                    ans['answerid'] = a.answerid
                    ans['text'] = a.text
                    ans['status'] = a.status
                    ans['uesr'] = a.user
                    item['answers'].append(ans)
                data.append(item)
            json.dump(data,f,ensure_ascii = False)
        with open('p2pQAuser.json','w',encoding = 'utf8') as f:
            userdata = []
            users = models.User.objects.all()
            for u in users:
                user = {}
                user['email'] = u.email
                user['nickname'] = u.nickname
                user['password'] = u.password
                userdata.append(user)
            json.dump(userdata,f,ensure_ascii=False)
    message['detail'] = 'ok'
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code    
    return response
            