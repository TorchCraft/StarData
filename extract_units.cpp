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

#include "TorchCraft/include/replayer.h"

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

bool is_file_exist(const char *fileName)
{
  std::ifstream infile(fileName);
  return infile.good();
}

int main(int argc, char *argv[]) {
  if (argc != 2) {
    std::cout << "Need one argument, glob of source file path" << std::endl;
    return 1;
  }
  auto dest = "/tmp";
  std::vector<std::string> files = glob(std::string(argv[1]));
  //std::random_shuffle ( files.begin(), files.end() );
  std::cout << files.size() << std::endl;
#pragma omp parallel for
  for (int k=0; k<files.size(); k++) {
    auto fname = files[k];
    auto where = fname.find("sc_uncompressed") + 15;
    auto outname = dest + fname.substr(where);
    auto tmpname = outname + ".tmp";
    if (is_file_exist(outname.c_str()) || is_file_exist(tmpname.c_str()))
      continue;
    std::cout << "doing file " << fname << '\n';

    std::ifstream inRep(fname);
    Replayer r;
    try {inRep >> r;} catch (const std::exception & e) {continue;}

    std::ofstream ofs(tmpname);
    auto map = r.getRawMap();
    auto x = THByteTensor_size(map, 0);
    auto y = THByteTensor_size(map, 1);
    auto t = r.size();
    ofs << x << " " << y << " " << t << '\n';
    for (int i=0; i<r.size(); i++) {
      auto f = r.getFrame(i);
      auto fn = r.getFrame(i+1);
      for (auto team : f->units)
        for (auto unit : team.second) {
          ofs << team.first << " " << unit.id << " " << unit.type << " " << unit.x << " " << unit.y << " ";
        }
      ofs << "\n";
    }

    ofs.close();
    if (rename(tmpname.c_str(), outname.c_str()) != 0) {
      std::cout << "Rename failed! From " << tmpname << " to " << outname << std::endl;
    }
  }
  return 0;
}
