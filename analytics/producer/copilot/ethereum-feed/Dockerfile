FROM public.ecr.aws/lts/ubuntu:20.04_stable

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         python3 python3-dev python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY *.sh /app/
COPY *.py /app/
COPY *.txt /app/
RUN pip install -r requirements.txt
RUN chmod +x *.sh

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
 
EXPOSE 8080

# start
CMD ["bash", "-c", "ls -la && exec /app/start.sh"]