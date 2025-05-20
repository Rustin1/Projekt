from django.shortcuts import redirect, render
from django.views import View
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Column, Note, Team, Person, PersonNote
from django.views.generic.edit import CreateView
from django.db import transaction
from .serializers import ColumnSerializer, NoteSerializer, PersonSerializer, TeamSerializer, PersonNoteSerializer


class ColumnAPIView(APIView):
    def post(self, request):
        position = request.data.get('position')
        highest = Column.objects.order_by('-position').first()
        if position is None:
            if highest:
                position = highest.position + 1
            else:
                position = 1
        if highest is None:
            position = 1
        elif position > highest.position:
            position = highest.position + 1
        else:
            with transaction.atomic():
                columns_to_update = Column.objects.filter(position__gte=position)
                columns_to_update = columns_to_update.order_by('-position')
                for column in columns_to_update:
                    column.position += 1
                    column.save()

        name = request.data.get('name', None)

        if name is None:
            name = "Kolumna "+str(Column.objects.all().count()+1)

        column_data = {
            'name': name,
            'position': position,
            'max': request.data.get('max', None)
        }

        print(column_data)

        serializer = ColumnSerializer(data=column_data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        columns = Column.objects.all().order_by('position')
        serializer = ColumnSerializer(columns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _move_notes_to_column(self, notes, column, person):
        existing_notes = Note.objects.filter(column=column, person=person).order_by('-position')
        position = existing_notes.first().position if len(existing_notes) > 0 else 0
        for note in notes:
            position = position + 1
            note.column = column
            note.position = position
            note.save()

    def delete(self, request):
        try:
            if Column.objects.all().count() <= 2:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            column_id = request.data['id']
            column = Column.objects.get(id=column_id)
            position = column.position

            # move notes to other column
            column_target_position = position - 1 if position > 2 else position + 1
            column_target = Column.objects.get(position=column_target_position)
            notes_to_update = Note.objects.filter(column=column_id, person=None)
            self._move_notes_to_column(notes_to_update, column_target, None)
            people = Team.objects.all().order_by("name")
            for person in people:
                notes_to_update = Note.objects.filter(column=column_id, person=person)
                self._move_notes_to_column(notes_to_update, column_target, person)

            # move other columns indexes
            columns_to_update = Column.objects.filter(position__gte=position)
            for col in columns_to_update:
                col.position -= 1
                col.save()

            column.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Column.DoesNotExist:
            return Response({"error": "Column does not exist"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            column_id = request.data['id']
            new_position = request.data.get('position')
            column = Column.objects.get(id=column_id)
            if new_position is not None and new_position != column.position:
                columns_to_update = Column.objects.filter(position__gte=min(new_position, column.position),
                                                          position__lte=max(new_position, column.position)).exclude(
                    id=column_id)
                if new_position > column.position:
                    columns_to_update.update(position=models.F('position') - 1)
                else:
                    columns_to_update.update(position=models.F('position') + 1)

                column.position = new_position

            name = request.data.get('name', None)
            max_notes = request.data.get('max', "nic")
            per_person = request.data.get('per_person', None)

            if name is not None:
                column.name = name
            if max_notes is not "nic":
                if max_notes is None:
                    column.max = None
                else:
                    column.max = request.data['max']
            if per_person is not None:
                column.per_person = per_person
            column.save()
            return Response(ColumnSerializer(column).data, status=status.HTTP_200_OK)
        except Column.DoesNotExist:
            return Response({"error": "Column does not exist"}, status=status.HTTP_404_NOT_FOUND)


class ColumnHTMLView(View):
    def get(self, request):
        return render(request, 'kanban.html')


class ColumnRedirectView(View):
    def get(self, request):
        return redirect('/columns')


class NoteAPIView(APIView):
    def get(self, request):
        notes = Note.objects.all().order_by("position")

        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        id = request.data['id']
        if not request.data['id']:
            return Response({"error": "Column does not exist"}, status=status.HTTP_404_NOT_FOUND)
        column = Column.objects.get(id=id)
        if column is None:
            return Response({"error": "Column does not exist"}, status=status.HTTP_404_NOT_FOUND)
        name = request.data.get('name', 'notatka ' + str((Note.objects.order_by("-id").first().id+1) if Note.objects.exists() else 1))
        position = request.data.get("position", None)
        if position is None:
            if Note.objects.filter(column=id, person=None).exists():
                position = Note.objects.filter(column=id, person=None).order_by('-position').first().position + 1
            else:
                position = 1
        else:
            with transaction.atomic():
                notes_to_update = Note.objects.filter(column=column,position__gte=position)
                notes_to_update = notes_to_update.order_by('-position')
                for note in notes_to_update:
                    note.position += 1
                    note.save()
        note = Note.objects.create(name=name, column=column, position=position)
        note.save()
        self._heal_column(column, None)
        serializer = NoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _prepare_place_in_column(self, column, person, position):
        notes_to_increment = Note.objects.filter(column=column, person=person, position__gte=position)
        notes_to_increment.update(position=models.F('position') + 1)

    def _recalculate_old_column_positions(self, column, person, position):
        notes_to_decrement = Note.objects.filter(column=column, person=person, position__gte=position)
        notes_to_decrement.update(position=models.F('position') - 1)

    def _heal_column(self, column, person):
        pos = 1
        notes_to_check = Note.objects.filter(column=column.id, person=person).order_by("position").all()
        for note in notes_to_check:
            if note.position != pos:
                print("WARNING!!! Healing Column was required! Affected note:",
                      'Col/person', column.id, '/', person.id if person else None,
                      'Note', note.id, ':', note.position, '=>', pos)
                note.position = pos
                note.save()
            pos = pos + 1

    def put(self, request):
        id = request.data.get('id', None)
        name = request.data.get('name', None)
        column_id = request.data.get('column', None)
        person_id = request.data.get('person', None)
        new_pos = request.data.get('position', None)
        print(id)
        print(name)

        if id is None:
            return Response({"error": "Note does not exist"}, status=status.HTTP_404_NOT_FOUND)

        note = Note.objects.get(id=request.data['id'])

        if note is None:
            return Response({"error": "Note does not exist"}, status=status.HTTP_404_NOT_FOUND)

        if name is not None:
            note.name = name

        if column_id is not None:
            column = Column.objects.get(id=column_id)
            person = Team.objects.get(id=person_id) if person_id else None
            if column.id != note.column.id or person != note.person:
                old_column = note.column
                old_person = note.person
                self._prepare_place_in_column(column, person, new_pos)
                self._recalculate_old_column_positions(note.column, note.person, note.position)
                note.position = new_pos
                note.column = column
                note.person = person
                note.save()
                self._heal_column(old_column, old_person)
                self._heal_column(note.column, note.person)
            elif new_pos is not None and new_pos != note.position:
                if new_pos > note.position:
                    notes_to_decrement = Note.objects.filter(column=column, person=person,
                                                             position__lte=new_pos, position__gte=note.position)
                    notes_to_decrement.update(position=models.F('position') - 1)
                elif new_pos < note.position:
                    notes_to_increment = Note.objects.filter(column=column, person=person,
                                                             position__lte=note.position, position__gte=new_pos)
                    notes_to_increment.update(position=models.F('position') + 1)
                note.position = new_pos
                note.save()
                self._heal_column(note.column, note.person)
        note.save()
        serializer = NoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        if not request.data['id']:
            return Response({"error": "Note does not exist"}, status=status.HTTP_404_NOT_FOUND)
        note = Note.objects.get(id=request.data['id'])
        if note is None:
            return Response({"error": "Note does not exist"}, status=status.HTTP_404_NOT_FOUND)
        note.delete()
        return Response(status=status.HTTP_200_OK)


class TeamAPIView(APIView):
    def get(self, request):
        people = Team.objects.all().order_by("name")

        serializer = TeamSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PersonAPIView(APIView):
    def get(self, request):
        people = Person.objects.all().order_by("name")

        serializer = PersonSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PersonNoteAPIView(APIView):
    def get(self, request):
        person_notes = PersonNote.objects.all()
        serializer = PersonNoteSerializer(person_notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        person = request.data.get('person', None)
        note = request.data.get('note', None)
        if person is None or note is None:
            return Response({"error": "missing ID"}, status=status.HTTP_404_NOT_FOUND)
        person = Person.objects.get(id=person)
        note = Person.objects.get(id=note)
        if person is None or note is None:
            return Response({"error": "missing Object"}, status=status.HTTP_404_NOT_FOUND)
        if PersonNote.objects.get(person=person, note=note):
            return Response({"error": "This connection already exists"}, status=status.HTTP_400_BAD_REQUEST)
        PersonNote.objects.create(person=person, note=note)
        return Response(status=status.HTTP_201_CREATED)

    def put(self, request):
        people = request.data.get('people', None)
        note = request.data.get('note', None)
        print(people)
        if people is None or note is None:
            return Response({"error": "missing ID"}, status=status.HTTP_404_NOT_FOUND)
        people = Person.objects.filter(id__in=people)
        note = Note.objects.get(id=note)
        if note is None:
            return Response({"error": "missing note"}, status=status.HTTP_404_NOT_FOUND)
        connections = PersonNote.objects.filter(note=note)
        connections.delete()
        for person in people:
            connection = PersonNote.objects.create(person=person, note=note)
            connection.save()

        person_notes = PersonNote.objects.all()
        serializer = PersonNoteSerializer(person_notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        person = request.data.get('person', None)
        note = request.data.get('note', None)
        if person is None or note is None:
            return Response({"error": "missing ID"}, status=status.HTTP_404_NOT_FOUND)
        person = Person.objects.get(id=person)
        note = Person.objects.get(id=note)
        if person is None or note is None:
            return Response({"error": "missing Object"}, status=status.HTTP_404_NOT_FOUND)
        PersonNote.objects.get(person=person, note=note).delete()

        return Response(status=status.HTTP_402_PAYMENT_REQUIRED)
