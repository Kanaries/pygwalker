#!/bin/sh
cur_dir=$(pwd)
file_dir=$(dirname $(dirname $0) )
echo $cur_dir
echo $file_dir
APP=$file_dir/app

(cd $file_dir && if ! command -v yarn; then npm install -g yarn; fi) && \
(cd $APP && yarn && yarn build)

ret=$?
cd $cur_dir
exit $?