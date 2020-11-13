from django.db import models

class Pothole(models.Model):
    uuid = models.UUIDField()
    depth = models.FloatField()
    width = models.FloatField()
    length = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    road = models.ForeignKey("Road", on_delete=models.DO_NOTHING)
    tenant = models.ForeignKey('Tenant', on_delete=models.DO_NOTHING)

class Tenant(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

class Road(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=150)
    tenant = models.ForeignKey('Tenant', on_delete=models.DO_NOTHING)
