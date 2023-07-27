from rest_framework import serializers
from getMentions.models import Mention
from getMentions.models import Blob

"""
to serialize the data into json or xml format from queryset
"""


class mentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mention
        fields = '__all__'


class blobSerializer(serializers.ModelSerializer):
    class Meta:

        model = Blob
        fields = '__all__'
