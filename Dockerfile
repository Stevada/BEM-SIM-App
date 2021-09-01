FROM ubuntu:18.04 

# Install Python3.7
RUN apt-get update
RUN apt-get install -y ca-certificates curl libx11-6 libexpat1 
RUN apt update
RUN apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa && apt update
RUN apt install -y python3.7 && wget https://bootstrap.pypa.io/get-pip.py && python3.7 get-pip.py
# RUN apt-get install -y ia32-libs

COPY . /usr/app/
WORKDIR /usr/app/

# Install Energyplus-9-3-0
RUN wget https://github.com/NREL/EnergyPlus/releases/download/v9.3.0/EnergyPlus-9.3.0-baff08990c-Linux-x86_64.sh \
    && chmod +x EnergyPlus-9.3.0-baff08990c-Linux-x86_64.sh \
    && echo "y\r" | ./EnergyPlus-9.3.0-baff08990c-Linux-x86_64.sh

RUN python3.7 -m pip install -r requirements.txt

CMD ["gunicorn", "app:app", "--config=config.py"]
