#!/bin/bash

set -xeuo pipefail

REL=rel-1.2.1

[ -f cadical-$REL.tar.gz ] ||
wget -c https://github.com/arminbiere/cadical/archive/$REL.tar.gz \
    -O cadical-$REL.tar.gz

[ -d cadical-$REL ] ||
tar xzf cadical-$REL.tar.gz

cd cadical-$REL

if ! [ -f makefile ]; then
    ./configure CXXFLAGS="-fPIC"
fi

make -j$(nproc)

${CXX:-g++} \
    -shared \
    -o ../libcadical.so \
    -Wl,--whole-archive build/libcadical.a -Wl,--no-whole-archive
