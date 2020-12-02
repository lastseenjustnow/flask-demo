FROM python:3.6.1-alpine
WORKDIR /project
ADD . /project

# Bloomberg API library
ENV APP /app
RUN mkdir $APP
WORKDIR $APP
COPY . .
ENV BLPAPI_ROOT /app/lib/blpapi_cpp_3.14.3.1
ENV LD_LIBRARY_PATH /app/lib/blpapi_cpp_3.14.3.1/Linux
ENV PATH "$PATH:/app/lib/blpapi_cpp_3.14.3.1"
RUN pip3 install --index-url=https://bloomberg.bintray.com/pip/simple -Iv blpapi==3.14.0

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python","server.py"]