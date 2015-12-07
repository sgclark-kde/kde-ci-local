#DATA ONLY CONTAINER
# This container holds the install sync data in /home/jenkins
# If loading a backup the files need to be in the build dir
FROM ubuntu:trusty
MAINTAINER Scarlett Clark <sgclark@kde.org>

RUN groupadd -g 1000 jenkins
RUN useradd -m -g 1000 -u 1000 -d /home/jenkins jenkins 

USER jenkins
RUN mkdir /home/jenkins/.ssh

#These keys need to be in path (generated on your host and placed in /var/lib/jenkins/scripts/docker/home-volume on master)
# Be sure to add these files to gitignore
ADD id_rsa /home/jenkins/.ssh/
ADD id_rsa.pub /home/jenkins/.ssh/
ADD known_hosts /home/jenkins/.ssh/
ADD authorized_keys /home/jenkins/.ssh/
ADD jenkins_install /home/jenkins/.ssh/
ADD config /home/jenkins/.ssh/

USER root
RUN chown -R jenkins.jenkins /home/jenkins/.ssh 
RUN chmod 644 /home/jenkins/.ssh/*
RUN chmod 640 /home/jenkins/.ssh/authorized_keys
RUN chmod 600 /home/jenkins/.ssh/id_rsa
RUN chmod 600 /home/jenkins/.ssh/jenkins_install

VOLUME /home/jenkins/.ssh

RUN echo "Be sure to run docker run --name HOME sgclarkkde/kde-slave-home on the slave host." 

CMD ["/bin/sh"]
CMD ["true"]