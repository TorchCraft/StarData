# StarData

## Overview

We release the largest StarCraft: Brood War replay dataset yet, with 65646 games. The full dataset after compression is 365 GB, 1535 million frames, and 496 million player actions. The entire frame data was dumped out at 8 frames per second. We made a big effort to ensure this dataset is clean and has mostly high quality replays. You can access it with TorchCraft in C++, Python, and Lua. The replays are in an AWS S3 bucket at s3://stardata. Read below for more details, or [our whitepaper on arXiv](https://arxiv.org/abs/1708.02139) for more details.

## Installing TorchCraft

Note: The current set of replays are only compatible with the 1.3.0 version of torchcraft included here.

Simply do 

```
git submodule update --init
cd TorchCraft
pip install .
```

More documentation can be found at https://github.com/TorchCraft/TorchCraft. Realistically, you will only need the replayer modules, which means you can ignore most of the connecting to starcraft parts. Check out the code to document its use
- [For python](https://github.com/TorchCraft/TorchCraft/blob/master/py/pyreplayer.cpp)
- For C++: [replayer.h](https://github.com/TorchCraft/TorchCraft/blob/master/include/replayer.h), [frame.h](https://github.com/TorchCraft/TorchCraft/blob/master/include/frame.h)
- For Lua: [replayer](https://github.com/TorchCraft/TorchCraft/blob/master/lua/replayer_lua.h), and [frame](https://github.com/TorchCraft/TorchCraft/blob/master/lua/frame_lua.h)

Note: Please make sure you have libzstd-1.1.4+, torchcraft will compile without it but won't be able to read the replays.

## Downloading the Data

- [Link to the original replays](https://dl.fbaipublicfiles.com/stardata/original_replays.tar.gz)
- Dumped replays, readable by TorchCraft 1.4, dumped on [this commit](https://github.com/TorchCraft/TorchCraft/commit/a28b153ff10e1826f531d407f723c5e0ccbd488b)
  are available at the following links. They have been chunked to help in downloading.
  - [00](https://dl.fbaipublicfiles.com/stardata/dumped_replays/0.tar.gz).
    [01](https://dl.fbaipublicfiles.com/stardata/dumped_replays/1.tar.gz).
    [02](https://dl.fbaipublicfiles.com/stardata/dumped_replays/2.tar.gz).
    [03](https://dl.fbaipublicfiles.com/stardata/dumped_replays/3.tar.gz).
    [04](https://dl.fbaipublicfiles.com/stardata/dumped_replays/4.tar.gz).
    [05](https://dl.fbaipublicfiles.com/stardata/dumped_replays/5.tar.gz).
    [06](https://dl.fbaipublicfiles.com/stardata/dumped_replays/6.tar.gz).
    [07](https://dl.fbaipublicfiles.com/stardata/dumped_replays/7.tar.gz).
    [08](https://dl.fbaipublicfiles.com/stardata/dumped_replays/8.tar.gz).
    [09](https://dl.fbaipublicfiles.com/stardata/dumped_replays/9.tar.gz).
    [10](https://dl.fbaipublicfiles.com/stardata/dumped_replays/10.tar.gz).
    [11](https://dl.fbaipublicfiles.com/stardata/dumped_replays/1.tar.gz).
    [12](https://dl.fbaipublicfiles.com/stardata/dumped_replays/12.tar.gz).
    [13](https://dl.fbaipublicfiles.com/stardata/dumped_replays/13.tar.gz).
    [14](https://dl.fbaipublicfiles.com/stardata/dumped_replays/14.tar.gz).
    [15](https://dl.fbaipublicfiles.com/stardata/dumped_replays/15.tar.gz).
    [16](https://dl.fbaipublicfiles.com/stardata/dumped_replays/16.tar.gz).
    [17](https://dl.fbaipublicfiles.com/stardata/dumped_replays/17.tar.gz).
    [18](https://dl.fbaipublicfiles.com/stardata/dumped_replays/18.tar.gz).
    [19](https://dl.fbaipublicfiles.com/stardata/dumped_replays/19.tar.gz).
  - Standardized [train](https://dl.fbaipublicfiles.com/stardata/dumped_replays/train.list),
                 [valid](https://dl.fbaipublicfiles.com/stardata/dumped_replays/valid.list), and
                 [test](https://dl.fbaipublicfiles.com/stardata/dumped_replays/test.list) sets are also available.
                 [Here](https://dl.fbaipublicfiles.com/stardata/dumped_replays/all.list) is a list of all the files.

## Reproducing Results

Some of the reproduction scripts are included, others scripts will be added as 
soon as we clean up the code and make it easy to install/run. Simply `make` and
you're good to go. All cpp files can be run like `script /path/to/replays/**/*.rep`

- extract_stats tells you some stats about the replays
- extract_units preprocesses for battle clustering
- get_corrupt_replays tells you what replays are considered corrupt
- cluster.py can be run on the output of extract_units to do battle clustering.

## Attributions

The white paper for the dataset is at:

Lin, Z., G., Jonas, K., Vasil, Synnaeve, G., AIIDE 2017. _STARDATA: A StarCraft AI Research Dataset_ ([arxiv](https://arxiv.org/abs/1708.02139))

We attribute most of the replays to [bwrep](http://bwreplays.com/) and [G. Synnaeve, P. Bessiere, A Dataset for StarCraft AI & an Example of Armies Clustering, 2012.](https://arxiv.org/pdf/1211.4552.pdf)
Please see the paper for a complete list of references.

## License

StarData is BSD-licensed. We also provide an additional patent grant.
