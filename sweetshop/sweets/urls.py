from rest_framework.routers import DefaultRouter

from .views import SweetViewSet

"""URL routing for sweets app."""
router = DefaultRouter()
router.register("sweets", SweetViewSet, basename="sweets")

urlpatterns = router.urls
