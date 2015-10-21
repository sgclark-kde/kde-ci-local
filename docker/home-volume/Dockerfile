#DATA ONLY CONTAINER
# This container holds the install sync data in /home/jenkins
# If loading a backup the files need to be in the build dir
FROM ubuntu:trusty
MAINTAINER Scarlett Clark <sgclark@kde.org>

# These dependencies are needed to grab our tools
RUN apt-get update && apt-get install -y python \
	git \
	ssh

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

RUN git clone https://github.com/sgclark-kde/kde-ci-local.git scripts

USER root
RUN chown -R jenkins.jenkins /home/jenkins 

VOLUME /home/jenkins

CMD ["/bin/sh"]
CMD ["true"]
