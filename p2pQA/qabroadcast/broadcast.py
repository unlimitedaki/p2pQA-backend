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

# 提出问题
@csrf_exempt
@transaction.atomic
def query(request):
    response = HttpResponse()
    code = 200
    message = {}
    if request.method == "POST":
        try:  
            user = request.COOKIES['email']#user = email,在数据表中
            req = json.loads(request.body.decode("utf-8"))
            # print(req)
            data = models.Question()
            data.text = req['question']
            data.status = 0
            data.uploadtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data.user = user
            data.save()
            message["detail"] = "提问成功"
            code = 200
        except Exception as ex:
            message["detail"] = str(ex)
            code = 406
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code
    return response

# 回答问题
@csrf_exempt
@transaction.atomic
def answer(request):
    response  = HttpResponse()
    code = 200
    message = {}
    if request.method == "POST":
        try:
            user = request.COOKIES['email']
            req = json.loads(request.body.decode("utf-8"))
            # print(req)
            data = models.Answer()
            data.questionid = req['questionid']
            data.text = req['answer'] 
            data.uploadtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data.status = 0
            data.user = user
            data.save()
            # question update
            question = models.Question.objects.select_for_update().get(questionid = req['questionid'])
            question.status = 1
            question.save()
            message['detail'] = "回答成功"
            code = 200
        except Exception as ex:
            message['detail'] = str(ex)
            code = 406
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code
    return response

# 不是接口，是给下一个接口用的函数
@transaction.atomic
def alreadyanswered(data,user):
    if data.status == 0:
        return False
    answers = models.Answer.objects.filter(questionid = data.questionid)
    for answer in answers:
        if answer.user == user:
            return True
    return False
    
# 问题列表
# 目前规则：列表中只包括：未被采纳(status != 2)，非本用户提出的,本用户未回答过的问题
@csrf_exempt
@transaction.atomic
def questions(request):
    response  = HttpResponse()
    code = 200
    message = {}
    if request.method == "GET":
        try:
            user = request.COOKIES['email']
            data = models.Question.objects.select_for_update().all().order_by('-uploadtime')
            questions = []
            for d in data:
                if d.user != user and d.status!=2 and not alreadyanswered(d,user):
                    question = {}
                    question["question"] = d.text
                    question["questionid"] = d.questionid
                    questions.append(question)
            message["questions"] = questions
        except Exception as ex:
            message['detail'] = str(ex)
            code = 406
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code
    return response

# 一个问题的答案
# 目前规则，只返回一个问题的未被采纳的答案和已被采纳的答案（被拒绝的不再显示）
@csrf_exempt
@transaction.atomic
def answers(request):
    response  = HttpResponse()
    code = 200
    message = {}
    if request.method == "POST":
        try:
            req = json.loads(request.body.decode("utf-8"))
            questionid = req["questionid"]
            # print(req)
            data = models.Answer.objects.select_for_update().filter(questionid = questionid).order_by('-uploadtime')
            answers = []
            for d in data:
                if d.status != -1:
                    answer = {}
                    answer["answer"] = d.text
                    answer["answerid"] = d.answerid
                    answers.append(answer)
            message["answers"] = answers
        except Exception as ex:
            message['detail'] = str(ex)
            code = 406
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code
    return response

# 提出问题记录
# 暂时按照问题提出时间倒序排序，之后需要改成问题的最后回答时间排序(第一次测试结束后，可以通过在问题表里面加入一个最新回答时间项作为排序标准，可以避免多次查询数据库)
@csrf_exempt
def querylist(request):
    response = HttpResponse()
    code = 200
    content = {}
    if request.method == "GET":
        try:
            email = request.COOKIES['email']
            print("getemail"+email)
            data = models.Question.objects.filter(user = email).order_by('-uploadtime')
            querylist = []
            if data == None:
                content['querylist'] = []
                content['detail'] = "尚未提出问题"
            else:
                for d in data:
                    query = {}
                    query["question"] = d.text
                    query["questionid"] = d.questionid
                    query["status"] = d.status
                    querylist.append(query)
                content['querylist'] = querylist
                # print(content)
        except Exception as ex:
            content['detail'] = str(ex)
            code = 406
    response.content = json.dumps(content,ensure_ascii=False)
    response.status_code = code
    return response

