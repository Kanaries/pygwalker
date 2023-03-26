#!/bin/sh
cur_dir=$(pwd)
file_dir=$(dirname $(dirname $0) )
echo $cur_dir
echo $file_dir
APP=$file_dir/app
GW=$file_dir/graphic-walker/packages/graphic-walker

(cd $file_dir; if ! command -v yarn; then npm install -g yarn; fi )

(cd $file_dir; pip install -e .)
(cd $GW; yarn link) && \
    (cd $APP; yarn link @kanaries/graphic-walker) && \
    (cd $APP; yarn) && \
    ((cd $GW; yarn build -w) & (cd $APP; yarn dev -w) );
(cd $APP; yarn unlink)
cd $cur_dir