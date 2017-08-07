'''
Copyright (c) 2017-present, Facebook, Inc.
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree. An additional grant 
of patent rights can be found in the PATENTS file in the same directory.
'''
import os

from os import path
from glob import glob
import argparse
import multiprocessing
import time
import traceback
import math

import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth

from itertools import cycle

'''
I do something like:
    find path/unit_loc_dump/10 -name 'TL_*.rep' |xargs -n1 -I% -P10 python cluster.py -i % -o path/battles/cluster/10/ -x 200 -y 200 -t 20 -b 0.5
'''

parser = argparse.ArgumentParser(description='Cluster some starcraft dumped replays. Each t is actually 3 frames combined')
parser.add_argument('-i', '--input', required=True, help='input glob')
parser.add_argument('-o', '--output', required=True, help='output folder')
# for -x, -y, -t, if you have none of --mrel, --trel, or --unit, then it behaves
# like division: x /= (args.x) is done. If you do have one of the --*rel or
# --unit options, instead it does x *= (args.x)
parser.add_argument('-x', '--x_scale', default=1, type=float, help='scale x axis, x /= x_scale')
parser.add_argument('-y', '--y_scale', default=1, type=float, help='scale y ayis, y /= y_scale')
parser.add_argument('-t', '--t_scale', default=1, type=float, help='scale t atis, t /= t_scale')
parser.add_argument('-b', '--bandwidth', default=-1, type=float, help='Bandwidth for mean shift, use a negative number to force autodetection')
parser.add_argument('--mrel', action='store_true', default=False, help='x_scale and y_scale accepts a decimal, and x and y are scaled to 1')
parser.add_argument('--trel', action='store_true', default=False, help='t_scale accepts a decimal, and t is scaled to 1')
parser.add_argument('--unit', action='store_true', default=False,
                    help='Use N(0, 1) normalization, incomaptible with mrel and trel.'
                         '--{x,y,t}_scale are used as decimals')
parser.add_argument('--min_deaths', default=3, type=int, help='How many deaths in each cluster is a "battle"')
# This parameter is pretty sensitive, I found that 0.5 is too high. I haven't
# experimented whether it's too low or the averaging centers approach is too
# heavy-handed.
parser.add_argument('--merge_sim', default=0.4, type=float,
                    help='If two bounding boxes are more than this similar (via Jaccard), merge them')
parser.add_argument('--bound_with_deaths', default=False, action='store_true',
                    help='Build bounding boxes with just deaths')

parser.add_argument('--t_padding', default=2, type=float,
                    help='Seconds before and after deaths to pad to')

parser.add_argument('-s', '--show', action='store_true', default=False, help='Whether to show plot or not')

