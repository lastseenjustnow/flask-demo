FROM python:3.6.5
FROM ubuntu:18.04
RUN apt-get update --fix-missing
RUN apt-get install -y python3-pip unixodbc-dev curl
ENV APP /app
RUN mkdir $APP
WORKDIR $APP
EXPOSE 5000
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
ENV BLPAPI_ROOT /app/lib/blpapi_cpp_3.14.3.1
ENV LD_LIBRARY_PATH /app/lib/blpapi_cpp_3.14.3.1/Linux
ENV PATH "$PATH:/app/lib/blpapi_cpp_3.14.3.1"
RUN pip3 install --index-url=https://bloomberg.bintray.com/pip/simple -Iv blpapi==3.14.0
ENTRYPOINT [ "python3" ]
CMD [ "server.py" ]