# 统计提问数量和已被回答的数量
@csrf_exempt
def queryAmount(request):
    response = HttpResponse()
    code = 200
    content = {}
    if request.method == "GET":
        try:
            email = request.COOKIES['email']
            data = models.Question.objects.filter(user = email).order_by('-uploadtime')
            querylist = []
            cqueries = 0
            canswered = 0
            if data == None:
                content['queries'] = cqueries
                content['answered'] = canswered
            else:
                for d in data:
                    if d.status == 1 or d.status == 2:
                        cqueries +=1
                        canswered += 1
                    elif d.status == 0:
                        cqueries += 1
                content['queries'] = cqueries
                content['answered'] = canswered
                # print(content)
        except Exception as ex:
            content['detail'] = str(ex)
            code = 406
    response.content = json.dumps(content,ensure_ascii=False)
    response.status_code = code
    return response

# 统计回答的数量和被采纳的数量
@csrf_exempt
def answerAmount(request):
    response = HttpResponse()
    code = 200
    content = {}
    if request.method == "GET":
        try:
            email = request.COOKIES['email']
            data = models.Answer.objects.filter(user = email).order_by('-uploadtime')
            querylist = []
            answers = 0
            accepted = 0
            if data == None:
                content['answers'] = answers
                content['accepted'] = accepted
            else:
                for d in data:
                    if d.status == 1:
                        answer +=1
                        canswered += 1
                    elif d.status == 0 or d.status == -1:
                        answer += 1
                content['answers'] = answers
                content['accepted'] = accepted
                # print(content)
        except Exception as ex:
            content['detail'] = str(ex)
            code = 406
    response.content = json.dumps(content,ensure_ascii=False)
    response.status_code = code
    return response

# 接受答案
# 目前规则：一个答案一旦被接受，将会拒绝其他答案
@csrf_exempt
@transaction.atomic
def acceptAnswer(request):
    response = HttpResponse()
    code = 200
    content = {}
    if request.method == "POST":
        try:
            req = json.loads(request.body.decode("utf-8"))
            answerid = req['answerid']
            #this answer is accepted
            answer = models.Answer.objects.select_for_update().get(answerid = answerid)
            questionid = answer.questionid
            answer.status = 1
            answer.save()
            #and this question should be closed
            question = models.Question.objects.select_for_update().get(questionid = questionid)
            question.status =2
            question.save()
            # of course other answers should be declined
            # print(answer.text)
            remainanswers = models.Answer.objects.select_for_update().filter(questionid = questionid)
            for answer in remainanswers:
                if answer.answerid != answerid:
                    answer.status = -1
                    answer.save()
                    # print(answer.answerid)
            content['detail'] = "回答已接受"
        except Exception as ex:
            content['detail'] = str(ex)
            code = 406
    response.content = json.dumps(content,ensure_ascii=False)
    response.status_code = code
    return response   

@csrf_exempt
@transaction.atomic
def reject(request):
    response = HttpResponse()
    code = 200
    content = {}
    if request.method == "POST":
        try:
            req = json.loads(request.body.decode("utf-8"))
            answerid = req['answerid']
            #this answer is accepted
            answer = models.Answer.objects.select_for_update().get(answerid = answerid)
            questionid = answer.questionid
            question = models.Question.objects.get(questionid = questionid)
            if question.status == 2:
                content['detail'] = "问题已关闭"
                code = 406
            else:
                answer.status = -1
                answer.save()
                content['detail'] = "回答已拒绝"
        except Exception as ex:
            content['detail'] = str(ex)
            code = 406
    response.content = json.dumps(content,ensure_ascii=False)
    response.status_code = code
    return response   