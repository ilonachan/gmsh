FROM python:3.8.6

VOLUME /gmsh/config

WORKDIR /gmsh

# install required libraries
COPY ./requirements.txt /gmsh/requirements.txt
RUN pip install -r /gmsh/requirements.txt

# copy the code and default configuration
COPY ./gmsh /gmsh/gmsh
COPY ./logging.yaml /gmsh/logging.yaml

# This will become relevant if I add a web interface to my bot
# ENV SERVER_PORT 8080
# EXPOSE $SERVER_PORT

CMD [ "python", "-m", "gmsh" ]