args = parser.parse_args()
import matplotlib
if not args.show:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Only the combat units
id2unit = [
    ("Terran_Marine", "0"),
    ("Terran_Ghost", "1"),
    ("Terran_Vulture", "2"),
    ("Terran_Goliath", "3"),
    ("Terran_Siege_Tank_Tank_Mode", "5"),
    ("Terran_SCV", "7"),
    ("Terran_Wraith", "8"),
    ("Terran_Science_Vessel", "9"),
    ("Terran_Dropship", "11"),
    ("Terran_Battlecruiser", "12"),
    ("Terran_Vulture_Spider_Mine", "13"),
    ("Terran_Nuclear_Missile", "14"),
    ("Terran_Civilian", "15"),
    ("Terran_Siege_Tank_Siege_Mode", "30"),
    ("Terran_Firebat", "32"),
    #("Spell_Scanner_Sweep", "33"),
    ("Terran_Medic", "34"),
    # ("Zerg_Larva", "35"),
    # ("Zerg_Egg", "36"),
    ("Zerg_Zergling", "37"),
    ("Zerg_Hydralisk", "38"),
    ("Zerg_Ultralisk", "39"),
    ("Zerg_Broodling", "40"),
    ("Zerg_Drone", "41"),
    ("Zerg_Overlord", "42"),
    ("Zerg_Mutalisk", "43"),
    ("Zerg_Guardian", "44"),
    ("Zerg_Queen", "45"),
    ("Zerg_Defiler", "46"),
    ("Zerg_Scourge", "47"),
    ("Zerg_Infested_Terran", "50"),
    ("Terran_Valkyrie", "58"),
    ("Zerg_Cocoon", "59"),
    ("Protoss_Corsair", "60"),
    ("Protoss_Dark_Templar", "61"),
    ("Zerg_Devourer", "62"),
    ("Protoss_Dark_Archon", "63"),
    ("Protoss_Probe", "64"),
    ("Protoss_Zealot", "65"),
    ("Protoss_Dragoon", "66"),
    ("Protoss_High_Templar", "67"),
    ("Protoss_Archon", "68"),
    ("Protoss_Shuttle", "69"),
    ("Protoss_Scout", "70"),
    ("Protoss_Arbiter", "71"),
    ("Protoss_Carrier", "72"),
    # ("Protoss_Interceptor", "73"),
    ("Protoss_Reaver", "83"),
    ("Protoss_Observer", "84"),
    # ("Protoss_Scarab", "85"),
    # ("Critter_Rhynadon", "89"),
    # ("Critter_Bengalaas", "90"),
    # ("Critter_Scantid", "93"),
    # ("Critter_Kakaru", "94"),
    # ("Critter_Ragnasaur", "95"),
    # ("Critter_Ursadon", "96"),
    ("Zerg_Lurker_Egg", "97"),
    ("Zerg_Lurker", "103"),
    # ("Spell_Disruption_Web", "105"),
    # ("Terran_Command_Center", "106"),
    # ("Terran_Comsat_Station", "107"),
    # ("Terran_Nuclear_Silo", "108"),
    # ("Terran_Supply_Depot", "109"),
    # ("Terran_Refinery", "110"),
    # ("Terran_Barracks", "111"),
    # ("Terran_Academy", "112"),
    # ("Terran_Factory", "113"),
    # ("Terran_Starport", "114"),
    # ("Terran_Control_Tower", "115"),
    # ("Terran_Science_Facility", "116"),
    # ("Terran_Covert_Ops", "117"),
    # ("Terran_Physics_Lab", "118"),
    # ("Terran_Machine_Shop", "120"),
    # ("Terran_Engineering_Bay", "122"),
    # ("Terran_Armory", "123"),
    ("Terran_Missile_Turret", "124"),
    ("Terran_Bunker", "125"),
    # ("Zerg_Infested_Command_Center", "130"),
    # ("Zerg_Hatchery", "131"),
    # ("Zerg_Lair", "132"),
    # ("Zerg_Hive", "133"),
    # ("Zerg_Nydus_Canal", "134"),
    # ("Zerg_Hydralisk_Den", "135"),
    # ("Zerg_Defiler_Mound", "136"),
    # ("Zerg_Greater_Spire", "137"),
    # ("Zerg_Queens_Nest", "138"),
    # ("Zerg_Evolution_Chamber", "139"),
    # ("Zerg_Ultralisk_Cavern", "140"),
    # ("Zerg_Spire", "141"),
    # ("Zerg_Spawning_Pool", "142"),
    ("Zerg_Creep_Colony", "143"),
    ("Zerg_Spore_Colony", "144"),
    ("Zerg_Sunken_Colony", "146"),
    # ("Zerg_Extractor", "149"),
    # ("Protoss_Nexus", "154"),
    # ("Protoss_Robotics_Facility", "155"),
    # ("Protoss_Pylon", "156"),
    # ("Protoss_Assimilator", "157"),
    # ("Protoss_Observatory", "159"),
    # ("Protoss_Gateway", "160"),
    # ("Protoss_Photon_Cannon", "162"),
    # ("Protoss_Citadel_of_Adun", "163"),
    # ("Protoss_Cybernetics_Core", "164"),
    # ("Protoss_Templar_Archives", "165"),
    # ("Protoss_Forge", "166"),
    # ("Protoss_Stargate", "167"),
    # ("Protoss_Fleet_Beacon", "169"),
    # ("Protoss_Arbiter_Tribunal", "170"),
    # ("Protoss_Robotics_Support_Bay", "171"),
    ("Protoss_Shield_Battery", "172"),
    # ("Resource_Mineral_Field", "176"),
    # ("Resource_Mineral_Field_Type_2", "177"),
    # ("Resource_Mineral_Field_Type_3", "178"),
    # ("Resource_Vespene_Geyser", "188"),
    # ("Spell_Dark_Swarm", "202"),
]
id2unit = {int(b): a for a, b in id2unit}
badunits = np.array(list(id2unit.keys()))


