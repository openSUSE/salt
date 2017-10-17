#!/bin/bash
#
# Update html.tar.bz2 documentation tarball
# Author: Bo Maryniuk <bo@suse.de>
#

function check_env() {
    for cmd in "sphinx-build" "make" "quilt"; do
	if [ -z "$(which $cmd 2>/dev/null)" ]; then
	    echo "Error: '$cmd' is missing."
	    exit 1;
	fi
    done
}

function quilt_setup() {
    quilt setup salt.spec
    cd $1
    quilt push -a
}

function build_docs() {
    cd $1
    make html
    rm _build/html/.buildinfo
    cd _build/html
    chmod -R -x+X *
    cd ..
    tar cvf - html | bzip2 > /tmp/html.tar.bz2
}

function write_changelog() {
    mv salt.changes salt.changes.previous
    TIME=$(date -u +'%a %b %d %T %Z %Y')
    MAIL=$1
    SEP="-------------------------------------------------------------------"
    cat <<EOF > salt.changes
$SEP
$TIME - $MAIL

- Updated html.tar.bz2 documentation tarball.

EOF
    cat salt.changes.previous >> salt.changes
    rm salt.changes.previous
}

if [ -z "$1" ]; then
    echo "Usage: $0 <your e-mail>"
    exit 1;
fi

check_env;
START=$(pwd)
SRC_DIR="salt-$(cat salt.spec | grep ^Version: | cut -d: -f2 | sed -e 's/[[:blank:]]//g')";
quilt_setup $SRC_DIR
build_docs doc

cd $START
rm -rf $SRC_DIR
mv /tmp/html.tar.bz2 $START

echo "Done"
echo "---------------"
