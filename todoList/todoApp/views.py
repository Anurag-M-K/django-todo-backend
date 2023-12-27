from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializers
from .models import User,Todo
import jwt,datetime
from rest_framework.response import Response
from .serializers import TodoSerializer
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import F
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator



class RegisterView(APIView):
    def post(self,request):
        serializer = UserSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
class LoginView(APIView):
    def post(self,request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found!')
        

        if not user.check_password(password):
            raise AuthenticationFailed('Wrong Password!')
        
        payload = {
            'id':user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),  # token expires after a
            'iat':datetime.datetime.utcnow()
        }

        token = jwt.encode(payload,'secret',algorithm='HS256')
        response = Response()
        response.set_cookie(key='jwt',value=token,httponly=True)
        response = Response({
            "success":True,
            "message":"Login successful",
            'token':token,
            "user":{
                "id":user.id,
                "username":user.username,
                "email":user.email
            }
        })
        
        response.set_cookie(key='jwt', value=token, httponly=True)

        return response
    

class UserView(APIView):
    def get(self,request):
        token = request.COOKIES.get('jwt')
        print("token ",token)
        if not token:
            raise AuthenticationFailed('unauthentiacated no token')
        
        try:
            payload = jwt.decode(token,'secret',algorithms='HS256')
            print("payload ",payload)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('unauthentiacated  hee')

        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializers(user)
        return Response(serializer.data)
    


class LogoutView(APIView):  
    def post(self,request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            "message":"success"
        }

        return response
    
class TodoView(APIView):
 
    def get(self,request,*args,**kwargs):
        token = request.headers.get('Authorization').split('Bearer')[1].strip()

        decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
        user_id  = decoded_token['id']
        todos = Todo.objects.filter(user=user_id)
        serializer = TodoSerializer(todos,many=True)
        return Response({"todos":serializer.data},status=status.HTTP_200_OK)

    @action(detail=True,methods=['POST'],url_path='todos')
    def post(self,request):
        token = request.headers.get('Authorization').split('Bearer')[1].strip()

        try :
            decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
            user_id  = decoded_token['id']
            request.data['user'] = user_id
        
      
            serializer = TodoSerializer(data= request.data)                 

            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except jwt.ExpiredSignatureError:
            return Response({"error":"Token has expired"},status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"error":"Invalid token"},status=status.HTTP_401_UNAUTHORIZED)
          
    @method_decorator(csrf_exempt)
    @action(detail=True,methods=['DELETE'])
    def delete_all_todos(self,request):
        print("dddddddddddddd ------------------ >")
        token = request.headers.get('Authorization').split('Bearer')[1].strip()
        decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
        user_id  = decoded_token['id']

        Todo.objects.filter(user=user_id).delete()

        return Response({'message':"All Todo deleted"})

    @action(detail=True, methods=['DELETE'], url_path='todos/(?P<id>\d+)')
    def delete(self, request, id, *args, **kwargs):
        token = request.headers.get('Authorization').split('Bearer')[1].strip()
        decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
        user_id  = decoded_token['id']
        item = Todo.objects.filter(id=id)
        item.delete()

        return Response({'message': "Todo deleted by ID"})


    @action(detail=True,methods=['PATCH'],url_path='todos/(?P<id>\d+)')
    def patch(self,request,id,*args,**kwargs):
        token = request.headers.get('Authorization').split('Bearer')[1].strip()
        decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
        user_id  = decoded_token['id']

        todo = Todo.objects.filter(id=id,user=user_id).first()
        if todo:
            todo.completed = not todo.completed
            todo.save()
             
            if todo.completed:
                return Response({'message':"Todo completed successfully🤩😘"})
            else:
                return Response({'message':"ooh not completed😒"})
        else:        
            return Response({"error":"Todo not found!"})
        
    @action(detail=True,methods=['PUT'],url_path='todos/(?P<id>\d+)')
    def put(self,request,id,*args):
        token = request.headers.get('Authorization').split('Bearer')[1].strip()
        decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
        user_id  = decoded_token['id']
        todo = Todo.objects.filter(id=id,user=user_id).first()
        if todo:
            try:
                request_data = json.loads(request.body)
            except JSONDecodeError:
                return Response({"error":"Invalid json data in the request body"},status=400)

            if todo.todo !=request_data.get('todo'):
                todo.todo = request_data.get('todo')
                todo.save()
                return Response({"message":"Todo updated successfully"})
            else:
                return Response({"message":"No change made to the todo"})
        else:
            return Response({"error":"Todo not found!"},status=404)