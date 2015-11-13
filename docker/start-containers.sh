echo "Starting data volumes"
docker run --name HOME sgclarkkde/kde-slave-home
docker run --name INSTALL sgclarkkde/kde-slave-install
echo "Starting ubuntu slave"
docker run --name ubuntu --volumes-from=HOME --volumes-from=INSTALL sgclarkkde/kde-slave-ubuntu