FROM python:3.6-alpine3.6

WORKDIR /srv

# Create an app user and run as that
#RUN adduser -S app
##RUN chown -R app /srv
#RUN chown -R www-data: /srv/instance
#USER app

# Install Python dependencies
#ADD requirements.txt .

# Add the project
ADD setup.py ./
RUN python setup.py develop  --user
ADD instance ./instance
ADD app ./app

ENV PATH $PATH:/home/app/.local/bin

ENV FLASK_APP app
CMD flask run --host 0.0.0.0 --port 8080
