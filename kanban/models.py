from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100)


class Column(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    position = models.IntegerField()
    max = models.IntegerField(null=True)
    per_person = models.BooleanField(default=False)


class Note(models.Model):
    column = models.ForeignKey(Column, on_delete=models.CASCADE)
    position = models.IntegerField()
    name = models.CharField(max_length=100, null=True)
    person = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)


class Person(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)


class PersonNote(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
