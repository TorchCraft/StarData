all:
	g++ -std=c++11 extract_units.cpp TorchCraft/replayer/*.cpp -I${HOME}/torch/install/include/ -L${HOME}/torch/install/lib -ITorchCraft/include -lTH -o extract_units
	g++ -std=c++11 extract_stats.cpp TorchCraft/replayer/*.cpp -I${HOME}/torch/install/include/ -L${HOME}/torch/install/lib -ITorchCraft/include -lTH -o extract_stats
	g++ -std=c++11 get_corrupt_replays.cpp TorchCraft/replayer/*.cpp -I${HOME}/torch/install/include/ -L${HOME}/torch/install/lib -ITorchCraft/include -lTH -o get_corrupt_replays

clean:
	rm extract_stats get_corrupt_replays extract_units
