FROM python:3.8.6

VOLUME /gmsh/config

# default database volume in case nothing usable is provided
VOLUME /db
# and default env variables pointing there
ENV DB_LOCATION sqlite:////db/gmsh.sqlite
ENV DB_PLAYGROUND_LOCATION sqlite:////db/playground.sqlite

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