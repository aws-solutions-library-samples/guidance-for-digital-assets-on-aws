FROM public.ecr.aws/lts/ubuntu:20.04_stable

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         ca-certificates \
         git \
         python3 python3-dev python3-pip \
    && rm -rf /var/lib/apt/lists/*

USER root
WORKDIR /root

# electrumx
RUN git clone https://github.com/spesmilo/electrumx.git
RUN cd electrumx && pip3 install .

COPY start.sh /root/
RUN chmod +x /root/start.sh

EXPOSE 50002

# start
CMD ["bash", "-c", "ls -la && exec /root/start.sh"]