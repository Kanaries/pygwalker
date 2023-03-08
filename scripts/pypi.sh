HERE=$(dirname $(dirname $0) )
(cd $HERE && python -m build && python -m twine upload $HERE/dist/* --skip-existing)