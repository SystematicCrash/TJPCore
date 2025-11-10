start:
	echo "starting the server...."
	uvicorn http_api.endpoints:app --port 9220 --reload
