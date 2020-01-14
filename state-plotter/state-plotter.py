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

__version__ = '0.2.0'

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

# global dictionaries and lists
cnPairDict = {}
nodePhasePairDict = {}
tsDataList = []
tsDataPausedList = []
vmagDataDict = {}
vmagDataPausedDict = {}
vmagDiffDataDict = {}
vmagDiffDataPausedDict = {}
vmagLinesDict = {}
vmagDiffLinesDict = {}
vangDataDict = {}
vangDataPausedDict = {}
vangDiffDataDict = {}
vangDiffDataPausedDict = {}
vangLinesDict = {}
vangDiffLinesDict = {}
simDataDict = {}
busToSimMRIDDict = {}
SEPairToSimMRIDDict = {}

# global variables
gapps = None
appName = sys.argv[0]
simID = sys.argv[1]
simReq = sys.argv[2]
tsInit = 0
pausedFlag = False
showFlag = False
firstPassFlag = True
plotNumber = 0
playIcon = None
pauseIcon = None
checkedIcon = None
uncheckedIcon = None
tsZoomSldr = None
tsPanSldr = None
vmagAx = None
vmagZoomSldr = None
vmagPanSldr = None
vmagDiffAx = None
vmagDiffZoomSldr = None
vmagDiffPanSldr = None
vangAx = None
vangZoomSldr = None
vangPanSldr = None
vangDiffAx = None
vangDiffZoomSldr = None
vangDiffPanSldr = None
pauseBtn = None
pauseAx = None
tsShowBtn = None
tsShowAx = None


def queryBusToSimMRID():
    sensRequestText = '{"configurationType":"CIM Dictionary","parameters":{"simulation_id":"' + simID + '"}}';
    sensResponse = gapps.get_response('goss.gridappsd.process.request.config', sensRequestText, timeout=600)

    for feeders in sensResponse['data']['feeders']:
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

                busup = busname.upper()
                if busup in busToSimMRIDDict:
                    simList = busToSimMRIDDict[busup]
                    simList.append(meas['mRID'])
                    busToSimMRIDDict[busup] = simList
                else:
                    simList = [meas['mRID']]
                    busToSimMRIDDict[busup] = simList

    print(appName + ': start simulation bus to simmrid query results...', flush=True)
    pprint.pprint(busToSimMRIDDict)
    print(appName + ': end simulation bus to simmrid query results', flush=True)


def mapSEPairToSimMRID():
    seMatchCount = 0

    for busname, simList in busToSimMRIDDict.items():
        bus, phase = busname.split('.')
        if bus in cnPairDict:
            seMatchCount += 1
            semrid = cnPairDict[bus]
            if phase == '1':
                SEPairToSimMRIDDict[semrid+',A'] = simList
            elif phase == '2':
                SEPairToSimMRIDDict[semrid+',B'] = simList
            elif phase == '3':
                SEPairToSimMRIDDict[semrid+',C'] = simList
    print(appName + ': start state-estimator to simulation mrid mapping...', flush=True)
    pprint.pprint(SEPairToSimMRIDDict)
    print(appName + ': end state-estimator to simulation mrid mapping', flush=True)

    simMRIDCount = len(busToSimMRIDDict)
    print(appName + ': ' + str(seMatchCount) + ' state-estimator node,phase pair matches out of ' + str(simMRIDCount) + ' total simulation mrids', flush=True)


