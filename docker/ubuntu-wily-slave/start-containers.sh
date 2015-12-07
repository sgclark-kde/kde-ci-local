echo "Starting ubuntu slave"
docker run -v /srv/jenkins:/srv/jenkins -v /home/jenkins/.ssh:/home/jenkins/.ssh sgclarkkde/kde-slave-ubuntu