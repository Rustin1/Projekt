from rest_framework import serializers
from .models import Column, Note, Team, Person, PersonNote


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = '__all__'


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'


class PersonNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonNote
        fields = '__all__'
