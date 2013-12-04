Github Recs
===========

Exploration of building a Github recommendations system.

Usage
-----

Build  a dataset:

    python src/dataset/dataset.py --clear --dataset=golang_recent --action=select
    python src/dataset/dataset.py --dataset=golang_recent --action=export
    python src/dataset/dataset.py --dataset=golang_recent --action=copy_local

K-Fold the data

    python src/kfold/kfold.py --k=4 --input=data --dataset=golang_recent
