import datetime

from django.http import HttpResponse

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
from VoteApp.models import Candidate, User , UserVoteRecord, ChatRecord, VoteType


# 添加用户Ip
def addUser(hostname,ip):
	us = User()
	us.uName = hostname
	us.uIP = ip
	us.uComName = hostname
	us.save()

# 检查用户是否已经投票
def check(user,n,typeId,uRemark,times=1):
	# 当前用户当天对某候选者只能投一票
	uvr = UserVoteRecord.objects.filter(isDelete=0,uNameId=user[0].id,uTimes=times,uWhoId=n,uType=typeId,uDate=datetime.datetime.now().__format__('%Y-%m-%d'))
	# print('******测试*****')
	# print(uvr)
	# print('******测试*****')
	if uvr.exists():
		return 0
	else:
		addVoteRecord(user[0].uIP, n,typeId,uRemark,times)
		return 1


# 增加投票记录
def addVoteRecord(ip,n,typeId,uRemark="",times=1):
	# 添加投票记录
	us = User.objects.get(uIP=ip,isDelete=0)
	cs = Candidate.cmanager.get(id=n,isDelete=0)
	ut = VoteType.objects.get(id=typeId)
	uvr = UserVoteRecord()
	uvr.uNameId = us
	uvr.uWhoId = cs
	uvr.uType = ut
	uvr.uTimes =times
	uvr.uRemark = uRemark
	uvr.save()

# 获取用户Ip
def getUserIP(request):
	# 获取客户端IP
	if 'HTTP_X_FORWARDED_FOR' in request.META:
		return request.META['HTTP_X_FORWARDED_FOR']
	else:
		return request.META['REMOTE_ADDR']

# 检测用户是否存在表中
def getUser(request,n,typeId,uRemark='',times=1):
	# 获取用户IP
	ip = getUserIP(request)
	#从数据库中查询当前用户是否存在，当前IP作为查询条件
	us = User.objects.filter(uIP=ip,isDelete=0)
	# 当前用户存在
	if us.exists():
		# 检查当前用户是否对该候选者投了票
		return check(us,n,typeId,uRemark,times)
	# 添加当前IP
	addUser('guest'+ str(ip[ip.rfind('.')+1:]),ip)
	# 增加投票记录
	addVoteRecord(ip, n,typeId,uRemark,times)
	return 1

# django对post增加了csrf的保护，所以需要加上@csrf_exempt装饰器
#get请求则不需要
# 处理留言请求
@csrf_exempt
def chat(request):
	cInfo = request.POST.get('cInfo')
	n = request.POST.get('n')
	# 通过用户IP查找用户的名字
	ip = getUserIP(request)
	user = User.objects.get(uIP=ip,isDelete=0)
	# 查找候选者
	candidate = Candidate.cmanager.get(id=n, isDelete=0)
	# 保存用户留言信息
	cr = ChatRecord()

	cr.crInfo = cInfo  #留言内容
	cr.crName = user.uName  #用户名称
	cr.crNickName = user.uNickName  # 用户呢称
	cr.crTopic = candidate.cName #候选者名称
	cr.crType = candidate.cVoteType  #投票类型
	cr.crUser = user   #用户
	cr.crCandidate = candidate #候选者
	cr.save()
	return HttpResponse(1)

# 测试页面处理
def test(request):
	print("IP", getUserIP(request))
	print("********************")
	dataDicr = {
		'content': '<h1>hello world</h1>'
	}
	return render(request,'test.html',context=dataDicr)

# 打分主页面
def share(request,whoId,times):
	test(request)
	# 获取候选者
	c = Candidate.cmanager.get(id=whoId)

	# 获取今天的留言
	now = datetime.datetime.now()
	start = now - datetime.timedelta(hours=23, minutes=59, seconds=59)
	crs = c.chatrecord_set.filter(crTime__gt=start)

	# 获取投票记录
	us = UserVoteRecord.objects.filter(uWhoId=whoId, uTimes=times,isDelete=0,uDate=datetime.datetime.now().__format__('%Y-%m-%d'))

	# 统计投票人数
	if us:
		c.cVotes = us.count()
	else:
		c.cVotes = 0
	# 统计总分数
	countGrades = 0
	for u in us:
		# print(u.uRemark)
		if u.uRemark:
			countGrades += int(u.uRemark)
	avg = 0
	if c.cVotes:
		avg = int(countGrades / c.cVotes)

	# testing(request, avg)
	dictData = {'cs': c, 'messages': crs,'avg':avg,'grades':us,'times':times}
	return render(request,'shareGrade.html',context=dictData)

# 处理打分请求
@csrf_exempt
def grade(request):
	# print("打分IP",getUserIP(request))
	whoId = request.POST.get('whoId')
	grades = request.POST.get('grades')
	times = request.POST.get('times')
	# print('***********',times)
	# 用户是否打分成功
	cn = Candidate.cmanager.get(id=whoId, isDelete=0)
	typeId = cn.cVoteType_id

	if getUser(request, whoId,typeId,uRemark=str(grades),times=times):
		# 增加打分人数
		cn.cVotes += 1
		cn.save()
		return HttpResponse(1)
	return HttpResponse(0)

# 打分系统首页
def shareNav(request):
	# 获取候选人物，按名字首字母排序
	cs = Candidate.cmanager.filter(cVoteType_id=2).order_by("cPinyin")

	dictData = {'cs': cs, 'messages': {}, 'avg': 0, 'votes': 0, 'whoSelect': 0, 'whoId': 0}
	return render(request, 'shareNav.html', context=dictData)