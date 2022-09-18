FROM openaustralia/buildstep:early_release

COPY requirements.txt .

RUN apt update -y \
    && apt-get install -y python3-pip
	
RUN pip3 install -r requirements.txt

RUN useradd morph

USER morph