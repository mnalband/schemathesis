# Run testing AioHTTP app on the given port
PYTHONPATH=$(pwd)/src python test/app.py "$@"
