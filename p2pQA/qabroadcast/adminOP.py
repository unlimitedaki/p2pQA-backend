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