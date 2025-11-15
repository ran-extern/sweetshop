from rest_framework.routers import DefaultRouter

from .views import SweetViewSet


router = DefaultRouter()
router.register(r"sweets", SweetViewSet, basename="sweets")

urlpatterns = router.urls
