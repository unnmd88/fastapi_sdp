FROM python:3.11-alpine
RUN pip install --upgrade pip
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . . 
ENTRYPOINT ['python', 'main.py']
