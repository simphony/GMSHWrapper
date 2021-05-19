# Start form Python3.7 Dockerhub-image
FROM python:3.7

# Use "bash"
SHELL ["/bin/bash", "-c"]

# Set the enviromental variables for the script
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# install needed packages
RUN apt-get update \
    && apt-get install -y ffmpeg libsm6 libxext6 libglu1-mesa-dev libgl1-mesa-glx \
    && python -m pip install --upgrade pip

# copy packages
COPY osp /home/gmshwrapper/osp
COPY flask /home/gmshwrapper/flask
COPY tests /home/gmshwrapper/tests
COPY examples /home/gmshwrapper/examples

# copy setup files
COPY .flake8 /home/gmshwrapper
COPY setup.py /home/gmshwrapper
COPY packageinfo.py /home/gmshwrapper
COPY requirements.txt /home/gmshwrapper

# install ontology and wrappers 
WORKDIR /home/gmshwrapper
RUN pip install -r requirements.txt
RUN python setup.py install

# run unittests
RUN python -m flake8
RUN python -m unittest

# run examples
WORKDIR /home/gmshwrapper/examples
RUN python rectangle_example.py
RUN python cylinder_example.py
RUN python complex_example.py

#start entrypoint
WORKDIR /home/gmshwrapper
ENTRYPOINT ["/bin/bash", "-c", "python3.7 flask/RUN.py"]