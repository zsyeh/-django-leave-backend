# views.py

from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Leave
from .serializers import LeaveSerializer, UserRegisterSerializer
from .serializers import UserRegisterSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework import generics, status

# 学生注册
@permission_classes([AllowAny])
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'detail': 'User registered successfully!',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 用户登录
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# 学生提交请假申请


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_leave(request):
    data = request.data
    student = request.user
    data['student'] = student.id
    
    # 解析并验证日期时间数据
    datetime_str = data.get('datetime')
    if datetime_str:
        try:
            # 只解析到年月日小时
            parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H')
            data['datetime'] = parsed_datetime.isoformat()
        except ValueError:
            return Response({'error': 'Datetime has wrong format. Use YYYY-MM-DDTHH format.'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = LeaveSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 学生查看请假状态
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_leave_status(request):
    student = request.user
    leaves = Leave.objects.filter(student=student)
    serializer = LeaveSerializer(leaves, many=True)
    return Response(serializer.data)

# 管理员批准请假
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def approve_leave(request, leave_id):
    try:
        leave = Leave.objects.get(id=leave_id)
    except Leave.DoesNotExist:
        return Response({'error': 'Leave not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.user.is_superuser:  # 确保是管理员
        leave.is_approved = True
        leave.save()
        return Response({'status': 'Leave approved'})
    return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)


class AdminLeaveListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        leaves = Leave.objects.all()
        serializer = LeaveSerializer(leaves, many=True)
        return Response(serializer.data)

    @csrf_exempt
    def patch(self, request, leave_id):
        try:
            leave = Leave.objects.get(id=leave_id)
        except Leave.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)
        
        leave.is_approved = True
        leave.save()
        return Response({'detail': 'Leave request approved successfully'}, status=status.HTTP_200_OK)


class CancelLeaveView(generics.DestroyAPIView):
    queryset = Leave.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        leave_id = kwargs.get('leave_id')
        try:
            leave_request = Leave.objects.get(id=leave_id, student=request.user)
            if leave_request.is_approved:
                leave_request.delete()
                return Response({'status': 'Leave cancelled successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Only approved leaves can be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        except Leave.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)