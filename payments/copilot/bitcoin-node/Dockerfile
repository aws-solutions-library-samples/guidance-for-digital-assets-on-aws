FROM public.ecr.aws/lts/ubuntu:20.04_stable

ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         awscli \
         wget \
         ca-certificates \
         git \
         jq \
         python3 python3-dev python3-pip \
    && rm -rf /var/lib/apt/lists/*

USER root
WORKDIR /root

# bitcoind
RUN wget https://bitcoincore.org/bin/bitcoin-core-22.0/bitcoin-22.0-x86_64-linux-gnu.tar.gz && \ 
    tar -xzf bitcoin-22.0-x86_64-linux-gnu.tar.gz && \
    ln -s bitcoin-22.0 bitcoin && \
    rm bitcoin-22.0-x86_64-linux-gnu.tar.gz
COPY bitcoin.conf /root/

COPY start.sh /root/
RUN chmod +x /root/start.sh
 
EXPOSE 8332
EXPOSE 28332

# start
CMD ["bash", "-c", "ls -la && exec /root/start.sh"]