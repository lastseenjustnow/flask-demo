FROM python:3.6.5
FROM ubuntu:18.04
RUN apt-get update --fix-missing
RUN apt-get install -y \
    python3-pip \
    unixodbc-dev \
    curl \
    ca-certificates \
    iputils-ping \
    net-tools
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
RUN pip3 install --index-url=https://bcms.bloomberg.com/pip/simple/ -Iv blpapi==3.14.0

# Microsoft ODBC Driver 17
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get -y install msodbcsql17
RUN ACCEPT_EULA=Y apt-get -y install mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"

ENTRYPOINT [ "python3" ]
CMD [ "server.py" ]
