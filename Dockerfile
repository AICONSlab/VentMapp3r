# Use a Linux Distro as a parent image
FROM ubuntu:16.04

# Set up
RUN apt-get update && apt-get install -y git wget build-essential g++ gcc cmake curl clang && \
    apt-get install -y libfreetype6-dev apt-utils pkg-config vim gfortran && \
    apt-get install -y binutils make linux-source unzip && \
    apt-get install -y apt-transport-https ca-certificates && \
    apt-get install -y python3-setuptools && \
    apt install -y libsm6 libxext6 libfontconfig1 libxrender1 libgl1-mesa-glx && \
    apt-get install -y python3-pip python3-dev && \
    cd /usr/local/bin/ && \
    ln -s /usr/bin/python3 python && \
    pip3 install --upgrade pip==20.3.4 && \
    cd ~

# Install c3d
RUN wget https://downloads.sourceforge.net/project/c3d/c3d/Nightly/c3d-nightly-Linux-x86_64.tar.gz && \
    tar -xzvf c3d-nightly-Linux-x86_64.tar.gz && mv c3d-1.1.0-Linux-x86_64 /opt/c3d && \
    rm c3d-nightly-Linux-x86_64.tar.gz
ENV PATH /opt/c3d/bin:${PATH}

# FSL
# Installing Neurodebian packages FSL
RUN wget -O- http://neuro.debian.net/lists/xenial.us-tn.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
#RUN apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

# Install FSL
RUN apt-get update && apt-get install -y --allow-unauthenticated fsl

ENV FSLDIR="/usr/share/fsl/5.0" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    POSSUMDIR="/usr/share/fsl/5.0" \
    LD_LIBRARY_PATH="/usr/lib/fsl/5.0:$LD_LIBRARY_PATH" \
    FSLTCLSH="/usr/bin/tclsh" \
    FSLWISH="/usr/bin/wish" \
    POSSUMDIR="/usr/share/fsl/5.0"

ENV PATH="/usr/lib/fsl/5.0:${PATH}"

# Install ANTs
ENV ANTSPATH="/opt/ANTs"
ENV ANTSTAR="/opt/ants.tar.gz"
RUN mkdir -p "${ANTSPATH}" && \
    wget -q --show-progress -O "${ANTSTAR}" https://huggingface.co/datasets/AICONSlab/icvmapper/resolve/dev/software/ANTs/ANTs-Linux-centos5_x86_64-v2.2.0-0740f91.tar.gz && \
    tar -xzvf "${ANTSTAR}" -C "${ANTSPATH}" --strip-components 1
ENV PATH=${ANTSPATH}:${PATH}

# Install miniconda
RUN curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -p /opt/miniconda -b && \
    rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH=/opt/miniconda/bin:${PATH}


#RUN echo -e $PWD

# Install all needed packages based on pip installation

RUN git clone -b dummy --single-branch https://github.com/mgoubran/VentMapp3r.git && \
	cd VentMapp3r && \
	pip install git+https://www.github.com/keras-team/keras-contrib.git && \
    pip install -e .[ventmapper]

# Download models, store in directory
RUN mkdir /VentMapp3r/models && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1enkZADLYj99_HdTF_jNxrxyFAHaXZDzf' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1enkZADLYj99_HdTF_jNxrxyFAHaXZDzf" -O /VentMapp3r/models/vent_multi_model.json && \
    rm -rf /tmp/cookies.txt && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=19MI05xrdg-VuIVzvJT_dr1lixu0G3KpD' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=19MI05xrdg-VuIVzvJT_dr1lixu0G3KpD" -O /VentMapp3r/models/vent_multi_model_weights.h5 && \
    rm -rf /tmp/cookies.txt && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1hsur5hMyPsT7UHSUmQeN9iegL8T2ZL5O' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1hsur5hMyPsT7UHSUmQeN9iegL8T2ZL5O" -O /VentMapp3r/models/vent_t1only_model.json && \
    rm -rf /tmp/cookies.txt && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1JBhzozGiz-mcMeF1cA9SW6PBgBTN2KSz' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1JBhzozGiz-mcMeF1cA9SW6PBgBTN2KSz" -O /VentMapp3r/models/vent_t1only_model_weights.h5 && \
    rm -rf /tmp/cookies.txt && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=17ecrsFi8ACVR_6f-mZ9jXTT-iCqClnCr' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=17ecrsFi8ACVR_6f-mZ9jXTT-iCqClnCr" -O /VentMapp3r/models/vent_t1fl_model.json && \
    rm -rf /tmp/cookies.txt && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1AveujA3q6SufALaHPVqh1nIjNQDCDXvp' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1AveujA3q6SufALaHPVqh1nIjNQDCDXvp" -O /VentMapp3r/models/vent_t1fl_model_weights.h5 && \
    rm -rf /tmp/cookies.txt

# Run ventmapper when the container launches
ENTRYPOINT ["/opt/miniconda/bin/ventmapper"]