def printWithSim(ts, sepair, vmag, simvmag, vmagdiff, vangle, simvangle, vanglediff):
    print(appName + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % mag diff: ' + str(vmagdiff) + ', seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', diff: ' + str(vanglediff), flush=True)
    # 13-node
    if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in simReq:
        if vmagdiff < -2.0:
            print(appName + ': OUTLIER, 13-node, vmagdiff<-2.0%: ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        if vanglediff > 34.0:
            print(appName + ': OUTLIER, 13-node, vanglediff>34.0: ts: ' + str(ts) + ', sepair: ' + sepair + ', seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', diff: ' + str(vanglediff), flush=True)
    # 123-node
    elif '_C1C3E687-6FFD-C753-582B-632A27E28507' in simReq:
        if vmagdiff > 3.0:
            print(appName + ': OUTLIER, 123-node, vmagdiff>3.0%: ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        if vmagdiff < -2.0:
            print(appName + ': OUTLIER, 123-node, vmagdiff<-2.0%: ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', simmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        if vanglediff < -100.0:
            print(appName + ': OUTLIER, 123-node, vanglediff<-100.0: ts: ' + str(ts) + ', sepair: ' + sepair + ', seangle: ' + str(vangle) + ', simvangle: ' + str(simvangle) + ', diff: ' + str(vanglediff), flush=True)
    # 9500-node
    #elif '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44' in simReq:


def printWithoutSim(ts, sepair, vmag, vangle):
    print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', sepair: ' + sepair + ', semag: ' + str(vmag) + ', seangle: ' + str(vangle), flush=True)
    if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in simReq:
        if vmag > 4000:
            print(appName + ': OUTLIER, 13-node, vmag>4K: ts: ' + str(ts) + ', sepair: ' + sepair + ', semag > 4K: ' + str(vmag), flush=True)


def measurementConfigCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    sepairCount = len(estVolt)

    # update the timestamp zoom slider upper limit and default value
    if firstPassFlag:
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
    if simDataDict and next(iter(simDataDict)) == ts:
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

            #print(appName + ': node,phase pair: ' + sepair, flush=True)
            #print(appName + ': timestamp: ' + str(ts), flush=True)
            #print(appName + ': v: ' + str(vmag), flush=True)
            #print(appName + ': angle: ' + str(vangle) + '\n', flush=True)

            # a little trick to add to the timestamp list for every measurement,
            # not for every node/phase pair match, but only add when a match
            # is confirmed for one of the node/phase pairs
            if matchCount == 1:
                if pausedFlag:
                    if len(tsDataList) > 0:
                        tsDataPausedList.append(ts - tsInit)
                    else:
                        tsInit = ts
                        tsDataPausedList.append(0)
                else:
                    if len(tsDataList) > 0:
                        tsDataList.append(ts - tsInit)
                    else:
                        tsInit = ts
                        tsDataList.append(0)

            printFlag = False
            if pausedFlag:
                vmagDataPausedDict[sepair].append(vmag)
                vangDataPausedDict[sepair].append(vangle)
                if simDataTS is not None:
                    if sepair in SEPairToSimMRIDDict:
                        for simmrid in SEPairToSimMRIDDict[sepair]:
                            if simmrid in simDataTS:
                                simmeas = simDataTS[simmrid]
                                if 'magnitude' in simmeas:
                                    printFlag = True
                                    diffMatchCount += 1
                                    simvmag = simmeas['magnitude']
                                    if simvmag != 0.0:
                                        vmagdiff = 100.0*(vmag - simvmag)/simvmag
                                    else:
                                        vmagdiff = 0.0
                                    vmagDiffDataPausedDict[sepair].append(vmagdiff)
                                    simvangle = simmeas['angle']
                                    vanglediff = vangle - simvangle
                                    vangDiffDataPausedDict[sepair].append(vanglediff)
                                    printWithSim(ts, sepair, vmag, simvmag, vmagdiff, vangle, simvangle, vanglediff)
                                    break
                if not printFlag:
                    printWithoutSim(ts, sepair, vmag, vangle)

            else:
                vmagDataDict[sepair].append(vmag)
                vangDataDict[sepair].append(vangle)
                if simDataTS is not None:
                    if sepair in SEPairToSimMRIDDict:
                        for simmrid in SEPairToSimMRIDDict[sepair]:
                            if simmrid in simDataTS:
                                simmeas = simDataTS[simmrid]
                                if 'magnitude' in simmeas:
                                    printFlag = True
                                    diffMatchCount += 1
                                    simvmag = simmeas['magnitude']
                                    if simvmag != 0.0:
                                        vmagdiff = 100.0*(vmag - simvmag)/simvmag
                                    else:
                                        vmagdiff = 0.0
                                    vmagDiffDataDict[sepair].append(vmagdiff)
                                    simvangle = simmeas['angle']
                                    vanglediff = vangle - simvangle
                                    vangDiffDataDict[sepair].append(vanglediff)
                                    printWithSim(ts, sepair, vmag, simvmag, vmagdiff, vangle, simvangle, vanglediff)
                                    break
                if not printFlag:
                    printWithoutSim(ts, sepair, vmag, vangle)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if matchCount == len(nodePhasePairDict):
                break

    print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' configuration file node,phase pair matches, ' + str(diffMatchCount) + ' matches to simulation data', flush=True)

    # update plot with the new data
    plotData(None)


def measurementNoConfigCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    sepairCount = len(estVolt)

    # update the timestamp zoom slider upper limit and default value
    if firstPassFlag:
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
    if simDataDict and next(iter(simDataDict)) == ts:
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

        #print(appName + ': node,phase pair: ' + sepair + ', matchCount: ' + str(matchCount), flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': vmag: ' + str(vmag), flush=True)
        #print(appName + ': vangle: ' + str(vangle) + '\n', flush=True)

        matchCount += 1

        if firstPassFlag:
            vmagDataDict[sepair] = []
            vmagDataPausedDict[sepair] = []
            vmagDiffDataDict[sepair] = []
            vmagDiffDataPausedDict[sepair] = []
            vangDataDict[sepair] = []
            vangDataPausedDict[sepair] = []
            vangDiffDataDict[sepair] = []
            vangDiffDataPausedDict[sepair] = []

            # create a lines dictionary entry per node/phase pair for each plot
            vmagLinesDict[sepair], = vmagAx.plot([], [], label=sepair)
            vmagDiffLinesDict[sepair], = vmagDiffAx.plot([], [], label=sepair)
            vangLinesDict[sepair], = vangAx.plot([], [], label=sepair)
            vangDiffLinesDict[sepair], = vangDiffAx.plot([], [], label=sepair)

        # a little trick to add to the timestamp list for every measurement,
        # not for every node/phase pair
        if matchCount == 1:
            if pausedFlag:
                if len(tsDataList) > 0:
                    tsDataPausedList.append(ts - tsInit)
                else:
                    tsInit = ts
                    tsDataPausedList.append(0)
            else:
                if len(tsDataList) > 0:
                    tsDataList.append(ts - tsInit)
                else:
                    tsInit = ts
                    tsDataList.append(0)

        printFlag = False
        if pausedFlag:
            vmagDataPausedDict[sepair].append(vmag)
            vangDataPausedDict[sepair].append(vangle)
            if simDataTS is not None:
                if sepair in SEPairToSimMRIDDict:
                    for simmrid in SEPairToSimMRIDDict[sepair]:
                        if simmrid in simDataTS:
                            simmeas = simDataTS[simmrid]
                            if 'magnitude' in simmeas:
                                printFlag = True
                                diffMatchCount += 1
                                simvmag = simmeas['magnitude']
                                if simvmag != 0.0:
                                    vmagdiff = 100.0*(vmag - simvmag)/simvmag
                                else:
                                    vmagdiff = 0.0
                                vmagDiffDataPausedDict[sepair].append(vmagdiff)
                                simvangle = simmeas['angle']
                                vanglediff = vangle - simvangle
                                vangDiffDataPausedDict[sepair].append(vanglediff)
                                printWithSim(ts, sepair, vmag, simvmag, vmagdiff, vangle, simvangle, vanglediff)
                                break
            if not printFlag:
                printWithoutSim(ts, sepair, vmag, vangle)

        else:
            vmagDataDict[sepair].append(vmag)
            vangDataDict[sepair].append(vangle)
            if simDataTS is not None:
                if sepair in SEPairToSimMRIDDict:
                    for simmrid in SEPairToSimMRIDDict[sepair]:
                        if simmrid in simDataTS:
                            simmeas = simDataTS[simmrid]
                            if 'magnitude' in simmeas:
                                printFlag = True
                                diffMatchCount += 1
                                simvmag = simmeas['magnitude']
                                if simvmag != 0.0:
                                    vmagdiff = 100.0*(vmag - simvmag)/simvmag
                                else:
                                    vmagdiff = 0.0;
                                vmagDiffDataDict[sepair].append(vmagdiff)
                                simvangle = simmeas['angle']
                                vanglediff = vangle - simvangle
                                vangDiffDataDict[sepair].append(vanglediff)
                                printWithSim(ts, sepair, vmag, simvmag, vmagdiff, vangle, simvangle, vanglediff)
                                break
            if not printFlag:
                printWithoutSim(ts, sepair, vmag, vangle)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if plotNumber>0 and matchCount==plotNumber:
            break

    # only do the dictionary initializtion code on the first call
    firstPassFlag = False

    if plotNumber > 0:
        print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching first ' + str(plotNumber) + '), ' + str(diffMatchCount) + ' matches to simulation data', flush=True)
    else:
        print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching all), ' + str(diffMatchCount) + ' matches to simulation data', flush=True)

    # update plot with the new data
    plotData(None)


def simulationOutputCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    # some debug printing
    print(appName + ': simulation output message timestamp: ' + str(ts), flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    simDataDict[ts] = msgdict['measurements']


def yAxisLimits(yMin, yMax, zoomVal, panVal):
    # check for yMin > yMax, which indicates there was no data to drive the
    # min/max determination
    if yMin > yMax:
        print(appName + ': WARNING: y-axis minimum and maximum values were not set due to lack of data--defaulting to avoid Matplotlib error!\n', flush=True)
        yMin = 0.0
        yMax = 100.0

    if zoomVal == 100:
        height = yMax - yMin
    else:
        height = (yMax-yMin)*zoomVal/100.0

    middle = yMin + (yMax-yMin)*panVal/100.0

    newYmin = middle - height/2.0
    newYmax = newYmin + height
    #print(appName + ': calculated newYmin: ' + str(newYmin), flush=True)
    #print(appName + ': calculated newYmax: ' + str(newYmax), flush=True)

    if newYmin < yMin:
        newYmin = yMin
        newYmax = newYmin + height
    elif newYmax > yMax:
        newYmax = yMax
        newYmin = newYmax - height
    #print(appName + ': final newYmin: ' + str(newYmin), flush=True)
    #print(appName + ': final newYmax: ' + str(newYmax) + '\n', flush=True)

    # override auto-scaling with the calculated y-axis limits
    # apply a fixed margin to the axis limits
    margin = height*0.03
    return newYmin-margin, newYmax+margin


def plotData(event):
    # avoid error by making sure there is data to plot
    if len(tsDataList)==0:
        return

    vmagDiffDataFlag = False
    vangDiffDataFlag = False

    if showFlag:
        xupper = int(tsDataList[-1])
        if xupper > 0:
            vmagAx.set_xlim(0, xupper)

        vmagYmax = sys.float_info.min
        vmagYmin = sys.float_info.max
        for pair in vmagDataDict:
            vmagLinesDict[pair].set_xdata(tsDataList)
            vmagLinesDict[pair].set_ydata(vmagDataDict[pair])
            vmagYmin = min(vmagYmin, min(vmagDataDict[pair]))
            vmagYmax = max(vmagYmax, max(vmagDataDict[pair]))
        #print(appName + ': vmagYmin: ' + str(vmagYmin) + ', vmagYmax: ' + str(vmagYmax), flush=True)

        vmagDiffYmax = sys.float_info.min
        vmagDiffYmin = sys.float_info.max
        for pair in vmagDiffDataDict:
            if len(vmagDiffDataDict[pair]) > 0:
                vmagDiffDataFlag = True
                vmagDiffLinesDict[pair].set_xdata(tsDataList)
                vmagDiffLinesDict[pair].set_ydata(vmagDiffDataDict[pair])
                vmagDiffYmin = min(vmagDiffYmin, min(vmagDiffDataDict[pair]))
                vmagDiffYmax = max(vmagDiffYmax, max(vmagDiffDataDict[pair]))
        #print(appName + ': vmagDiffYmin: ' + str(vmagDiffYmin) + ', vmagDiffYmax: ' + str(vmagDiffYmax), flush=True)

        vangYmax = sys.float_info.min
        vangYmin = sys.float_info.max
        for pair in vangDataDict:
            vangLinesDict[pair].set_xdata(tsDataList)
            vangLinesDict[pair].set_ydata(vangDataDict[pair])
            vangYmin = min(vangYmin, min(vangDataDict[pair]))
            vangYmax = max(vangYmax, max(vangDataDict[pair]))
        #print(appName + ': vangYmin: ' + str(vangYmin) + ', vangYmax: ' + str(vangYmax), flush=True)

        vangDiffYmax = sys.float_info.min
        vangDiffYmin = sys.float_info.max
        for pair in vangDiffDataDict:
            if len(vangDiffDataDict[pair]) > 0:
                vangDiffDataFlag = True
                vangDiffLinesDict[pair].set_xdata(tsDataList)
                vangDiffLinesDict[pair].set_ydata(vangDiffDataDict[pair])
                vangDiffYmin = min(vangDiffYmin, min(vangDiffDataDict[pair]))
                vangDiffYmax = max(vangDiffYmax, max(vangDiffDataDict[pair]))
        #print(appName + ': vangDiffYmin: ' + str(vangDiffYmin) + ', vangDiffYmax: ' + str(vangDiffYmax), flush=True)

    else:
        tsZoom = int(tsZoomSldr.val)
        time = int(tsPanSldr.val)
        if time == 100:
            # this fills data from the right
            xmax = tsDataList[-1]
            xmin = xmax - tsZoom

            # uncomment this code if filling from the left is preferred
            #if xmin < 0:
            #    xmin = 0
            #    xmax = tsZoom
        elif time == 0:
            xmin = 0
            xmax = tsZoom
        else:
            mid = int(tsDataList[-1]*time/100.0)
            xmin = int(mid - tsZoom/2.0)
            xmax = xmin + tsZoom
            # this fills data from the right
            if xmax > tsDataList[-1]:
                xmax = tsDataList[-1]
                xmin = xmax - tsZoom
            elif xmin < 0:
                xmin = 0
                xmax = tsZoom
            # if filling from the left is preferred uncomment the lines
            # below and comment out the block if/elif block above
            #if xmin < 0:
            #    xmax = tsDataList[-1]
            #    xmin = xmax - tsZoom
            #elif xmax > tsDataList[-1]:
            #    xmin = 0
            #    xmax = tsZoom

        vmagAx.set_xlim(xmin, xmax)
        print(appName + ': xmin: ' + str(xmin), flush=True)
        print(appName + ': xmax: ' + str(xmax), flush=True)

        startpt = 0
        if xmin > 0:
            # don't assume 3 timesteps between points, calculate startpt instead
            #startpt = int(xmin/3.0)
            for ix in range(len(tsDataList)):
                #print(appName + ': startpt ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                if tsDataList[ix] >= xmin:
                    # if it's feasible, set starting point to 1 before the
                    # calculated point so there is no data gap at the left edge
                    if ix > 1:
                        startpt = ix - 1
                    #print(appName + ': startpt break ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                    break

        # don't assume 3 timesteps between points, calculate endpt instead
        #endpt = int(xmax/3.0) + 1
        endpt = 0
        if xmax > 0:
            endpt = len(tsDataList)-1
            for ix in range(endpt,-1,-1):
                #print(appName + ': endpt ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                if tsDataList[ix] <= xmax:
                    # if it's feasible, set ending point to 1 after the
                    # calculated point so there is no data gap at the right edge
                    if ix < endpt:
                        endpt = ix + 1
                    #print(appName + ': endpt break ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                    break

        # always add 1 to endpt because array slice uses -1 for upper bound
        endpt += 1

        print(appName + ': startpt: ' + str(startpt), flush=True)
        print(appName + ': endpt: ' + str(endpt) + '\n', flush=True)

        vmagYmax = sys.float_info.min
        vmagYmin = sys.float_info.max
        for pair in vmagDataDict:
            vmagLinesDict[pair].set_xdata(tsDataList[startpt:endpt])
            vmagLinesDict[pair].set_ydata(vmagDataDict[pair][startpt:endpt])
            vmagYmin = min(vmagYmin, min(vmagDataDict[pair][startpt:endpt]))
            vmagYmax = max(vmagYmax, max(vmagDataDict[pair][startpt:endpt]))
        #print(appName + ': vmagYmin: ' + str(vmagYmin) + ', vmagYmax: ' + str(vmagYmax), flush=True)

        vmagDiffYmax = sys.float_info.min
        vmagDiffYmin = sys.float_info.max
        for pair in vmagDiffDataDict:
            if len(vmagDiffDataDict[pair]) > 0:
                vmagDiffDataFlag = True
                vmagDiffLinesDict[pair].set_xdata(tsDataList[startpt:endpt])
                vmagDiffLinesDict[pair].set_ydata(vmagDiffDataDict[pair][startpt:endpt])
                vmagDiffYmin = min(vmagDiffYmin, min(vmagDiffDataDict[pair][startpt:endpt]))
                vmagDiffYmax = max(vmagDiffYmax, max(vmagDiffDataDict[pair][startpt:endpt]))
        #print(appName + ': vmagDiffYmin: ' + str(vmagDiffYmin) + ', vmagDiffYmax: ' + str(vmagDiffYmax), flush=True)

        vangYmax = sys.float_info.min
        vangYmin = sys.float_info.max
        for pair in vangDataDict:
            vangLinesDict[pair].set_xdata(tsDataList[startpt:endpt])
            vangLinesDict[pair].set_ydata(vangDataDict[pair][startpt:endpt])
            vangYmin = min(vangYmin, min(vangDataDict[pair][startpt:endpt]))
            vangYmax = max(vangYmax, max(vangDataDict[pair][startpt:endpt]))
        #print(appName + ': vangYmin: ' + str(vangYmin) + ', vangYmax: ' + str(vangYmax), flush=True)

        vangDiffYmax = sys.float_info.min
        vangDiffYmin = sys.float_info.max
        for pair in vangDiffDataDict:
            if len(vangDiffDataDict[pair]) > 0:
                vangDiffDataFlag = True
                vangDiffLinesDict[pair].set_xdata(tsDataList[startpt:endpt])
                vangDiffLinesDict[pair].set_ydata(vangDiffDataDict[pair][startpt:endpt])
                vangDiffYmin = min(vangDiffYmin, min(vangDiffDataDict[pair][startpt:endpt]))
                vangDiffYmax = max(vangDiffYmax, max(vangDiffDataDict[pair][startpt:endpt]))
        #print(appName + ': vangDiffYmin: ' + str(vangDiffYmin) + ', vangDiffYmax: ' + str(vangDiffYmax), flush=True)

    # voltage magnitude plot y-axis zoom and pan calculation
    newvmagYmin, newvmagYmax = yAxisLimits(vmagYmin, vmagYmax, vmagZoomSldr.val, vmagPanSldr.val)
    vmagAx.set_ylim(newvmagYmin, newvmagYmax)

    # voltage magnitude difference plot y-axis zoom and pan calculation
    if not vmagDiffDataFlag:
        print(appName + ': WARNING: no voltage magnitude difference data to plot!\n', flush=True)
    newvmagDiffYmin, newvmagDiffYmax = yAxisLimits(vmagDiffYmin, vmagDiffYmax, vmagDiffZoomSldr.val, vmagDiffPanSldr.val)
    vmagDiffAx.set_ylim(newvmagDiffYmin, newvmagDiffYmax)

    # voltage angle plot y-axis zoom and pan calculation
    newvangYmin, newvangYmax = yAxisLimits(vangYmin, vangYmax, vangZoomSldr.val, vangPanSldr.val)
    vangAx.set_ylim(newvangYmin, newvangYmax)

    # voltage angle difference plot y-axis zoom and pan calculation
    if not vangDiffDataFlag:
        print(appName + ': WARNING: no voltage angle difference data to plot!\n', flush=True)
    newvangDiffYmin, newvangDiffYmax = yAxisLimits(vangDiffYmin, vangDiffYmax, vangDiffZoomSldr.val, vangDiffPanSldr.val)
    vangDiffAx.set_ylim(newvangDiffYmin, newvangDiffYmax)

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
        tsDataList.extend(tsDataPausedList)
        # clear the "paused" data so we build from scratch with the next pause
        tsDataPausedList.clear()

        # now do the same extend/clear for all the magnitude and angle data
        for pair in vmagDataDict:
            vmagDataDict[pair].extend(vmagDataPausedDict[pair])
            vangDataDict[pair].extend(vangDataPausedDict[pair])
            vmagDataPausedDict[pair].clear()
            vangDataPausedDict[pair].clear()

            vmagDiffDataDict[pair].extend(vmagDiffDataPausedDict[pair])
            vangDiffDataDict[pair].extend(vangDiffDataPausedDict[pair])
            vmagDiffDataPausedDict[pair].clear()
            vangDiffDataPausedDict[pair].clear()

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
    modelDict = json.loads(simReq)
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
    print(appName + ': start state-estimator bus to semrid query results...', flush=True)
    pprint.pprint(cnPairDict)
    print(appName + ': end state-estimator bus to semrid query results', flush=True)


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
        print(appName + ': Node/Phase pair configuration file state-plotter-config.csv does not exist.\n', flush=True)
        exit()

    #print(appName + ': ' + str(nodePhasePairDict), flush=True)


def initPlot(configFlag, legendFlag):
    # plot attributes needed by plotData function
    global tsZoomSldr, tsPanSldr
    global vmagAx, vmagZoomSldr, vmagPanSldr
    global vmagDiffAx, vmagDiffZoomSldr, vmagDiffPanSldr
    global vangAx, vangZoomSldr, vangPanSldr
    global vangDiffAx, vangDiffZoomSldr, vangDiffPanSldr
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

    figure = plt.figure(figsize=(10,9))
    figure.canvas.set_window_title('Simulation ID: ' + simID)

    vmagAx = figure.add_subplot(411)
    vmagAx.xaxis.set_major_locator(MaxNLocator(integer=True))
    vmagAx.grid()
    # shrink the margins, especially the top since we don't want a label
    plt.subplots_adjust(bottom=0.09, left=0.08, right=0.96, top=0.98, hspace=0.1)
    plt.ylabel('Voltage Magnitude (V)')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(vmagAx.get_xticklabels(), visible=False)

    vmagDiffAx = figure.add_subplot(412, sharex=vmagAx)
    vmagDiffAx.grid()
    plt.ylabel('Voltage Magnitude % Diff.')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(vmagDiffAx.get_xticklabels(), visible=False)

    vangAx = figure.add_subplot(413, sharex=vmagAx)
    vangAx.grid()
    plt.ylabel('Voltage Angle (deg.)')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(vangAx.get_xticklabels(), visible=False)

    vangDiffAx = figure.add_subplot(414, sharex=vmagAx)
    vangDiffAx.grid()
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage Angle Diff.')

    # pause/play button
    pauseAx = plt.axes([0.01, 0.01, 0.03, 0.03])
    pauseIcon = plt.imread('icons/pausebtn.png')
    playIcon = plt.imread('icons/playbtn.png')
    pauseBtn = Button(pauseAx, '', image=pauseIcon, color='1.0')
    pauseBtn.on_clicked(pauseCallback)

    # timestamp slice zoom slider
    tsZoomAx = plt.axes([0.32, 0.01, 0.1, 0.02])
    # note this slider has the label for the show all button as well as the
    # slider that's because the show all button uses a checkbox image and you
    # can't use both an image and a label with a button so this is a clever way
    # to get that behavior since matplotlib doesn't have a simple label widget
    tsZoomSldr = Slider(tsZoomAx, 'show all              zoom', 0, 1, valfmt='%d', valstep=1.0)
    tsZoomSldr.on_changed(plotData)

    # show all button that's embedded in the middle of the slider above
    tsShowAx = plt.axes([0.14, 0.01, 0.02, 0.02])
    uncheckedIcon = plt.imread('icons/uncheckedbtn.png')
    checkedIcon = plt.imread('icons/checkedbtn.png')
    tsShowBtn = Button(tsShowAx, '', image=uncheckedIcon, color='1.0')
    tsShowBtn.on_clicked(showCallback)

    # timestamp slice pan slider
    tsPanAx = plt.axes([0.63, 0.01, 0.1, 0.02])
    tsPanSldr = Slider(tsPanAx, 'pan', 0, 100, valinit=100, valfmt='%d', valstep=1.0)
    tsPanSldr.on_changed(plotData)

    # voltage angle difference slice zoom and pan sliders
    vangDiffZoomAx = plt.axes([0.97, 0.21, 0.015, 0.07])
    vangDiffZoomSldr = Slider(vangDiffZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vangDiffZoomSldr.on_changed(plotData)

    vangDiffPanAx = plt.axes([0.97, 0.10, 0.015, 0.07])
    vangDiffPanSldr = Slider(vangDiffPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vangDiffPanSldr.on_changed(plotData)

    # voltage angle slice zoom and pan sliders
    vangZoomAx = plt.axes([0.97, 0.44, 0.015, 0.07])
    vangZoomSldr = Slider(vangZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vangZoomSldr.on_changed(plotData)

    vangPanAx = plt.axes([0.97, 0.33, 0.015, 0.07])
    vangPanSldr = Slider(vangPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vangPanSldr.on_changed(plotData)

    # voltage magnitude difference slice zoom and pan sliders
    vmagDiffZoomAx = plt.axes([0.97, 0.67, 0.015, 0.07])
    vmagDiffZoomSldr = Slider(vmagDiffZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vmagDiffZoomSldr.on_changed(plotData)

    vmagDiffPanAx = plt.axes([0.97, 0.56, 0.015, 0.07])
    vmagDiffPanSldr = Slider(vmagDiffPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vmagDiffPanSldr.on_changed(plotData)

    # voltage magnitude slice zoom and pan sliders
    vmagZoomAx = plt.axes([0.97, 0.90, 0.015, 0.07])
    vmagZoomSldr = Slider(vmagZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vmagZoomSldr.on_changed(plotData)

    vmagPanAx = plt.axes([0.97, 0.79, 0.015, 0.07])
    vmagPanSldr = Slider(vmagPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vmagPanSldr.on_changed(plotData)

    if configFlag:
        for pair in nodePhasePairDict:
            # create empty lists for the per pair data for each plot so we can
            # just do append calls when data to plot arrives
            vmagDataDict[pair] = []
            vmagDataPausedDict[pair] = []
            vangDataDict[pair] = []
            vangDataPausedDict[pair] = []
            vmagDiffDataDict[pair] = []
            vmagDiffDataPausedDict[pair] = []
            vangDiffDataDict[pair] = []
            vangDiffDataPausedDict[pair] = []
            # create a lines dictionary entry per node/phase pair for each plot
            vmagLinesDict[pair], = vmagAx.plot([], [], label=nodePhasePairDict[pair])
            vmagLinesDiffDict[pair], = vmagDiffAx.plot([], [], label=nodePhasePairDict[pair])
            vangLinesDict[pair], = vangAx.plot([], [], label=nodePhasePairDict[pair])
            vangDiffLinesDict[pair], = vangDiffAx.plot([], [], label=nodePhasePairDict[pair])

        # need to wait on creating legend after other initialization until the
        #lines are defined
        if legendFlag or len(nodePhasePairDict)<=10:
            cols = math.ceil(len(nodePhasePairDict)/12)
            vmagAx.legend(ncol=cols)


def _main():
    global gapps, plotNumber

    if len(sys.argv) < 2:
        print('Usage: ' + appName + ' simID simReq\n', flush=True)
        exit()

    plotConfigFlag = True
    plotLegendFlag = False
    for arg in sys.argv:
        if arg == '-legend':
            plotLegendFlag = True
        elif arg == '-all':
            plotConfigFlag = False
        elif arg[0]=='-' and arg[1:].isdigit():
            plotConfigFlag = False
            plotNumber = int(arg[1:])
    gapps = GridAPPSD()

    # query to get connectivity node,phase pairs
    queryConnectivityPairs()

    # query to get bus to sensor mrid mapping
    queryBusToSimMRID()

    # finally, create map between state-estimator and simulation output
    mapSEPairToSimMRID()

    # matplotlib setup done before receiving any messages that reference it
    initPlot(plotConfigFlag, plotLegendFlag)

    if plotConfigFlag:
        # Determine what to plot based on the state-plotter-config file
        connectivityPairsToPlot()

        # subscribe to state-estimator measurement output--with config file
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                        simID, measurementConfigCallback)
    else:
        # subscribe to state-estimator measurement output--without config file
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                        simID, measurementNoConfigCallback)

    # subscribe to simulation output for comparison with measurements
    gapps.subscribe('/topic/goss.gridappsd.simulation.output.' +
                    simID, simulationOutputCallback)

    # interactive plot event loop allows both the ActiveMQ messages to be
    # received and plot GUI events
    plt.show()

    gapps.disconnect()


if __name__ == '__main__':
    _main()
