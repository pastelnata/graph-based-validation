FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
	&& python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]