BOOTSTRAP_DIR = /usr/share/javascript/bootstrap
BOOTSTRAP_VER = 3.2.0

all: clean getbootstrap
	# build css
	lessc goopg-bootstrap.less css/goopg-bootstrap.css
	# fix font exposing
	sed "s~url('../fonts/~url('chrome-extension://__MSG_@@extension_id__/lib/fonts/~g" -i css/goopg-bootstrap.css
	# copy what we need
	mv bootstrap/fonts/ .
	# delete what we don't
	rm -fr bootstrap


clean:
	rm -fr fonts
	rm -fr bootstrap*
	rm -f css/goopg-bootstrap.css


getbootstrap:
	if [ -d "$(BOOTSTRAP_DIR)" ] ; then cp -r $(BOOTSTRAP_DIR) bootstrap ; \
	else \
		curl -L -o bootstrap.tar.gz https://github.com/twbs/bootstrap/archive/v$(BOOTSTRAP_VER).tar.gz ; \
		tar xzf bootstrap.tar.gz ; \
		mv bootstrap-$(BOOTSTRAP_VER)/ bootstrap ; \
		rm bootstrap.tar.gz ; \
	fi

