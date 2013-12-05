Github Recs
===========

Exploration of building a Github recommendations system.

Preqs
-----

Follow the instructions in:

  * `src/dataset/README.md`
  * `lib/README.md`

Usage
-----

Build  a dataset:

    mkdir data
    python src/dataset/dataset.py --clear --dataset=golang_recent --action=select
    python src/dataset/dataset.py --dataset=golang_recent --action=export
    python src/dataset/dataset.py --dataset=golang_recent --action=copy_local

K-Fold the data

    python src/kfold/kfold.py --k=4 --input=data --dataset=golang_recent
