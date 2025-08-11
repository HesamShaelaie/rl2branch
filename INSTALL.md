## Packages to install

1. [SCIP](https://www.scipopt.org/) 7.0.2 (we recommend installing SCIPOptSuite).
1. [PySCIPOpt](https://github.com/scipopt/PySCIPOpt).
1. A custom version of [Ecole](https://github.com/lascavana/ecole) (includes a new observation).
1. [PyTorch](https://pytorch.org/).
1. [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/en/latest/).
1. Optional: [wandb](https://wandb.ai/) (tool to log training metrics).


Here are detailed installation instructions to create a working conda environment. Other versions of the packages may produce different results and/or have compatibility issues.
```
# make sure you have configured SCIP correctly #
echo $SCIPOPTDIR

# create conda environment #
conda create -n rl2branch python=3.8
conda activate rl2branch

# install pyscipopt #
pip install pyscipopt==3.0.4

# install necessary packages #
pip install cython
pip install wheel
pip install numpy
pip install scikit-build

# Ecole tree-mdp #
git clone git@github.com:lascavana/ecole.git
cd ecole-tree-mdp
mkdir wheels
python setup.py bdist_wheel --dist-dir wheels
pip install --no-index --find-links=wheels ecole

# pytorch #
conda install pytorch==1.7.1 torchvision==0.8.2 torchaudio==0.7.2 cpuonly -c pytorch

# pytorch geometric #
TORCH=1.7.1
CUDA=cpu
pip install torch-scatter -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
pip install torch-sparse -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
pip install torch-cluster -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
pip install torch-spline-conv -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
pip install torch-geometric==1.6.3
```
