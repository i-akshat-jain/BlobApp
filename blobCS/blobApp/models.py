from django.db.models import F
from django.db import models
from django.utils import timezone

class Blob(models.Model):
    id = models.AutoField(primary_key=True)
    blob = models.CharField(max_length=100, unique=True,
                            null=False)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now().time())
    def __str__(self):
        return f"{self.blob} - {self.date} - {self.time}"


class Mention(models.Model):
    id = models.AutoField(primary_key=True)
    blob_id = models.ForeignKey(Blob, db_column='blob_id', on_delete=models.CASCADE, default=None)
    mention = models.CharField(max_length=500, null=False, default=None)
    position = models.IntegerField(default = 0, null=True)
    wikipedia_url = models.URLField()

    def __str__(self):
        return f"{self.mention} - {self.wikipedia_url} - {self.position} - {self.blob_id}"


