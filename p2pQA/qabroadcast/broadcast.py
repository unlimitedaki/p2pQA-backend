from django.shortcuts import render
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
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
            data.lastestanswertime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            # update user socre
            curUser = models.User.objects.get(email = user)
            curUser.score += 1
            curUser.balance += 1
            curUser.save()
            # create answer
            data = models.Answer()
            data.questionid = req['questionid']
            data.text = req['answer'] 
            data.uploadtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data.status = 0
            data.user = user
            data.follow = 0
            data.save()
            # update question status
            question = models.Question.objects.select_for_update().get(questionid = req['questionid'])
            question.status = 1
            question.lastestanswertime = data.uploadtime
            question.save()
            message['detail'] = "回答成功"
            code = 200
        except Exception as ex:
            message['detail'] = str(ex)
            code = 406
    response.content = json.dumps(message,ensure_ascii=False)
    response.status_code = code
    return response

# 用不上了，已经被优化掉了
# @transaction.atomic
# def alreadyanswered(data,user):
#     if data.status == 0:
#         return False
#     answers = models.Answer.objects.filter(questionid = data.questionid)
#     for answer in answers:
#         if answer.user == user:
#             return True
#     return False
    
# 问题列表
# 目前规则：列表中只包括：未被采纳(status != 2)，非本用户提出的,本用户未回答过的问题
@csrf_exempt
def questions(request):
    response  = HttpResponse()
    code = 200
    message = {}
    if request.method == "GET":
        try:
            user = request.COOKIES['email']
            answeredQuestionids = [item['questionid'] for item in models.Answer.objects.filter(user = user).values('questionid')]
            followedQuestionids = [models.Answer.objects.get(answerid = item.answerid).questionid for item in models.Follow.objects.filter(follower = user)]
            excludeids = answeredQuestionids+followedQuestionids
            data = models.Question.objects.all().exclude(status = 2).exclude(user = user).exclude(questionid__in = excludeids).order_by('-uploadtime')
            # 这里做了一下优化，首先提取出本用户已经回答的所有问题的id
            # 然后exclude掉 状态关闭 + 本用户提出 + 已被本用户回答的问题
            message['questions'] = [{"question":item.text,"questionid":item.questionid,'user':models.User.objects.get(email = item.user).nickname,"time":str(item.uploadtime)} for item in data]
            # for d in data:
            #     question = {}
            #     question["question"] = d.text
            #     question["questionid"] = d.questionid
            #     questions.append(question)
            # message["questions"] = questions
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
            data = models.Answer.objects.select_for_update().filter(questionid = questionid).exclude(status = -1).order_by('-uploadtime')
            message["answers"] = [{"answer":item.text,"answerid":item.answerid,"follow":item.follow,"answertime":str(item.uploadtime),'user':models.User.objects.get(email = item.user).nickname} for item in data]
            # for d in data: 
                # answer = {}
                # answer["answer"] = d.text
                # answer["answerid"] = d.answerid
                # answers.append(answer)
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
            data = models.Question.objects.filter(user = email).order_by('-lastestanswertime')
            querylist = []
            if data == None:
                content['querylist'] = []
                content['detail'] = "尚未提出问题"
            else:
                content['querylist'] = [{"questions":item.text,"questionid":item.questionid,"status":item.status,"time":str(item.uploadtime)} for item in data]
                # print(content)
        except Exception as ex:
            content['detail'] = str(ex)
            code = 406
    response.content = json.dumps(content,ensure_ascii=False)
    response.status_code = code
    return response

