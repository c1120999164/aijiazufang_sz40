
from django.urls import path
from . import views

urlpatterns = [
    # path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
    path('api/v1.0/sms', views.SMSCodeView.as_view()),
    
    path('api/v1.0/imagecode', views.ImageCodeView.as_view()),
]