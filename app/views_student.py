from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.contrib.auth.hashers import make_password,check_password
from app.models import User_info,student_file,project,Student_info,Teacher_info,message,broadcast
from app.views import check_login
import os
from django.db.models import Q
from itertools import chain

@check_login
def index_students(request):
    #文件

    student_file_obj = student_file.objects.filter(email=User_info.objects.get(email=request.session.get('email'))).values()
    student_info_obj = Student_info.objects.filter(student=User_info.objects.get(email=request.session.get('email')))
    student_file_obj_list = list(student_file_obj)
    for i in (student_file_obj_list):
        i['project_name'] = project.objects.filter(id=int(student_info_obj[0].project_id))[0].project_name
        i['project_teacher'] =Teacher_info.objects.filter(Q(project_1=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                          | Q(project_2=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                          | Q(project_3=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                    )[0].teacher_name
    #个人资料
    profile = {}
    profile['username']  = User_info.objects.get(email=request.session.get('email')).username
    profile['email'] = request.session.get('email')
    profile['name']  = Student_info.objects.filter(student=User_info.objects.get(email=request.session.get('email')))[0].student_name
    profile['class'] = Student_info.objects.filter(student=User_info.objects.get(email=request.session.get('email')))[0].student_class
    profile['school'] = Student_info.objects.filter(student=User_info.objects.get(email=request.session.get('email')))[0].student_school
    profile['major'] = Student_info.objects.filter(student=User_info.objects.get(email=request.session.get('email')))[0].student_major
    profile['sex'] = Student_info.objects.filter(student=User_info.objects.get(email=request.session.get('email')))[0].student_sex
    profile['time'] = User_info.objects.get(email=request.session.get('email')).create_time
    if project.objects.filter(id = Student_info.objects.get(student=User_info.objects.get(email=request.session.get('email'))).project_id  ):
        profile['project_name'] = project.objects.filter(
            id=Student_info.objects.get(student=User_info.objects.get(email=request.session.get('email'))).project_id)[
            0].project_name
        profile['project_teacher'] =Teacher_info.objects.filter(Q(project_1=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                          |Q(project_2=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                          |Q(project_3=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                    )[0].teacher_name
    else:
        profile['project_name'] = 'null'
        profile['project_teacher'] = 'null'
    student_file_time_obj = student_file.objects.filter(email=User_info.objects.get(email=request.session.get('email'))).order_by('-student_upload_time')
    if student_file_time_obj:
        file_lasted_time = student_file_time_obj[0].student_upload_time
    else:
        file_lasted_time = '无'
    # 消息面板显示
    student_project_obj = Student_info.objects.get(student=User_info.objects.get(email=request.session.get('email'))).project
    messagenum = message.objects.filter(project=student_project_obj).count()
    no_read_messagenum = message.objects.filter(project=student_project_obj,message_flag=1,message_reservier=User_info.objects.get(email=request.session.get('email'))).count()
    alertnum = broadcast.objects.filter(Q(broadcast_upload_to=3) | Q(broadcast_upload_to=1)).count()

    #简短消息brief
    brief_broadcast_obj = broadcast.objects.filter(Q(broadcast_upload_to=3) | Q(broadcast_upload_to=1))
    brief_message_obj = message.objects.filter(Q(message_reservier=User_info.objects.get(email=request.session.get('email')))
                                               & Q(message_flag=1)
                                               & Q(project=student_project_obj)).values()
    brief_message_list = list(brief_message_obj)
    for i in brief_message_list:
        i['teacher'] = Teacher_info.objects.filter(Q(project_1=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                          |Q(project_2=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                          |Q(project_3=project.objects.filter(id=int(student_info_obj[0].project_id))[0].id)
                                                    )[0].teacher_name

    #所有项目浏览，
    all_project_obj = project.objects.all()
    # unselected_project_obj = project.objects.exclude(id = )
    if request.method =='GET':
        return render(request,'index_students.html',{'username' : User_info.objects.filter(email=request.session.get('email'))[0].username,
                                                     'student_files':student_file_obj_list,
                                                     'email':User_info.objects.get(email=request.session.get('email')),
                                                     'profile' :profile,
                                                     'messagenum':messagenum,
                                                     'no_read_messagenum':no_read_messagenum,
                                                     'alertnum':alertnum,
                                                     'brief_broadcasts':brief_broadcast_obj,
                                                     'brief_messages':brief_message_list,
                                                     'file_lasted_time':file_lasted_time,
                                                     })

#上传文件
def upload_file(request):
    user_email = request.session.get('email')
    if Student_info.objects.get(student=User_info.objects.get(email=user_email)).project:
        if request.method == 'POST':
            file_obj = request.FILES.get('file')
            if file_obj is None:
                return redirect('/index_students/#table')
            else:
                isExists = os.path.exists('./app/temp_file/%s' % user_email)
                if not isExists:
                    os.makedirs('./app/temp_file/%s' % user_email)
                file_path = os.path.join('app', 'temp_file', user_email, file_obj.name)
                with open(file_path, 'wb+') as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)
                fsize = os.path.getsize(file_path)
                fobj = User_info.objects.get(email=user_email)
                user_file_obj = student_file(email=fobj, student_file_name=file_obj.name, student_file_size=fsize,student_upload_add=file_path)
                user_file_obj.save()
                return redirect('/index_students/#table')
        else:
            return redirect('/index_students/#table')
    else:
        return HttpResponse("<script>alert('您没有项目，无法提交！');window.history.back();</script>")

#下载文件
def download_file(request,email,student_file_name):
    path = os.path.join('app', 'temp_file', email, student_file_name)
    file = open(path, 'rb')
    response = HttpResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename=' + student_file_name
    return response

#删除文件
def delete_file(request,email,student_file_name):

    userfile = student_file.objects.get(email=User_info.objects.get(email = email), student_file_name=student_file_name)
    userfile.delete()
    path = os.path.join('app', 'temp_file', email, student_file_name)
    os.remove(path)
    return redirect('/index_students/#table')

#更改个人资料
def alter_personal_info(request,email):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        school = request.POST.get('school')
        major = request.POST.get('major')
        class1 = request.POST.get('class')
        sex = request.POST.get('sex')
        num_sex = lambda x : 1 if sex=='male' else 2
        int_sex = num_sex(sex)
        User_info.objects.filter(email=email).update(username=username)

        data = {'student_class':class1,
                'student_major':major,
                'student_name':name,
                'student_school':school,
                'student_sex':int_sex}
        _t = Student_info.objects.get(student=User_info.objects.get(email=email))
        _t.__dict__.update(**data)
        _t.save()
        return redirect('/index_students/#myprofile')



#更改个人密码
def alter_personal_psd(request,email):
    if request.method == 'POST':
        newpassword = request.POST.get('newpassword')
        User_info.objects.filter(email=email).update(password = make_password(newpassword))
        return redirect('/index_students/#profile')