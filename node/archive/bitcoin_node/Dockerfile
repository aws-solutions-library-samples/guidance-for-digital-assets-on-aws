FROM public.ecr.aws/lts/ubuntu:20.04_stable

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         ca-certificates \
         git \
         python3 python3-dev python3-pip \
         socat \
         openssh-server \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd

USER root
WORKDIR /root

# bitcoind
RUN wget https://bitcoincore.org/bin/bitcoin-core-0.21.1/bitcoin-0.21.1-x86_64-linux-gnu.tar.gz && \ 
    tar -xzf bitcoin-0.21.1-x86_64-linux-gnu.tar.gz && \
    ln -s bitcoin-0.21.1 bitcoin && \
    rm bitcoin-0.21.1-x86_64-linux-gnu.tar.gz
COPY bitcoin.conf /root/
RUN wget https://raw.githubusercontent.com/bitcoin/bitcoin/master/share/rpcauth/rpcauth.py

# electrumx
RUN git clone https://github.com/spesmilo/electrumx.git
RUN cd electrumx && pip3 install .

COPY docker-ssh.sh /root/
RUN chmod +x /root/docker-ssh.sh

COPY start.sh /root/
RUN chmod +x /root/start.sh

EXPOSE 50002
EXPOSE 22

# start
CMD ["bash", "-c", "ls -la && exec /root/start.sh"]