from django.urls import path
from .views import (
    DashboardView, SwaggerDocsView, APIRootView,
    LiveGridSummaryAPIView, DistrictListAPIView,
    AnomalyListAPIView, ForecastAPIView, DirectiveListAPIView, CopilotChatAPIView
)

urlpatterns = [
    # Web Command Portal
    path('', DashboardView.as_view(), name='dashboard'),

    # Interactive Swagger / OpenAPI Documentation
    path('api/docs/', SwaggerDocsView.as_view(), name='swagger_docs'),

    # REST API Root
    path('api/v1/', APIRootView.as_view(), name='api_root'),

    # REST APIs
    path('api/v1/grid/live/', LiveGridSummaryAPIView.as_view(), name='api_live_grid'),
    path('api/v1/districts/', DistrictListAPIView.as_view(), name='api_districts'),
    path('api/v1/anomalies/', AnomalyListAPIView.as_view(), name='api_anomalies'),
    path('api/v1/forecast/', ForecastAPIView.as_view(), name='api_forecast'),
    path('api/v1/directives/', DirectiveListAPIView.as_view(), name='api_directives'),
    path('api/v1/copilot/chat/', CopilotChatAPIView.as_view(), name='api_copilot_chat'),
]
