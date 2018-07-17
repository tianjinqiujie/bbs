from django.shortcuts import render,redirect,HttpResponse
from django.db.models import Count
# Create your views here.
from django.contrib import auth
from utils.code import check_code

from blog.models import Article,UserInfo,Category,Tag,ArticleUpDown,Comment,Article2Tag
from blog import forms
import json
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from bbs import settings
import os


def code(request):
    img,random_code = check_code()
    request.session['random_code'] = random_code
    from io import BytesIO
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

def login(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        pwd = request.POST.get('pwd')
        code = request.POST.get('code')
        if code.upper() != request.session['random_code'].upper():
            return render(request, 'login.html', {'msg': '验证码错误'})
        user = auth.authenticate(username=user,password=pwd)
        if user:
            auth.login(request,user)
            return redirect('/index/')
    return render(request,'login.html')

def register(request):
    if request.method == "POST":
        print(request.POST)
        print("=" * 120)
        ret = {"status": 0, "msg": ""}
        form_obj = forms.RegForm(request.POST)
        print(request.POST)
        # 帮我做校验
        if form_obj.is_valid():

            # 校验通过，去数据库创建一个新的用户
            form_obj.cleaned_data.pop("re_password")
            avatar_img = request.FILES.get("avatar")
            UserInfo.objects.create_user(**form_obj.cleaned_data, avatar=avatar_img)
            ret["msg"] = "/index/"
            return JsonResponse(ret)
        else:
            print(form_obj.errors)
            ret["status"] = 1
            ret["msg"] = form_obj.errors
            print(ret)
            print("=" * 120)
            return JsonResponse(ret)
    # 生成一个form对象
    form_obj = forms.RegForm()
    print(form_obj.fields)
    return render(request, "register.html", {"form_obj": form_obj})

def index(request):
    article_list = Article.objects.all()
    return render(request,'index.html',{'article_list':article_list})

def logout(request):
    auth.logout(request)
    return redirect('/index/')

def homesite(request,username,**kwargs):
    """
    查询
    :param request:
    :param username:
    :return:
    """

    # 查询当前站点的用户对象
    user = UserInfo.objects.filter(username=username).first()
    if not user:
        return render(request,'not_found.html')
    # 查询当前站点对象
    blog = user.blog
    # 查询当前用户发布的所有文章
    if not kwargs:
        article_list = Article.objects.filter(user__username=username)
    else:
        condition=kwargs.get('condition')
        params = kwargs.get('params')
        if condition == 'category':
            article_list = Article.objects.filter(user__username=username).filter(category__title=params)
        elif condition == 'tag':
            article_list = Article.objects.filter(user__username=username).filter(tags__title=params)
            print(article_list)
        else:
            year,month = params.split('/')
            article_list = Article.objects.filter(user__username=username).filter(create_time__year=year,create_time__month=month)

    # if not article_list:
    #     return render(request,'not_found.html')
    # # 查询当前站点每一个分类的名称以及对应的文章数
    # category_list = Category.objects.filter(blog=blog).annotate(c=Count('article')).values('title','c')
    # # 查询当前站点每一个标签的名称以及对应的文章数
    # tag_list = Tag.objects.filter(blog=blog).annotate(c=Count('article')).values('title','c')
    return render(request,'homesite.html',locals())

def article_detail(request,username,article_id):
    user = UserInfo.objects.filter(username=username).first()
    # print(user)
    blog = user.blog
    # print(blog)

    article_obj = Article.objects.filter(pk=article_id).first()

    comment_list = Comment.objects.filter(article_id=article_id)

    return render(request,'article_detail.html',locals())


def digg(request):
    print(request.POST)
    is_up = json.loads(request.POST.get('is_up'))
    article_id = request.POST.get('article_id')
    user_id = request.user.pk
    response = {'state':True,'msg':None}
    obj=ArticleUpDown.objects.filter(user_id=user_id,article_id=article_id).first()
    if obj:
        response['state'] = False
        response['handled'] = obj.is_up
    else:
        with transaction.atomic():
            new_obj = ArticleUpDown.objects.create(user_id=user_id,article_id=article_id,is_up=is_up)
            print(new_obj,is_up,article_id)
            if is_up:
                Article.objects.filter(pk=article_id).update(up_count=F("up_count") + 1)
            else:
                Article.objects.filter(pk=article_id).update(down_count=F('down_count') + 1)
    return JsonResponse(response)

def comment(request):
    # 获取数据
    user_id=request.user.pk
    article_id=request.POST.get("article_id")
    content=request.POST.get("content")
    pid=request.POST.get("pid")
    # 生成评论对象
    with transaction.atomic():
        comment=Comment.objects.create(user_id=user_id,article_id=article_id,content=content,parent_comment_id=pid)
        Article.objects.filter(pk=article_id).update(comment_count=F("comment_count")+1)

    response={"state":True}
    response["timer"]=comment.create_time.strftime("%Y-%m-%d %X")
    response["content"]=comment.content
    response["user"]=request.user.username

    return JsonResponse(response)

def backend(request):
    user = request.user
    article_list=Article.objects.filter(user=user)
    return render(request,'backend/backend.html',locals())

def add_article(request):
    if request.method=="POST":

        title=request.POST.get("title")
        content=request.POST.get("content")
        user=request.user
        cate_pk=request.POST.get("cate")
        tags_pk_list=request.POST.getlist("tags")

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        # 文章过滤：
        for tag in soup.find_all():
            # print(tag.name)
            if tag.name in ["script",]:
                tag.decompose()

        # 切片文章文本
        desc=soup.text[0:150]

        article_obj=Article.objects.create(title=title,content=str(soup),user=user,category_id=cate_pk,desc=desc)

        for tag_pk in tags_pk_list:
            Article2Tag.objects.create(article_id=article_obj.pk,tag_id=tag_pk)

        return redirect("/backend/")


    else:

        blog=request.user.blog
        cate_list=Category.objects.filter(blog=blog)
        tags=Tag.objects.filter(blog=blog)
        return render(request,"backend/add_article.html",locals())


def upload(request):
    print(request.FILES)
    obj=request.FILES.get("upload_img")
    name=obj.name

    path=os.path.join(settings.BASE_DIR,"static","upload",name)
    with open(path,"wb") as f:
        for line in obj:
            f.write(line)

    import json

    res={
        "error":0,
        "url":"/static/upload/"+name
    }

    return HttpResponse(json.dumps(res))

def delete_article(request):
    delete_id = request.POST.get('article_id')
    del_obj = Article.objects.filter(nid=delete_id)
    if del_obj.first().user_id == request.user.pk:
        Article.objects.filter(nid=delete_id).delete()
    return HttpResponse('删除成功')

def edit_article(request,edit_id):
    if request.method=="POST":
        title=request.POST.get("title")
        content=request.POST.get("content")
        user=request.user
        cate_pk=request.POST.get("cate")
        tags_pk_list=request.POST.getlist("tags")

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        # 文章过滤：
        for tag in soup.find_all():
            # print(tag.name)
            if tag.name in ["script",]:
                tag.decompose()

        # 切片文章文本
        desc=soup.text[0:150]
        Article2Tag.objects.filter(article__nid=edit_id).delete()
        article_obj=Article.objects.filter(nid=edit_id).first()
        for tag_pk in tags_pk_list:
            Article2Tag.objects.create(article_id=article_obj.pk,tag_id=tag_pk)
        Article.objects.filter(nid=edit_id).update(title=title,content=str(soup),user=user,category_id=cate_pk,desc=desc)
        return redirect("/backend/")
    article_obj = Article.objects.filter(nid=edit_id).first()
    old_tag = Tag.objects.filter(article2tag__article_id=edit_id).all()
    print(old_tag)
    blog = request.user.blog
    cate_list = Category.objects.filter(blog=blog)
    tags = Tag.objects.filter(blog=blog)
    return render(request,'backend/edit_article.html',locals())