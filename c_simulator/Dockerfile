FROM gcc:latest
RUN apt-get update && apt-get install -y libcurl4-openssl-dev 
WORKDIR /app 
COPY . . 
RUN gcc -o simulator main.c -lcurl 
CMD ["./simulator"]