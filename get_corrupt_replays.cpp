/**
 * Copyright (c) 2017-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant 
 * of patent rights can be found in the PATENTS file in the same directory.
 */
extern "C" {
#include <TH/TH.h>
#include <luaT.h>
#include <lua.h>
#include <lauxlib.h>
#include <lualib.h>
}

#include <glob.h>
#include <stdio.h>
#include <iostream>
#include <algorithm>
#include <fstream>
#include <string>
#include <vector>
#include <thread>

#include "TorchCraft/include/replayer.h"

// compile in opt mode to get OMP

// Given a list of replays, prints the corrupt replays out to stdout
// input:
//    - source glob, example: /path/to/source/**/*.rep
//
// A replay is corrupt if in the last half of the game,
//  - it uses less than 70% of the total resources collected
//  - I tested number of deaths, but sometimes the bug would just command
//    units to their death, so it was not very informative...
//  - This is a heuristic based off of mostly visual inspection :) most replays
//    have this percentage > 85%, with a few very late games having ~75%
//
//  This actually gets some low-skill games as well, but I think that's okay

using namespace torchcraft::replayer;

inline std::vector<std::string> glob(const std::string& pat){
  using namespace std;
  glob_t glob_result;
  glob(pat.c_str(),GLOB_TILDE,nullptr,&glob_result);
  vector<string> ret;
  for(unsigned int i=0;i<glob_result.gl_pathc;++i){
    ret.push_back(string(glob_result.gl_pathv[i]));
  }
  globfree(&glob_result);
  return ret;
}

bool is_file_exist(const char *fileName)
{
  std::ifstream infile(fileName);
  return infile.good();
}

int main(int argc, char *argv[]) {
  if (argc < 2) {
    std::cout << "Needs 1 argument, the input glob\n";
    return 1;
  }
  std::vector<std::string> files = glob(std::string(argv[1]));
  std::cerr << files.size() << std::endl;
#pragma omp parallel for
  for (int k=0; k<files.size(); k++) {
    auto fname = files[k];
    auto where = fname.find("dumped_replays");

    std::ifstream inRep(fname);
    Replayer r;
    try {
      inRep >> r;
      int ore = 0, gas = 0, used_ore = 0, used_gas = 0,
          deaths = 0, lastunits = 0;
      for (int i=0; i<r.size(); i++) {
        auto f = r.getFrame(i);
        int cur_ore = 0, cur_gas = 0, cur_units = 0;
        for (auto p : f->resources) {
          cur_ore += p.second.ore;
          cur_gas += p.second.gas;
        }
        for (auto p : f->units) cur_units += p.second.size();

        // these are just approximations, since you can gain and lose in the
        // same frame and it won't pick it up, but it shouldn't matter.
        if (i > r.size() / 2) {
          used_ore += std::max(0, ore - cur_ore);
          used_gas += std::max(0, gas - cur_gas);
          deaths += std::max(0, lastunits - cur_units);
        }

        ore = cur_ore;
        gas = cur_gas;
        lastunits = cur_units;
      }
      auto pused_ore = (double)(used_ore) / (used_ore + ore);
      auto pused_gas = (double)(used_gas) / (used_gas + gas);
      if ((pused_ore + pused_gas) / 2 < 0.7) { }
      else continue;
    }
    catch (const std::exception & e) {
      std::cout << "Exception :(\n";
    }

#pragma omp critical
    std::cout << fname << std::endl;
  }
  return 0;
}
