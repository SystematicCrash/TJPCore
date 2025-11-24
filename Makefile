start:
	echo "starting the server...."
	uvicorn http_api.endpoints:app --port 9220 --reload

push:
	@echo "Pushing to main remote..."
	@git push main
	@echo "Pushing to origin remote..."
	@git push origin