def parse_file(fn):
    with open(fn) as infile:
        data = infile.readlines()
    max_y, max_x, max_t = [int(x) for x in data[0].split(' ')]
    data = [np.fromstring(d, dtype='int32', sep=' ').reshape(-1, 5) for d in data[1:] if d.strip() != ""]
    data = [d[d[:, 0] != -1] for d in data]
    data = [d[np.in1d(d[:, 2], badunits, True)] for d in data]
    ids = [d[:, 1] for d in data]
    deaths = [np.setdiff1d(x, y, assume_unique=True) for x, y in zip(ids[:-1], ids[1:])]
    xyt = []
    for t, (d, death) in enumerate(zip(data[:-1], deaths)):
        dead = np.compress(np.in1d(d[:, 1], death), d, axis=0)
        if dead.size > 0:
            xyt.append(np.concatenate([dead[:, 3:], t * np.ones((death.size, 1))], axis=1))
    if len(xyt) == 0:
        return data, xyt, lambda x: x, lambda x: x, False, None
    xyt = np.concatenate(xyt, axis=0)

    if args.unit:
        if args.mrel or args.trel:
            raise ValueError("Cannot supply both --unit and one of --mrel or --trel")
        mean = xyt.mean(axis=0)
        std = xyt.std(axis=0) + 1e-2

    xs, ys, ts = args.x_scale, args.y_scale, args.t_scale
    if args.mrel:
        xs /= max_x
        ys /= max_y
    elif not args.unit:
        xs = 1 / xs
        ys = 1 / ys
    if args.trel:
        ts /= max_t
    elif not args.unit:
        ts = 0.042 * 3 / ts  # convert frames to seconds

    scalar = np.array([xs, ys, ts])

    def transform(xyt):
        if args.unit:
            xyt = (xyt - mean) / std
        return xyt * scalar

    teams = [d[:, 0] for d in data]
    teams = np.unique(np.concatenate(teams))

    def untransform(xyt):
        if args.unit:
            xyt = xyt * std + mean
        return xyt / scalar

    return data, transform(xyt), transform, untransform, teams.size <= 3, (max_x, max_y, max_t)


def drawbox(ax, rectangle, color='b', alpha=0.2):
    x = rectangle[0:2]
    y = rectangle[2:4]
    z = rectangle[4:6]
    for i in x:
        Y, Z = np.meshgrid(y, z)
        ax.plot_surface(i, Y, Z, alpha=alpha, color=color)
    for i in y:
        X, Z = np.meshgrid(x, z)
        ax.plot_surface(X, i, Z, alpha=alpha, color=color)
    for i in z:
        X, Y = np.meshgrid(x, y)
        ax.plot_surface(X, Y, i, alpha=alpha, color=color)


def cluster(arg):
    infn, outfn = arg
    outfn = outfn[:-4]
    _cluster(infn, outfn)
    '''
    for i in range(10):
        try:
            _cluster(infn, outfn)
            return
        except:
            traceback.print_exc()
            try:
                os.remove(outfn + '.lock')
            except:
                pass
            time.sleep(1)
    print("FAILED {} => {}".format(infn, outfn))
    '''


def _cluster(infn, outfn):
    if path.exists(outfn + '.lock') or path.exists(outfn + '.txt'):
        return
    open(outfn + '.lock', 'w').close()
    print("doing " + infn)
    data, xyt, transform, untransform, valid, maxes = parse_file(infn)
    if not valid:
        return
    bandwidth = args.bandwidth
    if bandwidth < 0:
        bandwidth = estimate_bandwidth(xyt, quantile=0.2, n_samples=500)

    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(xyt)
    centers = ms.cluster_centers_
    radius = bandwidth
    centers = untransform(centers)
    radius = untransform(radius)
    xyt = untransform(xyt)

    labels = ms.labels_
    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)
    few = np.bincount(labels) < args.min_deaths
    extract_battles(outfn + '.txt', data, ms, maxes, xyt, transform, untransform)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, too_few in zip(range(n_clusters_), few):
        my_members = labels == k
        cluster_center = centers[k]
        if too_few:
            col = 'black'
        else:
            col = next(colors)
            ax.scatter(cluster_center[0], cluster_center[1], cluster_center[2], 'o', c=col, s=100)
        ax.scatter(xyt[my_members, 0], xyt[my_members, 1], xyt[my_members, 2], c=col)
    if args.show:
        plt.show()
    plt.savefig(outfn + ".png")
    plt.close(fig)
    try:
        os.remove(outfn + '.lock')
    except:
        pass


def radius_to_rect(center, x_radius, y_radius, maxes, before, after):
    x_max, y_max, t_max = maxes
    before = math.floor(max(0, before))
    after = math.ceil(min(t_max, after))
    xmin = center[0] - x_radius
    xmin = max(0, min(xmin, x_max - 2 * x_radius))
    xmax = center[0] + x_radius
    xmax = min(x_max, max(2 * x_radius, xmax))
    ymin = center[1] - y_radius
    ymin = max(0, min(ymin, y_max - 2 * y_radius))
    ymax = center[1] + y_radius
    ymax = min(y_max, max(2 * y_radius, ymax))

    xmin, xmax, ymin, ymax = [int(x) for x in [xmin, xmax, ymin, ymax]]

    return (xmin, xmax, ymin, ymax, before, after)


def filter_rectangle(units, rectangle, maxes):
    xmin, xmax, ymin, ymax, before, after = rectangle
    units = np.concatenate(units[before:after])
    fx = units[:, 3]
    fy = units[:, 4]
    return units[
        (fx >= xmin) * (fx <= xmax) *
        (fy >= ymin) * (fy <= ymax)]


