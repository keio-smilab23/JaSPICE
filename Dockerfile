FROM python:3.8.10
LABEL maintainer="yuigawada@gmail.com"

WORKDIR /root
ENV DEBIAN_FRONTEND noninteractive
COPY ./ /root/jaspice

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN cd /root/jaspice && pip install -e . 

RUN apt-get update --fix-missing &&\
    apt-get install -y --fix-missing apt-utils dialog &&\
    apt-get install -y emacs less

RUN apt-get upgrade -y --fix-missing &&\
    apt-get install -y --fix-missing make &&\
    apt-get install -y --fix-missing wget &&\
    apt-get install -y --fix-missing gcc &&\
    apt-get install -y --fix-missing g++ &&\
    apt-get install -y --fix-missing bzip2 &&\
    apt-get install -y --fix-missing libboost-dev &&\
    apt-get install -y --fix-missing google-perftools &&\
    apt-get install -y --fix-missing libgoogle-perftools-dev

# JUMANPP
RUN wget 'http://nlp.ist.i.kyoto-u.ac.jp/DLcounter/lime.cgi?down=http://lotus.kuee.kyoto-u.ac.jp/nl-resource/jumanpp/jumanpp-1.02.tar.xz&name=jumanpp-1.02.tar.xz' -O /tmp/jumanpp.tar.xz &&\
    tar xJvf /tmp/jumanpp.tar.xz -C /tmp &&\
    cd /tmp/jumanpp-1.02 &&\
    cat src/Makefile.am | sed s/-m64//g > Makefile.am.new && mv Makefile.am.new src/Makefile.am &&\
    cat src/Makefile.in | sed s/-m64//g > Makefile.in.new && mv Makefile.in.new src/Makefile.in &&\
    ./configure --prefix=/usr/local/ && make && make install &&\
    rm -rf /tmp/* &&\
    rm -rf /var/cache/apk/*

# JUMAN
RUN wget 'http://nlp.ist.i.kyoto-u.ac.jp/nl-resource/juman/juman-7.01.tar.bz2' -O /tmp/juman.tar.bz2 &&\ 
    tar xf /tmp/juman.tar.bz2 -C /tmp &&\
    cd /tmp/juman-7.01 &&\ 
    ./configure --prefix=/usr/local/ --build=arm && make && make install &&\
    rm -rf /tmp/* &&\
    rm -rf /var/cache/apk/* &&\
    apt-get update && apt-get install -y --fix-missing libjuman4

# KNP
RUN apt-get install -y --fix-missing zlib1g-dev &&\
    echo "download knp ..." &&\
    wget 'https://nlp.ist.i.kyoto-u.ac.jp/DLcounter/lime.cgi?down=https://nlp.ist.i.kyoto-u.ac.jp/nl-resource/knp/knp-4.20.tar.bz2&name=knp-4.20.tar.bz2' -O /tmp/knp.tar.bz2 &&\
    tar xf /tmp/knp.tar.bz2 -C /tmp &&\
    cd /tmp/knp-4.20 / &&\
    ./configure --prefix=/usr/local/ --with-juman-prefix=/usr/local/ --build=arm && make && make install &&\
    rm -rf /tmp/* &&\
    rm -rf /var/cache/apk/*


RUN apt-get clean &&\
    apt-get autoclean -y &&\
    apt-get autoremove -y &&\
    apt-get clean &&\
    rm -rf /tmp/* /var/tmp/* &&\
    rm -rf /var/lib/apt/lists/* &&\    
    rm -f /etc/ssh/ssh_host_*

CMD /bin/bash
ENTRYPOINT ["python", "/root/jaspice/jaspice/server.py"]