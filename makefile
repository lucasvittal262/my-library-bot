local-build-deploy:
	@echo ">>> Building Docker image..."
	@echo ""
	docker build . -t lucasvittal/my-lib-bot:$(VERSION)
	@echo ""
	@echo ">>> Pushing Docker image..."
	@echo ""
	docker push lucasvittal/my-lib-bot:$(VERSION)
	@echo ""
	@echo ">>> Uninstalling existing Helm release..."
	@echo ""
	helm uninstall my-lib-bot --ignore-not-found
	@echo ""
	@echo ">>> Installing Helm chart..."
	@echo ""
	helm install my-lib-bot ./helm/my-lib-bot/ -f ./helm/my-lib-bot/values-dev.yaml
	@echo ""
	@echo ">>> Enabling ingress..."
	@echo ""
	microk8s enable ingress
	@grep -q "my-lib-bot.local" /etc/hosts || echo "127.0.0.1 my-lib-bot.local" | sudo tee -a /etc/hosts
	@echo ""
	@echo ">>> Waiting for ingress controller to be ready..."
	@echo ""
	kubectl wait --namespace ingress --for=condition=ready pod --selector=name=nginx-ingress-microk8s --timeout=120s
	@echo ""
	@echo ">>> Done! App available at http://my-lib-bot.local"
	@echo ""

setup-local-env:
	@echo "Starting port-forwards..."
	@kubectl port-forward svc/my-lib-bot-qdrant 6333:6333 > /dev/null 2>&1 & \
	kubectl port-forward svc/my-lib-bot-qdrant 6334:6334 > /dev/null 2>&1 & \
	kubectl port-forward svc/my-lib-bot-qdrant 6335:6335 > /dev/null 2>&1 & \
	kubectl port-forward svc/my-lib-bot-mongodb 27017:27017 > /dev/null 2>&1 & \
	echo "Qdrant available at http://localhost:6333" && \
	echo "MongoDB available at mongodb://localhost:27017" && \
	echo "Port-forwards started."

unit-tests:
	@.venv/bin/python -m pytest src/tests/units

integration-tests:
	@.venv/bin/python -m pytest src/tests/integrations
