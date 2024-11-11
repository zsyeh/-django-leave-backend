# leave/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import Leave, StudentProfile


User = get_user_model()
from datetime import datetime
from rest_framework import serializers


class LeaveSerializer(serializers.ModelSerializer):
    # 原有字段
    student = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class_name = serializers.ReadOnlyField()
    
    # 新增字段
    student_number = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_class = serializers.SerializerMethodField()
    student_email = serializers.EmailField(source='student.email', read_only=True)
    
    class Meta:
        model = Leave
        fields = [
            'id', 'student', 'class_name', 'start_date', 'end_date', 'reason',
            'leave_time', 'status', 'approver',
            'student_number', 'student_name', 'student_class', 'student_email'
        ]
        read_only_fields = [
            'student_number', 'student_name', 'student_class', 'student_email'
        ]
    
    def get_student_number(self, obj):
        return obj.student.username  # 假设用户名为学号
    
    def get_student_name(self, obj):
        return obj.student.last_name  # 使用 last_name 作为姓名
    
    def get_student_class(self, obj):
        try:
            return obj.student.studentprofile.assigned_class.name
        except AttributeError:
            return None  # 若未设置班级，返回 None
    
    def validate(self, attrs):
        """
        验证结束日期不早于开始日期。
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if end_date < start_date:
            raise serializers.ValidationError({
                'end_date': '结束日期不能早于开始日期。'
            })
        
        return attrs
    
    def create(self, validated_data):
        # 保持原有的 create 方法
        validated_data['student'] = self.context['request'].user

        # 获取 student 的 class_name
        if hasattr(validated_data['student'], 'studentprofile') and validated_data['student'].studentprofile.assigned_class:
            assigned_class = validated_data['student'].studentprofile.assigned_class
            leave_instance = Leave.objects.create(**validated_data)  # 不包含 class_name
            leave_instance.class_name = assigned_class.name  # 手动设置 class_name
            
            # 计算请假天数
            start_date = leave_instance.start_date
            end_date = leave_instance.end_date
            # 假设 start_date 和 end_date 是日期字段，不包含时间
            delta = (end_date - start_date).days + 1  # 包含开始和结束日期

            # 设置 status 根据请假天数
            if delta >= 7:
                leave_instance.status = 4  # 时间多于7天，需要二重审批
            elif 3 <= delta <= 6:
                leave_instance.status = 2  # 假设 2 表示需要协商
            elif 1 <= delta <= 2:
                leave_instance.status = 1  # 假设 1 表示快速审核
            else:
                leave_instance.status = 0  # 默认状态

            leave_instance.save()  # 保存实例
            return leave_instance
        else:
            raise serializers.ValidationError("User profile or assigned class is not set.")


# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import StudentProfile, Class

class UserRegisterSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(write_only=True)  # 添加班级字段

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'class_name']  # 包含班级字段

    def create(self, validated_data):
        # 从 validated_data 中获取 class_name，然后将其移除以便创建用户
        class_name = validated_data.pop('class_name', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        
        # 查找并设置班级
        if class_name:
            try:
                assigned_class = Class.objects.get(name=class_name)
                # 创建学生的 profile 并关联班级
                StudentProfile.objects.create(user=user, assigned_class=assigned_class)
            except Class.DoesNotExist:
                raise serializers.ValidationError("Class with this name does not exist.")
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()
    student_number = serializers.CharField(source='username', read_only=True)
    email = serializers.EmailField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    user_group = serializers.SerializerMethodField()
    # 如果有其他字段需要包含，可以在这里添加

    class Meta:
        model = User
        fields = ['student_number', 'first_name', 'last_name', 'email', 'class_name','user_group']

    def get_class_name(self, obj):
        try:
            return obj.studentprofile.assigned_class.name
        except AttributeError:
            return None
    
    def get_user_group(self, obj):
        return obj.groups.first().name if obj.groups.first() else None