#统计提问，回答，点赞，积分数据
@csrf_exempt
def statistics(request):
    response = HttpResponse()
    if request.method == "GET":
        try:
            user = request.COOKIES['email']
            stats = {}
            stats['queries'] = models.Question.objects.filter(user = user).count()
            stats['answeredQueries'] = models.Question.objects.filter(user = user,status__in = [1,2]).count()
            stats['answers'] = models.Answer.objects.filter(user = user).exclude(status = -2).count()
            stats['accepted'] = models.Answer.objects.filter(user = user,status = 1).count()
            stats['follows'] = models.Follow.objects.filter(answeruser = user).count()
            stats['score'] = models.User.objects.get(email = user).balance
            response.content = json.dumps(stats,ensure_ascii = False)
            response.status_code = 200
        except Exception as ex:
            response.content = json.dumps({"detail":str(ex)},ensure_ascii= False)
            response.status_code = 406
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
            data = models.Question.objects.filter(user = email)
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
            data = models.Answer.objects.filter(user = email)
            querylist = []
            answers = 0
            accepted = 0
            if data == None:
                content['answers'] = answers
                content['accepted'] = accepted
            else:
                for d in data:
                    if d.status == 1:
                        answers +=1
                        accepted += 1
                    elif d.status == 0 or d.status == -1:
                        answers += 1
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
            # update user score +3
            curUser = models.User.objects.get(email = answer.user)
            curUser.score += 3
            curUser.balance += 3
            curUser.save()
            #and this question should be closed
            question = models.Question.objects.select_for_update().get(questionid = questionid)
            question.status =2
            question.save()
            # of course other answers should be reject
            # print(answer.text)
            remainanswers = models.Answer.objects.select_for_update().filter(questionid = questionid).exclude(answerid = answerid)
            for answer in remainanswers:
                answer.status = -1
                answer.save()
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

# 人类的本质是复读机，停止思考选择盲从 == 
@csrf_exempt
@transaction.atomic
def follow(request):
    response = HttpResponse()
    if request.method == "POST":
        try:
            req = json.loads(request.body.decode("utf-8"))
            user = request.COOKIES['email']
            answer = models.Answer.objects.select_for_update().get(answerid = req['answerid'])
            follow = models.Follow(answerid = req['answerid'],questionid = answer.questionid,answeruser = answer.user,follower = user)
            follow.save()
            answer.follow += 1
            answer.save()
            response.content = json.dumps({'detail':"ok"},ensure_ascii = False)
            response.status_code = 200            
        except Exception as ex:
            response.content = json.dumps({'detail':str(ex)},ensure_ascii = False)
            response.status_code = 406
    return response

@csrf_exempt
def answerRecord(request):
    response = HttpResponse()
    if request.method == "GET":
        try:
            user = request.COOKIES['email']
            answers = models.Answer.objects.filter(user = user).exclude(status = -2)
            questions = [models.Question.objects.get(questionid = item.questionid) for item in answers]
            queryusers = [models.User.objects.get(email = item.user) for item in questions]
            answerrecords = [{"answerid":item.answerid,"answer":item.text,"question":questions[i].text,"user":queryusers[i].nickname,"answerType":"answer","answertime":str(item.uploadtime)} for i,item in enumerate(answers)]
            follows = models.Follow.objects.filter(follower = user)
            fanswers = [models.Answer.objects.get(answerid = item.answerid) for item in follows]
            fquestions = [models.Question.objects.get(questionid = item.questionid) for item in fanswers]
            answerusers = [models.User.objects.get(email = item.user) for item in fanswers]
            followrecords = [{"answerid":item.answerid,"answer":item.text,"question":fquestions[i].text,"user":answerusers[i].nickname,"answerType":"follow","answertime":str(item.uploadtime)} for i,item in enumerate(fanswers)]
            record = answerrecords + followrecords
            record = sorted(record,key = lambda record:record['answertime'],reverse = True)
            response.content = json.dumps({"answerRecord":record},ensure_ascii = False)
            response.status_code = 200
        except Exception as ex:
            response.content = json.dumps({"detail":str(ex)})
            response.status_code = 406
    return response

@csrf_exempt
def correct(request):
    response = HttpResponse()
    if request.method == "POST":
        try:
            print("try")
            req = json.loads(request.body.decode("utf-8"))
            answerid = req['answerid']
            newAnswerText = req['answer']
            answer = models.Answer.objects.get(answerid = answerid)
            answer.status = -2# 废弃原答案
            answer.save()
            newAnswer = models.Answer(text = newAnswerText,questionid = answer.questionid,status = 0,user = answer.user,follow = 0,uploadtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            newAnswer.save()
            response.content = json.dumps({"detail":"ok"},ensure_ascii = False)
            response.status_code = 200
        except Exception as ex:
            response.content = json.dumps({"detail":str(ex)},ensure_ascii= False)
            response.status_code = 406
    return response
