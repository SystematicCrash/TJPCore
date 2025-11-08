start:
	echo "starting the server...."
	uvicorn http_api.endpoints:app --port 8080 --reload
