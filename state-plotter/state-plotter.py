#!/usr/bin/python3.6

# ------------------------------------------------------------------------------
# Copyright (c) 2019, Battelle Memorial Institute All rights reserved.
# Battelle Memorial Institute (hereinafter Battelle) hereby grants permission to any person or entity
# lawfully obtaining a copy of this software and associated documentation files (hereinafter the
# Software) to redistribute and use the Software in source and binary forms, with or without modification.
# Such person or entity may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and may permit others to do so, subject to the following conditions:
# Redistributions of source code must retain the above copyright notice, this list of conditions and the
# following disclaimers.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
# the following disclaimer in the documentation and/or other materials provided with the distribution.
# Other than as used herein, neither the name Battelle Memorial Institute or Battelle may be used in any
# form whatsoever without the express written consent of Battelle.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# BATTELLE OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# General disclaimer for use with OSS licenses
#
# This material was prepared as an account of work sponsored by an agency of the United States Government.
# Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any
# of their employees, nor any jurisdiction or organization that has cooperated in the development of these
# materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for
# the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process
# disclosed, or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer,
# or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United
# States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by BATTELLE for the
# UNITED STATES DEPARTMENT OF ENERGY under Contract DE-AC05-76RL01830
# ------------------------------------------------------------------------------
"""
Created on Oct 1, 2019

@author: Gary D. Black
"""

__version__ = '0.0.1'

import sys
import json
import math
import pprint

# gridappsd-python module
from gridappsd import GridAPPSD

# requires matplotlib 3.1.0+ for vertical sliders
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.widgets import Button
from matplotlib.widgets import CheckButtons
from matplotlib.ticker import MaxNLocator
from matplotlib import backend_bases

cnPairDict = {}
nodePhasePairDict = {}
tsData = []
tsDataPaused = []
vDataDict = {}
vDataDictPaused = {}
vDiffDataDict = {}
vDiffDataDictPaused = {}
vLinesDict = {}
angDataDict = {}
angDataDictPaused = {}
angDiffDataDict = {}
angDiffDataDictPaused = {}
angLinesDict = {}
simDataDict = {}
busToSimMRIDDict = {}
SEPairToSimMRIDDict = {}
tsInit = 0
pausedFlag = False
showFlag = False
firstPassFlag = True
plotNumber = 0


def mapBusToSimMRID():
    # TODO Hardwire busToSimMRIDDict entries until I can code the real query
    sim_req = sys.argv[2]
    # ieee13nodecktassets
    if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in sim_req:
        busToSimFile = 'busToSim.13.csv'
    # ieee123
    elif '_C1C3E687-6FFD-C753-582B-632A27E28507' in sim_req:
        busToSimFile = 'busToSim.123.csv'
    # test9500new
    elif '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44' in sim_req:
        busToSimFile = 'busToSim.9500.csv'

    with open('../' + busToSimFile) as csvfp:
        for line in csvfp:
            # strip whitespace including trailing newline
            line = ''.join(line.split())
            bus, simmrid = line.split(',')
            busToSimMRIDDict[bus] = simmrid


def mapSEPairToSimMRID():
    for busname, simmrid in busToSimMRIDDict.items():
        bus, phase = busname.split('.')
        if bus in cnPairDict:
            semrid = cnPairDict[bus]
            if phase == '1':
                SEPairToSimMRIDDict[semrid+',A'] = simmrid
            elif phase == '2':
                SEPairToSimMRIDDict[semrid+',B'] = simmrid
            elif phase == '3':
                SEPairToSimMRIDDict[semrid+',C'] = simmrid
    pprint.pprint(SEPairToSimMRIDDict)


def measurementConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']
    print(sys.argv[0] + ': measurement timestamp: ' + str(ts), flush=True)

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    sepairCount = 0
    global tsZoomSldr, tsInit, pausedFlag, firstPassFlag

    # update the timestamp zoom slider upper limit and default value
    if firstPassFlag:
        sepairCount = len(estVolt)

        # scale based on cube root of number of node/phase pairs
        # 18 is just a magic number that seems to produce reasonable values
        # for the 3 models used as test cases--20 is a bit too big, 15 too small
        upper = 18 * (sepairCount**(1./3))
        # round to the nearest 10 to keep the slider from looking odd
        upper = int(round(upper/10.0)) * 10;
        # sanity check just in case
        upper = max(upper, 60)
        # // is integer floor division operator
        default = upper // 2;
        #print('setting slider upper limit: ' + str(upper) + ', default value: ' + str(default) + ', matchCount: ' + str(matchCount), flush=True)
        tsZoomSldr.valmin = 1
        tsZoomSldr.valmax = upper
        tsZoomSldr.val = default
        tsZoomSldr.ax.set_xlim(tsZoomSldr.valmin, tsZoomSldr.valmax)
        tsZoomSldr.set_val(tsZoomSldr.val)

        # clear flag that sets zoom slider values
        firstPassFlag = False

    # simulation data processing setup
    # to account for state estimator work queue draining design, iterate over
    # simDataDict and toss all measurements until we reach the current timestamp
    for tskey in list(simDataDict):
        if tskey < ts:
            del simDataDict[tskey]
        else:
            break

    # verify the first key is the current timestamp after tossing the ones
    # before the current timestamp
    if next(iter(simDataDict)) == ts:
        simDataTS = simDataDict[ts]
        # now that we have a copy, won't need this timestamp any longer either
        del simDataDict[ts]
    else:
        simDataTS = None
    # end simulation data processing setup

    for item in estVolt:
        sepair = item['ConnectivityNode'] + ',' + item['phase']

        if sepair in nodePhasePairDict:
            matchCount += 1
            vmag = item['v']
            vangle = item['angle']

            #print(sys.argv[0] + ': node,phase pair: ' + sepair, flush=True)
            #print(sys.argv[0] + ': timestamp: ' + str(ts), flush=True)
            #print(sys.argv[0] + ': v: ' + str(vmag), flush=True)
            #print(sys.argv[0] + ': angle: ' + str(vangle) + '\n', flush=True)

            # a little trick to add to the timestamp list for every measurement,
            # not for every node/phase pair match, but only add when a match
            # is confirmed for one of the node/phase pairs
            if matchCount == 1:
                if pausedFlag:
                    if len(tsData) > 0:
                        tsDataPaused.append(ts - tsInit)
                    else:
                        tsInit = ts
                        tsDataPaused.append(0)
                else:
                    if len(tsData) > 0:
                        tsData.append(ts - tsInit)
                    else:
                        tsInit = ts
                        tsData.append(0)

            if pausedFlag:
                vDataDictPaused[sepair].append(vmag)
                angDataDictPaused[sepair].append(vangle)
                if simDataTS is not None:
                    if sepair in SEPairToSimMRIDDict:
                        simmrid = SEPairToSimMRIDDict[sepair]
                        if simmrid in simDataTS:
                            simmeas = simDataTS[simmrid]
                            if 'magnitude' in simmeas:
                                simvmag = simmeas['magnitude']
                                if simvmag != 0.0:
                                    vmagdiff = 100.0*abs(vmag - simvmag)/simvmag
                                else:
                                    vmagdiff = 0.0
                                vDiffDataDictPaused[sepair].append(vmagdiff)
                                print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', paused semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
                                simvangle = simmeas['angle']
                                if simvangle != 0.0:
                                    vanglediff = 100.0*abs((abs(vangle)-abs(simvangle))/simvangle)
                                else:
                                    vanglediff = 0.0
                                angDiffDataDictPaused[sepair].append(vanglediff)
                                print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', paused seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', % diff: ' + str(vanglediff), flush=True)
            else:
                vDataDict[sepair].append(vmag)
                angDataDict[sepair].append(vangle)
                if simDataTS is not None:
                    if sepair in SEPairToSimMRIDDict:
                        simmrid = SEPairToSimMRIDDict[sepair]
                        if simmrid in simDataTS:
                            simmeas = simDataTS[simmrid]
                            if 'magnitude' in simmeas:
                                simvmag = simmeas['magnitude']
                                if simvmag != 0.0:
                                    vmagdiff = 100.0*abs(vmag - simvmag)/simvmag
                                else:
                                    vmagdiff = 0.0
                                vDiffDataDict[sepair].append(vmagdiff)
                                print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
                                simvangle = simmeas['angle']
                                if simvangle != 0.0:
                                    vanglediff = 100.0*abs((abs(vangle)-abs(simvangle))/simvangle)
                                else:
                                    vanglediff = 0.0
                                angDiffDataDict[sepair].append(vanglediff)
                                print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', % diff: ' + str(vanglediff), flush=True)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if matchCount == len(nodePhasePairDict):
                break

    # update plot with the new data
    plotData(None)


def measurementNoConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']
    print(sys.argv[0] + ': measurement timestamp: ' + str(ts), flush=True)

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    global tsZoomSldr, tsInit, pausedFlag, firstPassFlag, plotNumber

    # update the timestamp zoom slider upper limit and default value
    if firstPassFlag:
        sepairCount = len(estVolt)

        # scale based on cube root of number of node/phase pairs
        # 18 is just a magic number that seems to produce reasonable values
        # for the 3 models used as test cases--20 is a bit too big, 15 too small
        upper = 18 * (sepairCount**(1./3))
        # round to the nearest 10 to keep the slider from looking odd
        upper = int(round(upper/10.0)) * 10;
        # sanity check just in case
        upper = max(upper, 60)
        # // is integer floor division operator
        default = upper // 2;
        #print('setting slider upper limit: ' + str(upper) + ', default value: ' + str(default) + ', matchCount: ' + str(matchCount), flush=True)
        tsZoomSldr.valmin = 1
        tsZoomSldr.valmax = upper
        tsZoomSldr.val = default
        tsZoomSldr.ax.set_xlim(tsZoomSldr.valmin, tsZoomSldr.valmax)
        tsZoomSldr.set_val(tsZoomSldr.val)

    # simulation data processing setup
    # to account for state estimator work queue draining design, iterate over
    # simDataDict and toss all measurements until we reach the current timestamp
    for tskey in list(simDataDict):
        if tskey < ts:
            del simDataDict[tskey]
        else:
            break

    # verify the first key is the current timestamp after tossing the ones
    # before the current timestamp
    if next(iter(simDataDict)) == ts:
        simDataTS = simDataDict[ts]
        # now that we have a copy, won't need this timestamp any longer either
        del simDataDict[ts]
    else:
        simDataTS = None
    # end simulation data processing setup

    for item in estVolt:
        sepair = item['ConnectivityNode'] + ',' + item['phase']
        vmag = item['v']
        vangle = item['angle']

        print(sys.argv[0] + ': node,phase pair: ' + sepair + ', matchCount: ' + str(matchCount), flush=True)
        #print(sys.argv[0] + ': timestamp: ' + str(ts), flush=True)
        #print(sys.argv[0] + ': vmag: ' + str(vmag), flush=True)
        #print(sys.argv[0] + ': vangle: ' + str(vangle) + '\n', flush=True)

        matchCount += 1

        if firstPassFlag:
            vDataDict[sepair] = []
            vDataDictPaused[sepair] = []
            vDiffDataDict[sepair] = []
            vDiffDataDictPaused[sepair] = []
            angDataDict[sepair] = []
            angDataDictPaused[sepair] = []
            angDiffDataDict[sepair] = []
            angDiffDataDictPaused[sepair] = []

            # create a lines dictionary entry per node/phase pair for each plot
            vLinesDict[sepair], = vAx.plot([], [], label=sepair)
            angLinesDict[sepair], = angAx.plot([], [], label=sepair)

        # a little trick to add to the timestamp list for every measurement,
        # not for every node/phase pair
        if matchCount == 1:
            if pausedFlag:
                if len(tsData) > 0:
                    tsDataPaused.append(ts - tsInit)
                else:
                    tsInit = ts
                    tsDataPaused.append(0)
            else:
                if len(tsData) > 0:
                    tsData.append(ts - tsInit)
                else:
                    tsInit = ts
                    tsData.append(0)

        if pausedFlag:
            vDataDictPaused[sepair].append(vmag)
            angDataDictPaused[sepair].append(vangle)
            if simDataTS is not None:
                if sepair in SEPairToSimMRIDDict:
                    simmrid = SEPairToSimMRIDDict[sepair]
                    if simmrid in simDataTS:
                        simmeas = simDataTS[simmrid]
                        if 'magnitude' in simmeas:
                            simvmag = simmeas['magnitude']
                            if simvmag != 0.0:
                                vmagdiff = 100.0*abs(vmag - simvmag)/simvmag
                            else:
                                vmagdiff = 0.0
                            vDiffDataDictPaused[sepair].append(vmagdiff)
                            print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', paused semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
                            simvangle = simmeas['angle']
                            if simvangle != 0.0:
                                vanglediff = 100.0*abs((abs(vangle)-abs(simvangle))/simvangle)
                            else:
                                vanglediff = 0.0
                            angDiffDataDictPaused[sepair].append(vanglediff)
                            print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', paused seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', % diff: ' + str(vanglediff), flush=True)

        else:
            vDataDict[sepair].append(vmag)
            angDataDict[sepair].append(vangle)
            if simDataTS is not None:
                if sepair in SEPairToSimMRIDDict:
                    simmrid = SEPairToSimMRIDDict[sepair]
                    if simmrid in simDataTS:
                        simmeas = simDataTS[simmrid]
                        if 'magnitude' in simmeas:
                            simvmag = simmeas['magnitude']
                            if simvmag != 0.0:
                                vmagdiff = 100.0*abs(vmag - simvmag)/simvmag
                            else:
                                vmagdiff = 0.0;
                            vDiffDataDict[sepair].append(vmagdiff)
                            print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
                            simvangle = simmeas['angle']
                            if simvangle != 0.0:
                                vanglediff = 100.0*abs((abs(vangle)-abs(simvangle))/simvangle)
                            else:
                                vanglediff = 0.0
                            angDiffDataDict[sepair].append(vanglediff)
                            print(sys.argv[0] + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', % diff: ' + str(vanglediff), flush=True)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if plotNumber>0 and matchCount==plotNumber:
            break

    # only do the dictionary initializtion code on the first call
    firstPassFlag = False

    # update plot with the new data
    plotData(None)


def simulationOutputCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    # some debug printing
    print(sys.argv[0] + ': simulation output message timestamp: ' + str(ts), flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    simDataDict[ts] = msgdict['measurements']


def sensorDefCallback(header, message):
    print('START sensorDefCallback!!!!', flush=True)
    for feeders in message['data']['feeders']:
        for meas in feeders['measurements']:
            if meas['measurementType'] == 'PNV':
                busname = meas['ConnectivityNode']
                phase = meas['phases']
                if phase == 'A':
                    busname += '.1'
                elif phase == 'B':
                    busname += '.2'
                elif phase == 'C':
                    busname += '.3'
                elif phase == 's1':
                    busname += '.1'
                elif phase == 's2':
                    busname += '.2'

                busToSimMRIDDict[busname] = meas['mRID']

    pprint.pprint(busToSimMRIDDict)

    mapSEPairToSimMRID()
    print('DONE sensorDefCallback!!!!', flush=True)


def plotData(event):
    # avoid error by making sure there is data to plot
    if len(tsData)==0:
        return

    if showFlag:
        vAx.set_xlim((0, int(tsData[-1])))

        vYmax = sys.float_info.min
        vYmin = sys.float_info.max
        for pair in vDataDict:
            vLinesDict[pair].set_xdata(tsData)
            vLinesDict[pair].set_ydata(vDataDict[pair])
            vYmin = min(vYmin, min(vDataDict[pair]))
            vYmax = max(vYmax, max(vDataDict[pair]))

        angYmax = sys.float_info.min
        angYmin = sys.float_info.max
        for pair in angDataDict:
            angLinesDict[pair].set_xdata(tsData)
            angLinesDict[pair].set_ydata(angDataDict[pair])
            angYmin = min(angYmin, min(angDataDict[pair]))
            angYmax = max(angYmax, max(angDataDict[pair]))
    else:
        tsZoom = int(tsZoomSldr.val)
        time = int(tsPanSldr.val)
        if time == 100:
            # this fills data from the right
            xmax = tsData[-1]
            xmin = xmax - tsZoom

            # uncomment this code if filling from the left is preferred
            #if xmin < 0:
            #    xmin = 0
            #    xmax = tsZoom
        elif time == 0:
            xmin = 0
            xmax = tsZoom
        else:
            mid = int(tsData[-1]*time/100.0)
            xmin = int(mid - tsZoom/2.0)
            xmax = xmin + tsZoom
            # this fills data from the right
            if xmax > tsData[-1]:
                xmax = tsData[-1]
                xmin = xmax - tsZoom
            elif xmin < 0:
                xmin = 0
                xmax = tsZoom
            # if filling from the left is preferred uncomment the lines
            # below and comment out the block if/elif block above
            #if xmin < 0:
            #    xmax = tsData[-1]
            #    xmin = xmax - tsZoom
            #elif xmax > tsData[-1]:
            #    xmin = 0
            #    xmax = tsZoom

        vAx.set_xlim(xmin, xmax)
        print(sys.argv[0] + ': xmin: ' + str(xmin), flush=True)
        print(sys.argv[0] + ': xmax: ' + str(xmax), flush=True)

        startpt = 0
        if xmin > 0:
            # don't assume 3 timesteps between points, calculate startpt instead
            #startpt = int(xmin/3.0)
            for ix in range(len(tsData)):
                #print(sys.argv[0] + ': startpt ix: ' + str(ix) + ', tsData: ' + str(tsData[ix]), flush=True)
                if tsData[ix] >= xmin:
                    # if it's feasible, set starting point to 1 before the
                    # calculated point so there is no data gap at the left edge
                    if ix > 1:
                        startpt = ix - 1
                    #print(sys.argv[0] + ': startpt break ix: ' + str(ix) + ', tsData: ' + str(tsData[ix]), flush=True)
                    break

        # don't assume 3 timesteps between points, calculate endpt instead
        #endpt = int(xmax/3.0) + 1
        endpt = 0
        if xmax > 0:
            endpt = len(tsData)-1
            for ix in range(endpt,-1,-1):
                #print(sys.argv[0] + ': endpt ix: ' + str(ix) + ', tsData: ' + str(tsData[ix]), flush=True)
                if tsData[ix] <= xmax:
                    # if it's feasible, set ending point to 1 after the
                    # calculated point so there is no data gap at the right edge
                    if ix < endpt:
                        endpt = ix + 1
                    #print(sys.argv[0] + ': endpt break ix: ' + str(ix) + ', tsData: ' + str(tsData[ix]), flush=True)
                    break

        # always add 1 to endpt because array slice uses -1 for upper bound
        endpt += 1

        print(sys.argv[0] + ': startpt: ' + str(startpt), flush=True)
        print(sys.argv[0] + ': endpt: ' + str(endpt) + '\n', flush=True)

        vYmax = sys.float_info.min
        vYmin = sys.float_info.max
        for pair in vDataDict:
            vLinesDict[pair].set_xdata(tsData[startpt:endpt])
            vLinesDict[pair].set_ydata(vDataDict[pair][startpt:endpt])
            vYmin = min(vYmin, min(vDataDict[pair][startpt:endpt]))
            vYmax = max(vYmax, max(vDataDict[pair][startpt:endpt]))

        angYmax = sys.float_info.min
        angYmin = sys.float_info.max
        for pair in angDataDict:
            angLinesDict[pair].set_xdata(tsData[startpt:endpt])
            angLinesDict[pair].set_ydata(angDataDict[pair][startpt:endpt])
            angYmin = min(angYmin, min(angDataDict[pair][startpt:endpt]))
            angYmax = max(angYmax, max(angDataDict[pair][startpt:endpt]))

    # voltage plot y-axis zoom and pan calculation
    vZoom = int(vZoomSldr.val)
    if vZoom == 100:
        vHeight = vYmax - vYmin
    else:
        vHeight = (vYmax-vYmin)*vZoom/100.0

    vPan = int(vPanSldr.val)
    vMid = vYmin + (vYmax-vYmin)*vPan/100.0

    newvYmin = vMid - vHeight/2.0
    newvYmax = newvYmin + vHeight
    #print(sys.argv[0] + ': calculated newvYmin: ' + str(newvYmin), flush=True)
    #print(sys.argv[0] + ': calculated newvYmax: ' + str(newvYmax), flush=True)

    if newvYmin < vYmin:
        newvYmin = vYmin
        newvYmax = newvYmin + vHeight
    elif newvYmax > vYmax:
        newvYmax = vYmax
        newvYmin = newvYmax - vHeight
    #print(sys.argv[0] + ': final newvYmin: ' + str(newvYmin), flush=True)
    #print(sys.argv[0] + ': final newvYmax: ' + str(newvYmax) + '\n', flush=True)

    # override auto-scaling with the calculated y-axis limits
    # apply a fixed margin to the axis limits
    vMargin = vHeight*0.03
    vAx.set_ylim((newvYmin-vMargin, newvYmax+vMargin))

    # angle plot y-axis zoom and pan calculation
    angZoom = int(angZoomSldr.val)
    if angZoom == 100:
        angHeight = angYmax - angYmin
    else:
        angHeight = (angYmax-angYmin)*angZoom/100.0

    angPan = int(angPanSldr.val)
    angMid = angYmin + (angYmax-angYmin)*angPan/100.0

    newangYmin = angMid - angHeight/2.0
    newangYmax = newangYmin + angHeight
    #print(sys.argv[0] + ': calculated newangYmin: ' + str(newangYmin), flush=True)
    #print(sys.argv[0] + ': calculated newangYmax: ' + str(newangYmax), flush=True)

    if newangYmin < angYmin:
        newangYmin = angYmin
        newangYmax = newangYmin + angHeight
    elif newangYmax > angYmax:
        newangYmax = angYmax
        newangYmin = newangYmax - angHeight
    #print(sys.argv[0] + ': final newangYmin: ' + str(newangYmin), flush=True)
    #print(sys.argv[0] + ': final newangYmax: ' + str(newangYmax) + '\n', flush=True)

    # override auto-scaling with the calculated y-axis limits
    # apply a fixed margin to the axis limits
    angMargin = angHeight*0.03
    angAx.set_ylim((newangYmin-angMargin, newangYmax+angMargin))

    # flush all the plot changes
    plt.draw()


def pauseCallback(event):
    global pausedFlag
    # toggle whether plot is paused
    pausedFlag = not pausedFlag

    # update the button icon
    pauseAx.images[0].set_data(playIcon if pausedFlag else pauseIcon)
    plt.draw()

    if not pausedFlag:
        # add all the data that came in since the pause button was hit
        tsData.extend(tsDataPaused)
        # clear the "paused" data so we build from scratch with the next pause
        tsDataPaused.clear()
        for pair in nodePhasePairDict:
            vDataDict[pair].extend(vDataDictPaused[pair])
            angDataDict[pair].extend(angDataDictPaused[pair])
            vDataDictPaused[pair].clear()
            angDataDictPaused[pair].clear()

            vDiffDataDict[pair].extend(vDiffDataDictPaused[pair])
            angDiffDataDict[pair].extend(angDiffDataDictPaused[pair])
            vDiffDataDictPaused[pair].clear()
            angDiffDataDictPaused[pair].clear()

    plotData(None)


def showCallback(event):
    global showFlag
    # toggle whether to show all timestamps
    showFlag = not showFlag

    # update the button icon
    tsShowAx.images[0].set_data(checkedIcon if showFlag else uncheckedIcon)
    plt.draw()

    plotData(None)


def queryConnectivityPairs():
    # extract the model ID from JSON argument
    sim_req = sys.argv[2]
    modelDict = json.loads(sim_req)
    model_mrid = modelDict['power_system_config']['Line_name']

    connectivity_names_query = \
            'PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> ' + \
            'PREFIX c:  <http://iec.ch/TC57/CIM100#> ' + \
            'SELECT ?cnid ?cnname WHERE { ' + \
              '?term c:Terminal.ConnectivityNode ?cn. ' + \
              '?cn c:IdentifiedObject.mRID ?cnid. ' + \
              '?cn c:IdentifiedObject.name ?cnname. ' + \
              'VALUES ?fdrid {"' + model_mrid + '"}' + \
              '?term c:Terminal.ConductingEquipment ?ce. ' + \
              '?ce c:Equipment.EquipmentContainer ?fdr. ' + \
              '?fdr c:IdentifiedObject.mRID ?fdrid. ' + \
            '}' + \
            'GROUP BY ?cnid ?cnname ' + \
            'ORDER by ?cnid'

    connectivity_names_request = {
            "requestType": "QUERY",
            "resultFormat": "JSON",
            "queryString": connectivity_names_query
            }

    connectivity_names_response = gapps.get_response('goss.gridappsd.process.request.data.powergridmodel', connectivity_names_request, timeout=600)

    results = connectivity_names_response['data']['results']['bindings']

    for node in results:
        cnname = node['cnname']['value']
        cnid = node['cnid']['value']
        cnPairDict[cnname.upper()] = cnid
    #pprint.pprint(cnPairDict)


def connectivityPairsToPlot():
    # match connectivity node,phase pairs with the config file for determining
    # what data to plot
    try:
        with open('../state-plotter-config.csv') as pairfile:
            for line in pairfile:
                # strip all whitespace from line whether at beginning, middle, or end
                line = ''.join(line.split())
                # skip empty and commented out lines
                if line=='' or line.startswith('#'):
                    next
                 
                bus, phase = line.split(',')
                bus = node.upper()
                if bus in cnPairDict:
                    nodePhasePairDict[cnPairDict[bus] + ',' + phase] = line
    except:
        print(sys.argv[0] + ': Node/Phase pair configuration file state-plotter-config.csv does not exist.\n', flush=True)
        exit()

    #print(sys.argv[0] + ': ' + str(nodePhasePairDict), flush=True)


def initPlot(configFlag, legendFlag):
    # plot attributes needed by plotData function
    global tsZoomSldr, tsPanSldr
    global vAx, vZoomSldr, vPanSldr
    global angAx, angZoomSldr, angPanSldr
    global pauseBtn, pauseAx, pauseIcon, playIcon
    global tsShowBtn, tsShowAx, checkedIcon, uncheckedIcon

    # customize navigation toolbar
    # get rid of the toolbar buttons completely
    plt.rcParams['toolbar'] = 'None'
    # pick and choose the toolbar buttons to display
    #backend_bases.NavigationToolbar2.toolitems = (
    #        ('Home', 'Reset to original view', 'home', 'home'),
    #        ('Back', 'Back to previous view', 'back', 'back'),
    #        ('Forward', 'Forward to next view', 'forward', 'forward'),
    #        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
    #        ('Zoom', 'Zoom to Rectangle', 'zoom_to_rect', 'zoom'),
    #        )

    figure = plt.figure(figsize=(10,6))
    figure.canvas.set_window_title('Simulation ID: ' + sim_id)

    vAx = figure.add_subplot(211)
    vAx.xaxis.set_major_locator(MaxNLocator(integer=True))
    vAx.grid()
    # shrink the margins, especially the top since we don't want a label
    plt.subplots_adjust(bottom=0.09, left=0.08, right=0.96, top=0.98, hspace=0.1)
    plt.ylabel('Voltage Magnitude (V)')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(vAx.get_xticklabels(), visible=False)

    angAx = figure.add_subplot(212, sharex=vAx)
    angAx.grid()
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage Angle (deg.)')

    # pause/play button
    pauseAx = plt.axes([0.0, 0.01, 0.04, 0.04])
    pauseIcon = plt.imread('icons/pausebtn.png')
    playIcon = plt.imread('icons/playbtn.png')
    pauseBtn = Button(pauseAx, '', image=pauseIcon, color='1.0')
    pauseBtn.on_clicked(pauseCallback)

    # timestamp slice zoom slider
    tsZoomAx = plt.axes([0.22, 0.01, 0.1, 0.03])
    # note this slider has the label for the show all button as well as the
    # slider that's because the show all button uses a checkbox image and you
    # can't use both an image and a label with a button so this is a clever way
    # to get that behavior since matplotlib doesn't have a simple label widget
    tsZoomSldr = Slider(tsZoomAx, 'show all           zoom', 0, 1, valfmt='%d', valstep=1.0)
    tsZoomSldr.on_changed(plotData)

    # show all button that's embedded in the middle of the slider above
    tsShowAx = plt.axes([0.13, 0.01, 0.03, 0.03])
    uncheckedIcon = plt.imread('icons/uncheckedbtn.png')
    checkedIcon = plt.imread('icons/checkedbtn.png')
    tsShowBtn = Button(tsShowAx, '', image=uncheckedIcon, color='1.0')
    tsShowBtn.on_clicked(showCallback)

    # timestamp slice pan slider
    tsPanAx = plt.axes([0.83, 0.01, 0.1, 0.03])
    tsPanSldr = Slider(tsPanAx, 'pan', 0, 100, valinit=100, valfmt='%d', valstep=1.0)
    tsPanSldr.on_changed(plotData)

    # angle slice zoom and pan sliders
    angZoomAx = plt.axes([0.97, 0.33, 0.02, 0.15])
    angZoomSldr = Slider(angZoomAx, 'zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    angZoomSldr.on_changed(plotData)

    angPanAx = plt.axes([0.97, 0.11, 0.02, 0.15])
    angPanSldr = Slider(angPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    angPanSldr.on_changed(plotData)

    # voltage slice zoom and pan sliders
    vZoomAx = plt.axes([0.97, 0.80, 0.02, 0.15])
    vZoomSldr = Slider(vZoomAx, 'zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vZoomSldr.on_changed(plotData)

    vPanAx = plt.axes([0.97, 0.58, 0.02, 0.15])
    vPanSldr = Slider(vPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vPanSldr.on_changed(plotData)

    if configFlag:
        for pair in nodePhasePairDict:
            # create empty lists for the per pair data for each plot so we can
            # just do append calls when data to plot arrives
            vDataDict[pair] = []
            vDataDictPaused[pair] = []
            angDataDict[pair] = []
            angDataDictPaused[pair] = []
            vDiffDataDict[pair] = []
            vDiffDataDictPaused[pair] = []
            angDiffDataDict[pair] = []
            angDiffDataDictPaused[pair] = []
            # create a lines dictionary entry per node/phase pair for each plot
            vLinesDict[pair], = vAx.plot([], [], label=nodePhasePairDict[pair])
            angLinesDict[pair], = angAx.plot([], [], label=nodePhasePairDict[pair])

        # need to wait on creating legend after other initialization until the
        #lines are defined
        if legendFlag or len(nodePhasePairDict)<=10:
            cols = math.ceil(len(nodePhasePairDict)/12)
            vAx.legend(ncol=cols)


def _main():
    global gapps, sim_id, plotNumber

    if len(sys.argv) < 2:
        print('Usage: ' + sys.argv[0] + ' sim_id sim_req\n', flush=True)
        exit()

    sim_id = sys.argv[1]

    plotLegendFlag = False
    plotConfigFlag = True
    for arg in sys.argv:
        if arg == '-legend':
            legendFlag = True
        elif arg == '-all':
            plotConfigFlag = False
        elif arg[0]=='-' and arg[1:].isdigit():
            plotConfigFlag = False
            plotNumber = int(arg[1:])

    gapps = GridAPPSD()

    # GridAPPS-D query to get connectivity node,phase pairs
    queryConnectivityPairs()

    # subscribe to and then request CIM dictionary parameters for simulation
    # so the conducting equipment MRIDs to connectivity nodes can be extracted
    gapps.subscribe('/queue/goss.gridappsd.se.response.' + sim_id + '.cimdict',
                    sensorDefCallback)

    sensRequestText = '{"configurationType":"CIM Dictionary","parameters":{"simulation_id":"' + sim_id + '"}}';
    gapps.send('/topic/goss.gridappsd.process.request.config', sensRequestText)

    # create dictionaries to map between simulation and state-estimator output
    #mapBusToSimMRID()
    #mapSEPairToSimMRID()

    if plotConfigFlag:
        # Determine what to plot based on the state-plotter-config file
        connectivityPairsToPlot()

        # subscribe to state-estimator measurement output--with config file
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                        sim_id, measurementConfigCallback)
    else:
        # subscribe to state-estimator measurement output--without config file
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                        sim_id, measurementNoConfigCallback)

    # subscribe to simulation output for comparison with measurements
    gapps.subscribe('/topic/goss.gridappsd.simulation.output.' +
                    sim_id, simulationOutputCallback)

    # matplotlib setup
    initPlot(plotConfigFlag, plotLegendFlag)

    # interactive plot event loop allows both the ActiveMQ messages to be
    # received and plot GUI events
    plt.show()

    gapps.disconnect()


if __name__ == '__main__':
    _main()
