FROM python:3.9

EXPOSE 5050
WORKDIR /src
COPY requirements.txt /src
RUN pip install -r requirements.txt
COPY . /src
CMD ["python3", "run_bot.py"]
