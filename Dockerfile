FROM python:3.10-slim
WORKDIR /app
COPY *.py /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
