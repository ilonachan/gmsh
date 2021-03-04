FROM python:3.8.6

# ENV DB_LOCATION postgresql:///gmsh:Secret Password@db:1234/gmsh
# ENV DB_PLAYGROUND_LOCATION postgresql:///gmsh:Secret Password@db:1234/playground

VOLUME /gmsh/config

WORKDIR /gmsh

# install required libraries
COPY ./requirements.txt /gmsh/requirements.txt
RUN pip install -r /gmsh/requirements.txt

# copy the code and default configuration
COPY ./gmsh /gmsh/gmsh
COPY ./logging.yaml /gmsh/logging.yaml

# ENV SERVER_PORT 8080
# EXPOSE $SERVER_PORT

CMD [ "python", "-m", "gmsh" ]