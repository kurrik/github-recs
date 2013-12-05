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

Train Apriori rules

    python src/apriori/apriori.py \
      --ruleset=data/golang_recent/kfold/repo_trans.ruleset_0 \
      --train=data/golang_recent/kfold/repo_trans.train_0 \
      --minsup=2 --minconf=100 --clear

Test Apriori rules

    python src/apriori/apriori.py \
      --ruleset=data/golang_recent/kfold/repo_trans.ruleset_0 \
      --test=data/golang_recent/kfold/repo_trans.test_0
