from django.db import models
from django.utils import timezone

class Blob(models.Model):
    id = models.AutoField(primary_key=True)
    blob = models.CharField(max_length=100, unique=True,
                            null=False, default=None)
    date = models.DateField(default = timezone.now)

    def __str__(self):
        return f"{self.blob} - {self.date}"


class Mention(models.Model):
    id = models.AutoField(primary_key=True)
    blob_id = models.ForeignKey(Blob, on_delete=models.CASCADE, default=None)
    rank = models.IntegerField( default=None)
    mention = models.CharField(max_length=255, default=None)
    url = models.URLField( default=None)
    wikipedia_url = models.URLField()

    def __str__(self):
        return f"{self.mention} - {self.url}"
