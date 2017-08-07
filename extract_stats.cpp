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
#include <iostream>
#include <algorithm>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <unordered_set>

#include "TorchCraft/include/replayer.h"

// compile in opt mode to get OMP

using namespace torchcraft::replayer;

inline std::vector<std::string> glob(const std::string& pat){
  using namespace std;
  glob_t glob_result;
  glob(pat.c_str(),GLOB_TILDE,NULL,&glob_result);
  vector<string> ret;
  for(unsigned int i=0;i<glob_result.gl_pathc;++i){
    ret.push_back(string(glob_result.gl_pathv[i]));
  }
  globfree(&glob_result);
  return ret;
}

inline std::vector<std::string> split(const std::string &s, char delim) {
  std::vector<std::string> result;
  std::stringstream ss;
  ss.str(s);
  std::string item;
  while (std::getline(ss, item, delim)) {
    result.push_back(item);
  }
  return result;
}

bool is_file_exist(const char *fileName)
{
  std::ifstream infile(fileName);
  return infile.good();
}

int main(int argc, char *argv[]) {
  if (argc != 3) {
    std::cout << "Need two arguments, source file path and which fold" << std::endl;
    return 1;
  }
  auto num = std::string(argv[2]);
  auto files = glob(std::string(argv[1]) + "/" + num + "/*");
  std::vector<std::string> resultstrs;
#pragma omp parallel for
  for (int k=0; k<files.size(); k++) {
    auto fname = files[k];
    auto splitted = split(fname, '/');
    auto name = splitted.at(splitted.size()-1);

    std::ifstream inRep(fname);
    Replayer r;
    inRep >> r;

    auto map = r.getRawMap();
    auto x = THByteTensor_size(map, 0);
    auto y = THByteTensor_size(map, 1);
    auto t = r.size();
    std::unordered_set<int32_t> n_units[2];
    int32_t c_ore[2], c_gas[2], n_ore[2], n_gas[2], n_psi[2], n_max_psi[2];
    c_ore[0] = 50; c_ore[1] = 50;
    c_gas[0] = 0; c_gas[1] = 0;
    n_ore[0] = 0; n_ore[1] = 0;
    n_gas[0] = 0; n_gas[1] = 0;
    n_psi[0] = 0; n_psi[1] = 0;
    n_max_psi[0] = 0; n_max_psi[1] = 0;

    for (int i=0; i<r.size(); i++) {
      auto f = r.getFrame(i);
      for (auto team : f->units) {
        if (! (team.first == 0 || team.first == 1) ) continue;
        for (auto unit : team.second) {
          n_units[team.first].insert(unit.id);
        }
      }

      for (int32_t team = 0; team <= 1; team ++)
        if (f->resources.find(team) != f->resources.end()) {
          auto res = f->resources[team];
          n_ore[team] += std::max(0, res.ore - c_ore[team]);
          n_gas[team] += std::max(0, res.gas - c_gas[team]);

          if (res.used_psi != 0) n_psi[team] = res.used_psi;
          n_max_psi[team] = std::max(res.used_psi, n_max_psi[team]);

          c_ore[team] = res.ore;
          c_gas[team] = res.gas;
        }
    }

    auto walk = THByteTensor_new();
    auto gh = THByteTensor_new();
    auto build = THByteTensor_new();
    std::vector<int> tx, ty;
    r.getMap(walk, gh, build, tx, ty);

    std::ostringstream outstr;
    outstr << name;
    outstr << " " << r.size();
    outstr << " " << n_units[0].size() << " " << n_units[1].size();
    outstr << " " << n_ore[0] << " " << n_gas[0] << " " << n_psi[0] << " " << n_max_psi[0];
    outstr << " " << n_ore[1] << " " << n_gas[1] << " " << n_psi[1] << " " << n_max_psi[1];
    outstr << " " << x << " " << y << " " << THByteTensor_sumall(walk) << " " << THByteTensor_sumall(gh);
    auto str = outstr.str();
#pragma omp critical
    resultstrs.push_back(str);
  }
  for (auto str : resultstrs) std::cout << str << "\n";
  return 0;
}

