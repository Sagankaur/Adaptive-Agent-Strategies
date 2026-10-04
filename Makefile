IMAGE ?= adaptive-agent-strategies:test
CPUS ?= 1
MEMORY ?= 1g

.PHONY: image test

image:
	docker build -t $(IMAGE) .

# Runs the tests offline, as the calling user, with the repository mounted read-only.
test: image
	docker run --rm --network none --cpus=$(CPUS) --memory=$(MEMORY) \
		--user $$(id -u):$$(id -g) -v "$(CURDIR)":/app:ro $(IMAGE)
