  #Grab the latest alpine image
FROM python:3.8-slim-buster

# Add dependency file
ADD /requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip3 install --no-cache-dir -q -r /tmp/requirements.txt

# Add our code
ADD . /opt/app/
WORKDIR /opt/app


# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku			
CMD ["gunicorn", "app:server"]