def extract_battles(outfn, data, ms, maxes, deaths, transform, untransform,
                    x_radius=100, y_radius=100,
                    ):
    '''
    Outputs a text file to `outfn`
    Each battle is
        xmin, xmax, ymin, ymax, tmin, tmax
        list of units and counts for player 0
        list of units and counts ids for player 1
    repeated for every battle that occurs.
    '''
    max_x, max_y, max_t = maxes
    if args.bound_with_deaths:
        predict_with = deaths
    else:
        cdata = [np.concatenate([d, t * np.ones((d.shape[0], 1))], axis=1) for t, d in enumerate(data)]
        cdata = np.concatenate(cdata)
        predict_with = cdata[:, 3:]
    predict_with = transform(predict_with)
    x = ms.predict(predict_with)
    labels = ms.labels_
    few = np.bincount(labels) < args.min_deaths
    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)
    out = []
    rects = []
    for k, too_few in zip(range(n_clusters_), few):
        if too_few:
            continue
        center = ms.cluster_centers_[k]
        my_members = x == k
        units = predict_with[my_members]
        times = units[:, -1]
        if times.size == 0:
            continue
        unnormalized = untransform(((0, 0, times.min()), (0, 0, times.max())))
        start = int(unnormalized[0, 2])
        end = int(unnormalized[1, 2])

        # x seconds before first death and x after last death
        before = args.t_padding * 8
        after = args.t_padding * 8
        rectangle = radius_to_rect(untransform(center), x_radius, y_radius,
                                   maxes, start - before, end + after)

        rects.append((center, rectangle))

    # Merge highly similar rectangles by averaging centers greedily
    # Only stop when there are no possible merges left
    i = 0
    while i < len(rects) - 1:
        length = len(rects)
        j = i + 1
        while j < len(rects):
            c1, rect = rects[i]
            xmin1, xmax1, ymin1, ymax1, tmin1, tmax1 = rect
            c2, rect = rects[j]
            xmin2, xmax2, ymin2, ymax2, tmin2, tmax2 = rect

            A1 = (xmax1 - xmin1) * (ymax1 - ymin1) * (tmax1 - tmin1)
            A2 = (xmax2 - xmin2) * (ymax2 - ymin2) * (tmax2 - tmin2)

            A_intersect = (
                max(0, min(xmax1, xmax2) - max(xmin1, xmin2)) *
                max(0, min(ymax1, ymax2) - max(ymin1, ymin2)) *
                max(0, min(tmax1, tmax2) - max(tmin1, tmin2))
            )

            if A_intersect / float(A1 + A2 - A_intersect) > args.merge_sim:
                tmin = min(tmin1, tmin2)
                tmax = max(tmax1, tmax2)
                c = (c1 + c2) / 2  # weight this by unit number if results are bad
                rect = radius_to_rect(c, x_radius, y_radius, maxes, tmin, tmax)
                rects[i] = (c, rect)
                del rects[j]
            else:
                j += 1
        if len(rects) == length:
            i += 1
        else:
            i = 0

    for item in rects:
        _, rectangle = item
        filtered_units = filter_rectangle(data, rectangle, maxes)
        team0 = filtered_units[:, 0] == 0
        if not any(team0) or all(team0):  # bad cluster
            continue

        t0 = filtered_units[team0]
        t0 = t0[t0[:, 1].argsort()]
        unique = np.diff(t0[:, 1], axis=0) > 0
        unique = np.append(unique, True)
        u0 = t0[unique]
        bc0 = np.bincount(u0[:, 2])

        t1 = filtered_units[np.logical_not(team0)]
        t1 = t1[t1[:, 1].argsort()]
        unique = np.diff(t1[:, 1], axis=0) > 0
        unique = np.append(unique, True)
        u1 = t1[unique]
        bc1 = np.bincount(u1[:, 2])

        out.append(",".join(str(x) for x in rectangle))
        out.append(",".join(
            "{}: {}".format(id2unit[id], c)
            for id, c in zip(np.nonzero(bc0)[0], bc0[bc0 > 0]) if id in id2unit))
        out.append(",".join(
            "{}: {}".format(id2unit[id], c)
            for id, c in zip(np.nonzero(bc1)[0], bc1[bc1 > 0]) if id in id2unit))

    with open(outfn, 'w') as f:
        f.write("\n".join(out))

    return rects


if __name__ == "__main__":
    files = glob(args.input)
    os.makedirs(path.abspath(args.output), exist_ok=True)
    # [cluster((fn, path.join(args.output, path.basename(fn)))) for fn in files]
    p = multiprocessing.Pool()
    p.map(cluster, [(fn, path.join(args.output, path.basename(fn))) for fn in files])
