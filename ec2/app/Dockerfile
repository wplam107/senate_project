  #Grab the python slim image
FROM python:3.8-slim-buster

# Add dependency file
ADD ./requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip3 install --no-cache-dir -q -r /tmp/requirements.txt

# Add code
ADD . /opt/app/
WORKDIR /opt/app


# Run the app with gunicorn			
CMD ["gunicorn", "app:server"]
