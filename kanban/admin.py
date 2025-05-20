from django.contrib import admin

from .models import Column, Note, Team, Person, PersonNote


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'max', 'per_person']

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['name', 'column', 'position', 'person']

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname']


@admin.register(PersonNote)
class PersonNoteAdmin(admin.ModelAdmin):
    list_display = ['person', 'note']
