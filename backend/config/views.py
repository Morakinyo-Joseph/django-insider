from rest_framework import status
from rest_framework.views import APIView
import logging
from django.contrib.auth.models import User 
from rest_framework.response import Response


logger = logging.getLogger(__name__)


class _500(APIView):
    def post(self, request):
        logger.info("I am star struck.")

        user = User
        newuser = user.name

        return Response({"message": "Maybe a success response"})


class _200(APIView):
    def post(self, request):

        return Response({"reply": "The night o yea"})