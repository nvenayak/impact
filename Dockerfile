FROM python:3.5.2
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD requirements.txt /code
WORKDIR /code
RUN pip install -r requirements.txt
WORKDIR ../
COPY /FermAT /code/FermAT
COPY /FermAT_web /code/FermAT_web
COPY setup.py /code
WORKDIR /code
RUN python setup.py install
EXPOSE 8000
WORKDIR /code/FermAT_web
CMD python manage.py runserver 0.0.0.0:8000
