FROM python:3.10-alpine
EXPOSE 8000
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
COPY kanban /app/kanban
COPY Zespolowy /app/Zespolowy
COPY db /app/db
COPY manage.py /app/
