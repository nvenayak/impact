FROM python:3.5.2
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD requirements.txt /code
WORKDIR /code
RUN pip install -r requirements.txt
WORKDIR ../
COPY /FermAT /code/FermAT
COPY /FermAT_web /code/FermAT_web
COPY /docs/_build/html /code/FermAT_web/FermAT_web/static/docs

#COPY /docs /code/docs
#WORKDIR /code/docs
#RUN pip install nbsphinx
#RUN pip install sphinx_bootstrap_theme
#RUN pip install ipython
#RUN pip install jupyter
#RUN apt-get install make
#RUN /bin/bash -c ls
#RUN /bin/bash -c 'make html'

COPY setup.py /code
WORKDIR /code
RUN mkdir /code/db
RUN python setup.py develop
EXPOSE 8000
WORKDIR /code/FermAT_web
RUN python3 manage.py migrate
CMD python3 manage.py runserver 0.0.0.0:8000
