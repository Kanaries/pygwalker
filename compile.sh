cur_dir=$(pwd)
file_dir=$(dirname $0)
echo $cur_dir
echo $file_dir
cd $file_dir/graphic-walker
yarn && yarn build
cp packages/graphic-walker/dist/graphic-walker.umd.js ../pygwalker/templates/
cd $cur_dir