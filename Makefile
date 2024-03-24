DEBUG_DIR = debug
DEPLOY_DIR = deploy
STATIC_DIR = static


all: clear debug deploy

debug:
	mkdir -p $(DEBUG_DIR)
	# cp -r $(STATIC_DIR)/* $(DEBUG_DIR)
	python3 build.py --debug -d $(DEBUG_DIR)

deploy:
	mkdir -p $(DEPLOY_DIR)
	# cp -r $(STATIC_DIR)/* $(DEPLOY_DIR)
	python3 build.py -d $(DEPLOY_DIR)

syncss:
	cp -r $(DEBUG_DIR)/css/ $(STATIC_DIR)/css/

clear:
	rm -rf $(DEBUG_DIR)
	rm -rf $(DEPLOY_DIR)

pages: deploy
	ghp-import -n -f -p $(DEPLOY_DIR)

.PHONY: all debug deploy clear pages
