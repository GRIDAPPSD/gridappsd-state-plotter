#!/usr/bin/env python3

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

__version__ = '0.3.0'

import sys
import json
import math
import pprint
import statistics

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
busToSEDict = {}
SEToBusDict = {}
plotPairDict = {}
busToSimDict = {}
SEToSimDict = {}
SEToVnomMagDict = {}
SEToVnomAngDict = {}
simAllDataDict = {}

tsDataList = []
tsDataPausedList = []
SEDataDict = {}
SEDataPausedDict = {}
simDataDict = {}
simDataPausedDict = {}
diffDataDict = {}
diffDataPausedDict = {}
SELinesDict = {}
simLinesDict = {}
diffLinesDict = {}
SELegendLineList = []
SELegendLabelList = []
simLegendLineList = []
simLegendLabelList = []
plotPhaseList = []

# global variables
gapps = None
appName = None
simID = None
simReq = None
tsInit = 0
plotMagFlag = True
plotCompFlag = True
plotStatsFlag = True
plotSimAllFlag = False
plotPausedFlag = False
plotShowAllFlag = False
firstPassFlag = True
firstPlotFlag = True
plotOverlayFlag = False
plotLegendFlag = False
plotMatchesFlag = False
printDataFlag = False
plotNumber = 0
plotTitle = None
playIcon = None
pauseIcon = None
checkedIcon = None
uncheckedIcon = None
uiTSZoomSldr = None
uiTSPanSldr = None
uiPauseAx = None
uiPauseBtn = None
uiShowBtn = None
uiShowAx = None
uiSEAx = None
uiSEZoomSldr = None
uiSEPanSldr = None
uiSimAx = None
uiSimZoomSldr = None
uiSimPanSldr = None
uiDiffAx = None
uiDiffZoomSldr = None
uiDiffPanSldr = None

#stdevBlue = 'DodgerBlue'
#minmaxBlue = 'PaleTurquoise'
stdevBlue = '#389dff'
minmaxBlue = '#9be6ff'

def queryBusToSim():
    sensRequestText = '{"configurationType":"CIM Dictionary","parameters":{"simulation_id":"' + simID + '"}}';
    sensResponse = gapps.get_response('goss.gridappsd.process.request.config', sensRequestText, timeout=1200)

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
                if busup in busToSimDict:
                    simList = busToSimDict[busup]
                    simList.append(meas['mRID'])
                    busToSimDict[busup] = simList
                else:
                    simList = [meas['mRID']]
                    busToSimDict[busup] = simList

    print(appName + ': start simulation bus to simmrid query results...', flush=True)
    pprint.pprint(busToSimDict)
    print(appName + ': end simulation bus to simmrid query results', flush=True)


def mapSEToSim():
    seMatchCount = 0

    for busname, simList in busToSimDict.items():
        bus, phase = busname.split('.')
        if bus in busToSEDict:
            seMatchCount += 1
            semrid = busToSEDict[bus]
            if phase == '1':
                SEToSimDict[semrid+',A'] = simList
            elif phase == '2':
                SEToSimDict[semrid+',B'] = simList
            elif phase == '3':
                SEToSimDict[semrid+',C'] = simList
    print(appName + ': start state-estimator to simulation mrid mapping...', flush=True)
    pprint.pprint(SEToSimDict)
    print(appName + ': end state-estimator to simulation mrid mapping', flush=True)

    print(appName + ': ' + str(seMatchCount) + ' state-estimator node,phase pair matches out of ' + str(len(busToSimDict)) + ' total simulation mrids', flush=True)


def mapSEToVnomMag(semrid, phase, magnitude):
    if phase == 1:
        SEToVnomMagDict[semrid+',A'] = magnitude
    elif phase == 2:
        SEToVnomMagDict[semrid+',B'] = magnitude
    elif phase == 3:
        SEToVnomMagDict[semrid+',C'] = magnitude


def mapSEToVnomAngle(semrid, phase, angle):
    if phase == 1:
        SEToVnomAngDict[semrid+',A'] = angle
    elif phase == 2:
        SEToVnomAngDict[semrid+',B'] = angle
    elif phase == 3:
        SEToVnomAngDict[semrid+',C'] = angle


def queryVnom():
    vnomRequestText = '{"configurationType":"Vnom Export","parameters":{"simulation_id":"' + simID + '"}}';
    vnomResponse = gapps.get_response('goss.gridappsd.process.request.config', vnomRequestText, timeout=1200)
    # use busToSEDict dictionary to map to sepair (node,phase)

    if plotMagFlag:
        for line in vnomResponse['data']['vnom']:
            vnom = line.split(',')
            bus = vnom[0].strip('"')
            if bus in busToSEDict:
                semrid = busToSEDict[bus]
                mapSEToVnomMag(semrid, int(vnom[2]), float(vnom[3]))
                mapSEToVnomMag(semrid, int(vnom[6]), float(vnom[7]))
                mapSEToVnomMag(semrid, int(vnom[10]), float(vnom[11]))

        print(appName + ': start state-estimator to vnom magnitude mapping...', flush=True)
        pprint.pprint(SEToVnomMagDict)
        print(appName + ': end state-estimator to vnom magnitude mapping', flush=True)

    else:
        for line in vnomResponse['data']['vnom']:
            vnom = line.split(',')
            bus = vnom[0].strip('"')
            if bus in busToSEDict:
                semrid = busToSEDict[bus]
                mapSEToVnomAngle(semrid, int(vnom[2]), float(vnom[4]))
                mapSEToVnomAngle(semrid, int(vnom[6]), float(vnom[8]))
                mapSEToVnomAngle(semrid, int(vnom[10]), float(vnom[12]))

        print(appName + ': start state-estimator to vnom angle mapping...', flush=True)
        pprint.pprint(SEToVnomAngDict)
        print(appName + ': end state-estimator to vnom angle mapping', flush=True)


def vmagPrintWithSim(ts, sepair, sevmag, simvmag, vmagdiff):
    if printDataFlag:
        print(appName + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag: ' + str(sevmag) + ', simvmag: ' + str(simvmag) + ', % mag diff: ' + str(vmagdiff), flush=True)
        # 13-node
        if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in simReq:
            if vmagdiff < -2.0:
                print(appName + ': OUTLIER, 13-node, vmagdiff<-2.0%: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag: ' + str(sevmag) + ', simvmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        # 123-node
        elif '_C1C3E687-6FFD-C753-582B-632A27E28507' in simReq:
            if vmagdiff > 3.0:
                print(appName + ': OUTLIER, 123-node, vmagdiff>3.0%: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag: ' + str(sevmag) + ', simvmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
            if vmagdiff < -2.5:
                print(appName + ': OUTLIER, 123-node, vmagdiff<-2.5%: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag: ' + str(sevmag) + ', simvmag: ' + str(simvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        # 9500-node
        #elif '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44' in simReq:


def vangPrintWithSim(ts, sepair, sevang, simvang, vangdiff):
    if printDataFlag:
        print(appName + ', ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevang: ' + str(sevang) + ', simvang: ' + str(simvang) + ', diff: ' + str(vangdiff), flush=True)
        # 13-node
        if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in simReq:
            if vangdiff > 34.0:
                print(appName + ': OUTLIER, 13-node, vangdiff>34.0: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevang: ' + str(sevang) + ', simvang: ' + str(simvang) + ', diff: ' + str(vangdiff), flush=True)
        # 123-node
        #elif '_C1C3E687-6FFD-C753-582B-632A27E28507' in simReq:
        #    if vangdiff < -10.0:
        #        print(appName + ': OUTLIER, 123-node, vangdiff<-100.0: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevang: ' + str(sevang) + ', simvang: ' + str(simvang) + ', diff: ' + str(vangdiff), flush=True)
        # 9500-node
        #elif '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44' in simReq:


def vmagPrintWithoutSim(ts, sepair, sevmag):
    if printDataFlag:
        print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag: ' + str(sevmag), flush=True)
        if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in simReq:
            if sevmag > 4000:
                print(appName + ': OUTLIER, 13-node, sevmag>4K: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag > 4K: ' + str(sevmag), flush=True)


def vangPrintWithoutSim(ts, sepair, sevang):
    if printDataFlag:
        print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevang: ' + str(sevang), flush=True)


def calcVNom(vval, sepair):
    if plotMagFlag:
        if plotCompFlag and sepair in SEToVnomMagDict:
            return vval / SEToVnomMagDict[sepair]
    else:
        if plotCompFlag and sepair in SEToVnomAngDict:
            vval -= SEToVnomAngDict[sepair]
            # -165 <= vval <= 195.0
            while vval > 195.0:
                vval -= 360.0
            while vval < -165.0:
                vval += 360.0

    return vval


def estimateConfigCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    # to account for state estimator work queue draining design, iterate over
    # simAllDataDict and toss all measurements until we reach the current
    # timestamp since they won't be referenced again and will just drain memory
    simDataTS = None
    for tskey in list(simAllDataDict):
        if tskey < ts:
            del simAllDataDict[tskey]
        elif tskey == ts:
            simDataTS = simAllDataDict[tskey]
            break
        else:
            break

    if not simDataTS:
        print(appName + ': NOTE: No simulation measurement for timestamp: ' + str(ts) + ', disregarding estimate', flush=True)
        return

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    sepairCount = len(estVolt)

    # update the timestamp zoom slider upper limit and default value
    if firstPassFlag:
        # scale based on cube root of number of node/phase pairs
        # The multiplier is just a magic scaling factor that seems to produce
        # reasonable values for the 3 models used as test cases
        upper = 100 * (sepairCount**(1./3))
        #upper = 18 * (sepairCount**(1./3))
        # round to the nearest 10 to keep the slider from looking odd
        upper = int(round(upper/10.0)) * 10;
        # sanity check just in case
        upper = max(upper, 60)
        # // is integer floor division operator
        default = upper // 2;
        #print('setting time slider upper limit: ' + str(upper) + ', default value: ' + str(default) + ', matchCount: ' + str(matchCount), flush=True)
        uiTSZoomSldr.valmin = 1
        uiTSZoomSldr.valmax = upper
        uiTSZoomSldr.val = default
        uiTSZoomSldr.ax.set_xlim(uiTSZoomSldr.valmin, uiTSZoomSldr.valmax)
        uiTSZoomSldr.set_val(uiTSZoomSldr.val)

        # save first timestamp so what we plot is an offset from this
        tsInit = ts

        # clear flag that sets zoom slider values
        firstPassFlag = False

    # set the data element keys we want to extract
    if plotMagFlag:
        sekey = 'v'
        simkey = 'magnitude'
    else:
        sekey = 'angle'
        simkey = 'angle'

    for item in estVolt:
        # only consider phases A, B, C
        phase = item['phase']
        if phase!='A' and phase!='B' and phase!='C':
            continue

        sepair = item['ConnectivityNode'] + ',' + phase

        if sepair in plotPairDict:
            sevval = item[sekey]
            sevval = calcVNom(sevval, sepair)

            #print(appName + ': node,phase pair: ' + sepair, flush=True)
            #print(appName + ': timestamp: ' + str(ts), flush=True)
            #print(appName + ': sevval: ' + str(sevval), flush=True)

            matchCount += 1

            simvval = None
            if not plotMatchesFlag:
                if matchCount == 1:
                    tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
                SEDataPausedDict[sepair].append(sevval) if plotPausedFlag else SEDataDict[sepair].append(sevval)
            if simDataTS is not None and sepair in SEToSimDict:
                for simmrid in SEToSimDict[sepair]:
                    if simmrid in simDataTS:
                        simmeas = simDataTS[simmrid]
                        if simkey in simmeas:
                            diffMatchCount += 1
                            if plotMatchesFlag:
                                if diffMatchCount == 1:
                                    tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
                                SEDataPausedDict[sepair].append(sevval) if plotPausedFlag else SEDataDict[sepair].append(sevval)
                            simvval = simmeas[simkey]
                            simvval = calcVNom(simvval, sepair)
                            simDataPausedDict[sepair].append(simvval) if plotPausedFlag else simDataDict[sepair].append(simvval)

                            if not plotMagFlag:
                                diffvval = sevval - simvval
                            elif simvval != 0.0:
                                diffvval = 100.0*(sevval - simvval)/simvval
                            else:
                                diffvval = 0.0
                            if not plotOverlayFlag:
                                diffDataPausedDict[sepair].append(diffvval) if plotPausedFlag else diffDataDict[sepair].append(diffvval)
                            if plotMagFlag:
                                vmagPrintWithSim(ts, sepair, sevval, simvval, diffvval)
                            else:
                                vangPrintWithSim(ts, sepair, sevval, simvval, diffvval)
                            break
            if not simvval:
                if plotMagFlag:
                    vmagPrintWithoutSim(ts, sepair, sevval)
                else:
                    vangPrintWithoutSim(ts, sepair, sevval)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if not plotMatchesFlag and matchCount==len(plotPairDict):
                break
            elif plotMatchesFlag and diffMatchCount==len(plotPairDict):
                break

    #print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' configuration file node,phase pair matches, ' + str(diffMatchCount) + ' matches to simulation data', flush=True)

    # update plots with the new data
    plotData(None)


def estimateNoConfigCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    # to account for state estimator work queue draining design, iterate over
    # simAllDataDict and toss all measurements until we reach the current
    # timestamp since they won't be referenced again and will just drain memory
    simDataTS = None
    for tskey in list(simAllDataDict):
        if tskey < ts:
            del simAllDataDict[tskey]
        elif tskey == ts:
            simDataTS = simAllDataDict[tskey]
            break
        else:
            break

    if not simDataTS:
        print(appName + ': NOTE: No simulation measurement for timestamp: ' + str(ts) + ', disregarding estimate', flush=True)
        return

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    sepairCount = len(estVolt)

    if firstPassFlag:
        # update the timestamp zoom slider upper limit and default value
        # scale based on cube root of number of node/phase pairs
        # The multiplier is just a magic scaling factor that seems to produce
        # reasonable values for the 3 models used as test cases
        upper = 100 * (sepairCount**(1./3))
        #upper = 18 * (sepairCount**(1./3))
        # round to the nearest 10 to keep the slider from looking odd
        upper = int(round(upper/10.0)) * 10;
        # sanity check just in case
        upper = max(upper, 60)
        # // is integer floor division operator
        default = upper // 2;
        #print('setting slider upper limit: ' + str(upper) + ', default value: ' + str(default) + ', matchCount: ' + str(matchCount), flush=True)
        uiTSZoomSldr.valmin = 1
        uiTSZoomSldr.valmax = upper
        uiTSZoomSldr.val = default
        uiTSZoomSldr.ax.set_xlim(uiTSZoomSldr.valmin, uiTSZoomSldr.valmax)
        uiTSZoomSldr.set_val(uiTSZoomSldr.val)
        uiTSZoomSldr.valmin = 1

    if firstPassFlag:
        # save first timestamp so what we plot is an offset from this
        tsInit = ts

    # set the data element keys we want to extract
    if plotMagFlag:
        sekey = 'v'
        simkey = 'magnitude'
    else:
        sekey = 'angle'
        simkey = 'angle'

    for item in estVolt:
        # only consider phases A, B, C
        phase = item['phase']
        if phase!='A' and phase!='B' and phase!='C':
            continue

        sepair = item['ConnectivityNode'] + ',' + phase
        sevval = item[sekey]
        sevval = calcVNom(sevval, sepair)

        #print(appName + ': node,phase pair: ' + sepair + ', matchCount: ' + str(matchCount), flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': sevval: ' + str(sevval), flush=True)

        # only do the dictionary initializtion code on the first call
        if firstPassFlag:
            SEDataDict[sepair] = []
            SEDataPausedDict[sepair] = []
            simDataDict[sepair] = []
            simDataPausedDict[sepair] = []
            if not plotOverlayFlag:
                diffDataDict[sepair] = []
                diffDataPausedDict[sepair] = []

            # create a lines dictionary entry per node/phase pair for each plot
            if plotOverlayFlag:
                SELinesDict[sepair], = uiSEAx.plot([], [], label=SEToBusDict[sepair], linestyle='--')

                diffLinesDict[sepair+' Actual'], = uiDiffAx.plot([], [], label=SEToBusDict[sepair]+' Actual')
                color = diffLinesDict[sepair+' Actual'].get_color()
                diffLinesDict[sepair+' Est'], = uiDiffAx.plot([], [], label=SEToBusDict[sepair]+' Est.', linestyle='--', color=color)
            else:
                SELinesDict[sepair], = uiSEAx.plot([], [], label=SEToBusDict[sepair])

                diffLinesDict[sepair], = uiDiffAx.plot([], [], label=SEToBusDict[sepair])

            simLinesDict[sepair], = uiSimAx.plot([], [], label=SEToBusDict[sepair])

        # 123-node angle plots:
        #   phase A heads to -60 degrees right away
        #   phase B heads to -20 degrees around 500 seconds
        #   phase C stays around 0, ranging from 0 to 2.5 degrees away from
        #     the actual angle

        # Phase exclusion logic
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        matchCount += 1

        simvval = None
        if not plotMatchesFlag:
            if matchCount == 1:
                tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
            SEDataPausedDict[sepair].append(sevval) if plotPausedFlag else SEDataDict[sepair].append(sevval)
        if simDataTS is not None and sepair in SEToSimDict:
            for simmrid in SEToSimDict[sepair]:
                if simmrid in simDataTS:
                    simmeas = simDataTS[simmrid]
                    if simkey in simmeas:
                        diffMatchCount += 1
                        if plotMatchesFlag:
                            if diffMatchCount == 1:
                                tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
                            SEDataPausedDict[sepair].append(sevval) if plotPausedFlag else SEDataDict[sepair].append(sevval)

                        simvval = simmeas[simkey]
                        simvval = calcVNom(simvval, sepair)
                        simDataPausedDict[sepair].append(simvval) if plotPausedFlag else simDataDict[sepair].append(simvval)

                        if not plotMagFlag:
                            diffvval = sevval - simvval
                        elif simvval != 0.0:
                            diffvval = 100.0*(sevval - simvval)/simvval
                        else:
                            diffvval = 0.0
                        if not plotOverlayFlag:
                            diffDataPausedDict[sepair].append(diffvval) if plotPausedFlag else diffDataDict[sepair].append(diffvval)

                        if plotMagFlag:
                            vmagPrintWithSim(ts, sepair, sevval, simvval, diffvval)
                        else:
                            vangPrintWithSim(ts, sepair, sevval, simvval, diffvval)
                        break
        if not simvval:
            if plotMagFlag:
                vmagPrintWithoutSim(ts, sepair, sevval)
            else:
                vangPrintWithoutSim(ts, sepair, sevval)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if not plotMatchesFlag and plotNumber>0 and matchCount==plotNumber:
            break
        elif plotMatchesFlag and plotNumber>0 and diffMatchCount==plotNumber:
            break

    firstPassFlag = False

    #if plotNumber > 0:
    #    print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching first ' + str(plotNumber) + '), ' + str(diffMatchCount) + ' matches to simulation data', flush=True)
    #else:
    #    print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching all), ' + str(diffMatchCount) + ' matches to simulation data', flush=True)

    # update plots with the new data
    plotData(None)


def estimateStatsCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    # to account for state estimator work queue draining design, iterate over
    # simAllDataDict and toss all measurements until we reach the current
    # timestamp since they won't be referenced again and will just drain memory
    simDataTS = None
    for tskey in list(simAllDataDict):
        if tskey < ts:
            del simAllDataDict[tskey]
        elif tskey == ts:
            simDataTS = simAllDataDict[tskey]
            break
        else:
            break

    if not simDataTS:
        print(appName + ': NOTE: No simulation measurement for timestamp: ' + str(ts) + ', disregarding estimate', flush=True)
        return

    estVolt = msgdict['Estimate']['SvEstVoltages']
    sepairCount = len(estVolt)

    if firstPassFlag:
        # update the timestamp zoom slider upper limit and default value
        # scale based on cube root of number of node/phase pairs
        # The multiplier is just a magic scaling factor that seems to produce
        # reasonable values for the 3 models used as test cases
        upper = 100 * (sepairCount**(1./3))
        #upper = 18 * (sepairCount**(1./3))
        # round to the nearest 10 to keep the slider from looking odd
        upper = int(round(upper/10.0)) * 10;
        # sanity check just in case
        upper = max(upper, 60)
        # // is integer floor division operator
        #default = upper // 2;
        default = upper // 2;
        #print('setting slider upper limit: ' + str(upper) + ', default value: ' + str(default) + ', matchCount: ' + str(matchCount), flush=True)
        uiTSZoomSldr.valmin = 1
        uiTSZoomSldr.valmax = upper
        uiTSZoomSldr.val = default
        uiTSZoomSldr.ax.set_xlim(uiTSZoomSldr.valmin, uiTSZoomSldr.valmax)
        uiTSZoomSldr.set_val(uiTSZoomSldr.val)
        uiTSZoomSldr.valmin = 1

        SEDataDict['Min'] = []
        SEDataDict['Max'] = []
        SEDataDict['Mean'] = []
        SEDataDict['Stdev Low'] = []
        SEDataDict['Stdev High'] = []
        SEDataPausedDict['Min'] = []
        SEDataPausedDict['Max'] = []
        SEDataPausedDict['Mean'] = []
        SEDataPausedDict['Stdev Low'] = []
        SEDataPausedDict['Stdev High'] = []
        simDataDict['Min'] = []
        simDataDict['Max'] = []
        simDataDict['Mean'] = []
        simDataDict['Stdev Low'] = []
        simDataDict['Stdev High'] = []
        simDataPausedDict['Min'] = []
        simDataPausedDict['Max'] = []
        simDataPausedDict['Mean'] = []
        simDataPausedDict['Stdev Low'] = []
        simDataPausedDict['Stdev High'] = []

        # create a lines dictionary entry per node/phase pair for each plot
        if plotOverlayFlag:
            SELinesDict['Min'], = uiSEAx.plot([], [], label='Minimum', linestyle='--', color='cyan')
            SELinesDict['Max'], = uiSEAx.plot([], [], label='Maximum', linestyle='--', color='cyan')
            SELinesDict['Stdev Low'], = uiSEAx.plot([], [], label='Std. Dev. Low', linestyle='--', color='blue')
            SELinesDict['Stdev High'], = uiSEAx.plot([], [], label='Std. Dev. High', linestyle='--', color='blue')
            SELinesDict['Mean'], = uiSEAx.plot([], [], label='Mean', linestyle='--', color='red')

            diffLinesDict['Min Actual'], = uiDiffAx.plot([], [], label='Minimum Actual', color='cyan')
            color = diffLinesDict['Min Actual'].get_color()
            diffLinesDict['Min Est'], = uiDiffAx.plot([], [], label='Minimum Est.', linestyle='--', color=color)

            diffLinesDict['Max Actual'], = uiDiffAx.plot([], [], label='Maximum Actual', color='cyan')
            color = diffLinesDict['Max Actual'].get_color()
            diffLinesDict['Max Est'], = uiDiffAx.plot([], [], label='Maximum Est.', linestyle='--', color=color)

            diffLinesDict['Stdev Low Actual'], = uiDiffAx.plot([], [], label='Std. Dev. Low Actual', color='blue')
            color = diffLinesDict['Stdev Low Actual'].get_color()
            diffLinesDict['Stdev Low Est'], = uiDiffAx.plot([], [], label='Std. Dev. Low Est.', linestyle='--', color=color)

            diffLinesDict['Stdev High Actual'], = uiDiffAx.plot([], [], label='Std. Dev. High Actual', color='blue')
            color = diffLinesDict['Stdev High Actual'].get_color()
            diffLinesDict['Stdev High Est'], = uiDiffAx.plot([], [], label='Std. Dev. High Est.', linestyle='--', color=color)

            diffLinesDict['Mean Actual'], = uiDiffAx.plot([], [], label='Mean Actual', color='red')
            color = diffLinesDict['Mean Actual'].get_color()
            diffLinesDict['Mean Est'], = uiDiffAx.plot([], [], label='Mean Est.', linestyle='--', color=color)

        else:
            SELinesDict['Min'], = uiSEAx.plot([], [], label='Minimum', color='cyan')
            SELinesDict['Max'], = uiSEAx.plot([], [], label='Maximum', color='cyan')
            SELinesDict['Stdev Low'], = uiSEAx.plot([], [], label='Std. Dev. Low', color='blue')
            SELinesDict['Stdev High'], = uiSEAx.plot([], [], label='Std. Dev. High', color='blue')
            SELinesDict['Mean'], = uiSEAx.plot([], [], label='Mean', color='red')

            diffDataDict['Mean'] = []
            diffDataPausedDict['Mean'] = []

            diffLinesDict['Mean'], = uiDiffAx.plot([], [], label='Mean', color='red')

        simLinesDict['Min'], = uiSimAx.plot([], [], label='Minimum', color='cyan')
        simLinesDict['Max'], = uiSimAx.plot([], [], label='Maximum', color='cyan')
        simLinesDict['Stdev Low'], = uiSimAx.plot([], [], label='Std. Dev. Low', color='blue')
        simLinesDict['Stdev High'], = uiSimAx.plot([], [], label='Std. Dev. High', color='blue')
        simLinesDict['Mean'], = uiSimAx.plot([], [], label='Mean', color='red')

    if firstPassFlag:
        # save first timestamp so what we plot is an offset from this
        tsInit = ts
        firstPassFlag = False

    # set the data element keys we want to extract
    if plotMagFlag:
        sekey = 'v'
        simkey = 'magnitude'
    else:
        sekey = 'angle'
        simkey = 'angle'

    selist = []
    simlist = []
    difflist = []

    for item in estVolt:
        # only consider phases A, B, C and user-specified phases
        phase = item['phase']
        if phase!='A' and phase!='B' and phase!='C' or \
           len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        sepair = item['ConnectivityNode'] + ',' + phase
        sevval = item[sekey]
        sevval = calcVNom(sevval, sepair)

        #print(appName + ': node,phase pair: ' + sepair, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': sevval: ' + str(sevval), flush=True)

        simvval = None
        if not plotMatchesFlag:
            selist.append(sevval)
        if simDataTS is not None and sepair in SEToSimDict:
            for simmrid in SEToSimDict[sepair]:
                if simmrid in simDataTS:
                    simmeas = simDataTS[simmrid]
                    if simkey in simmeas:
                        if plotMatchesFlag:
                            selist.append(sevval)

                        simvval = simmeas[simkey]
                        simvval = calcVNom(simvval, sepair)
                        simlist.append(simvval)

                        if not plotMagFlag:
                            diffvval = sevval - simvval
                        elif simvval != 0.0:
                            diffvval = 100.0*(sevval - simvval)/simvval
                        else:
                            diffvval = 0.0

                        if not plotOverlayFlag:
                            difflist.append(diffvval)

                        if plotMagFlag:
                            vmagPrintWithSim(ts, sepair, sevval, simvval, diffvval)
                        else:
                            vangPrintWithSim(ts, sepair, sevval, simvval, diffvval)
                        break

        if not simvval:
            if plotMagFlag:
                vmagPrintWithoutSim(ts, sepair, sevval)
            else:
                vangPrintWithoutSim(ts, sepair, sevval)

    tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)

    semin = min(selist)
    semax = max(selist)
    semean = statistics.mean(selist)
    sestdev = statistics.pstdev(selist, semean)
    SEDataPausedDict['Min'].append(semin) if plotPausedFlag else SEDataDict['Min'].append(semin)
    SEDataPausedDict['Max'].append(semax) if plotPausedFlag else SEDataDict['Max'].append(semax)
    SEDataPausedDict['Mean'].append(semean) if plotPausedFlag else SEDataDict['Mean'].append(semean)
    SEDataPausedDict['Stdev Low'].append(semean-sestdev) if plotPausedFlag else SEDataDict['Stdev Low'].append(semean-sestdev)
    SEDataPausedDict['Stdev High'].append(semean+sestdev) if plotPausedFlag else SEDataDict['Stdev High'].append(semean+sestdev)

    if len(simlist) > 0:
        simmin = min(simlist)
        simmax = max(simlist)
        simmean = statistics.mean(simlist)
        simstdev = statistics.pstdev(simlist, simmean)
        simDataPausedDict['Min'].append(simmin) if plotPausedFlag else simDataDict['Min'].append(simmin)
        simDataPausedDict['Max'].append(simmax) if plotPausedFlag else simDataDict['Max'].append(simmax)
        simDataPausedDict['Mean'].append(simmean) if plotPausedFlag else simDataDict['Mean'].append(simmean)
        simDataPausedDict['Stdev Low'].append(simmean-simstdev) if plotPausedFlag else simDataDict['Stdev Low'].append(simmean-simstdev)
        simDataPausedDict['Stdev High'].append(simmean+simstdev) if plotPausedFlag else simDataDict['Stdev High'].append(simmean+simstdev)

    if not plotOverlayFlag and len(difflist)>0:
        diffmean = statistics.mean(difflist)
        diffDataPausedDict['Mean'].append(diffmean) if plotPausedFlag else diffDataDict['Mean'].append(diffmean)
        if plotMagFlag:
            print(appName + ': mean magnitude % diff: ' + str(diffmean), flush=True)
        else:
            print(appName + ': mean angle diff: ' + str(diffmean), flush=True)

    # update plots with the new data
    plotData(None)


def simulationOutputCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': simulation output message timestamp: ' + str(ts), flush=True)
    # a single dot per measurement to match how state-estimator does it
    print('.', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    simAllDataDict[ts] = msgdict['measurements']


def yAxisLimits(yMin, yMax, zoomVal, panVal):
    #print(appName + ': starting yMin: ' + str(yMin), flush=True)
    #print(appName + ': starting yMax: ' + str(yMax), flush=True)

    # check for yMin > yMax, which indicates there was no data to drive the
    # min/max determination
    if yMin > yMax:
        print(appName + ': NOTE: y-axis minimum and maximum values were not set due to lack of data--defaulting to 0-100\n', flush=True)
        yMin = 0.0
        yMax = 100.0
    elif yMin!=0.0 and abs((yMax-yMin)/yMin)<0.05:
        # scale values for near-constant data to avoid overly tight axis limits
        yMin -= abs(yMin)*0.025
        yMax += abs(yMax)*0.025

    yDiff = yMax - yMin

    if zoomVal == 100:
        height = yDiff
    else:
        height = yDiff*zoomVal/100.0

    middle = yMin + yDiff*panVal/100.0

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
    margin = height*0.10
    newYmin -= margin
    newYmax += margin
    #print(appName + ': margin newYmin: ' + str(newYmin), flush=True)
    #print(appName + ': margin newYmax: ' + str(newYmax) + '\n', flush=True)

    return newYmin, newYmax


def plotData(event):
    global firstPlotFlag

    # avoid error by making sure there is data to plot, which really means
    # lines, or 2 points, since single points don't show up
    if len(tsDataList) < 2:
        return

    simDataFlag = False
    diffDataFlag = False

    if plotShowAllFlag:
        xupper = int(tsDataList[-1])
        if xupper > 0:
            uiSEAx.set_xlim(0, xupper)

        SEYmax = -sys.float_info.max
        SEYmin = sys.float_info.max
        for pair in SEDataDict:
            if len(SEDataDict[pair]) > 0:
                if len(SEDataDict[pair]) != len(tsDataList):
                    print('***MISMATCH Estimate show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(SEDataDict[pair])), flush=True)
                SELinesDict[pair].set_xdata(tsDataList)
                SELinesDict[pair].set_ydata(SEDataDict[pair])
                SEYmin = min(SEYmin, min(SEDataDict[pair]))
                SEYmax = max(SEYmax, max(SEDataDict[pair]))
                if firstPlotFlag and len(plotPairDict)>0:
                    SELegendLineList.append(SELinesDict[pair])
                    SELegendLabelList.append(plotPairDict[pair])
        #print(appName + ': SEYmin: ' + str(SEYmin) + ', SEYmax: ' + str(SEYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiSEAx)
            if len(SEDataDict['Mean']) > 0:
                if len(SEDataDict['Mean']) != len(tsDataList):
                    print('***MISMATCH Estimate show all statistics, xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(SEDataDict['Mean'])), flush=True)
                plt.fill_between(x=tsDataList, y1=SEDataDict['Mean'], y2=SEDataDict['Stdev Low'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=SEDataDict['Mean'], y2=SEDataDict['Stdev High'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=SEDataDict['Stdev Low'], y2=SEDataDict['Min'], color=minmaxBlue)
                plt.fill_between(x=tsDataList, y1=SEDataDict['Stdev High'], y2=SEDataDict['Max'], color=minmaxBlue)

        simYmax = -sys.float_info.max
        simYmin = sys.float_info.max
        for pair in simDataDict:
            if len(simDataDict[pair]) > 0:
                simDataFlag = True
                if len(simDataDict[pair]) != len(tsDataList):
                    print('***MISMATCH Simulation show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(simDataDict[pair])), flush=True)
                simLinesDict[pair].set_xdata(tsDataList)
                simLinesDict[pair].set_ydata(simDataDict[pair])
                simYmin = min(simYmin, min(simDataDict[pair]))
                simYmax = max(simYmax, max(simDataDict[pair]))
                if firstPlotFlag and len(plotPairDict)>0:
                    simLegendLineList.append(simLinesDict[pair])
                    simLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': simYmin: ' + str(simYmin) + ', simYmax: ' + str(simYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiSimAx)
            if len(simDataDict['Mean']) > 0:
                if len(simDataDict['Mean']) != len(tsDataList):
                    print('***MISMATCH Simulation show all statistics, xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(simDataDict['Mean'])), flush=True)
                plt.fill_between(x=tsDataList, y1=simDataDict['Mean'], y2=simDataDict['Stdev Low'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=simDataDict['Mean'], y2=simDataDict['Stdev High'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=simDataDict['Stdev Low'], y2=simDataDict['Min'], color=minmaxBlue)
                plt.fill_between(x=tsDataList, y1=simDataDict['Stdev High'], y2=simDataDict['Max'], color=minmaxBlue)

        diffYmax = -sys.float_info.max
        diffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in SEDataDict:
                if len(SEDataDict[pair]) > 0:
                    if len(SEDataDict[pair]) != len(tsDataList):
                        print('***MISMATCH Difference Estimate show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(SEDataDict[pair])), flush=True)
                    diffLinesDict[pair+' Est'].set_xdata(tsDataList)
                    diffLinesDict[pair+' Est'].set_ydata(SEDataDict[pair])
                    diffYmin = min(diffYmin, min(SEDataDict[pair]))
                    diffYmax = max(diffYmax, max(SEDataDict[pair]))

                if len(simDataDict[pair]) > 0:
                    if len(simDataDict[pair]) != len(tsDataList):
                        print('***MISMATCH Difference Simulation show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(simDataDict[pair])), flush=True)
                    diffLinesDict[pair+' Actual'].set_xdata(tsDataList)
                    diffLinesDict[pair+' Actual'].set_ydata(simDataDict[pair])
                    diffYmin = min(diffYmin, min(simDataDict[pair]))
                    diffYmax = max(diffYmax, max(simDataDict[pair]))

        else:
            for pair in diffDataDict:
                if len(diffDataDict[pair]) > 0:
                    if len(diffDataDict[pair]) != len(tsDataList):
                        print('***MISMATCH Difference show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(diffDataDict[pair])), flush=True)
                    diffDataFlag = True
                    diffLinesDict[pair].set_xdata(tsDataList)
                    diffLinesDict[pair].set_ydata(diffDataDict[pair])
                    diffYmin = min(diffYmin, min(diffDataDict[pair]))
                    diffYmax = max(diffYmax, max(diffDataDict[pair]))
        #print(appName + ': diffYmin: ' + str(diffYmin) + ', diffYmax: ' + str(diffYmax), flush=True)

    else:
        tsZoom = int(uiTSZoomSldr.val)
        tsPan = int(uiTSPanSldr.val)
        if tsPan == 100:
            # this fills data from the right
            tsXmax = tsDataList[-1]
            tsXmin = tsXmax - tsZoom

            # uncomment this code if filling from the left is preferred
            #if tsXmin < 0:
            #    tsXmin = 0
            #    tsXmax = tsZoom
        elif tsPan == 0:
            tsXmin = 0
            tsXmax = tsZoom
        else:
            tsMid = int(tsDataList[-1]*tsPan/100.0)
            tsXmin = int(tsMid - tsZoom/2.0)
            tsXmax = tsXmin + tsZoom
            # this fills data from the right
            if tsXmax > tsDataList[-1]:
                tsXmax = tsDataList[-1]
                tsXmin = tsXmax - tsZoom
            elif tsXmin < 0:
                tsXmin = 0
                tsXmax = tsZoom
            # if filling from the left is preferred uncomment the lines
            # below and comment out the block if/elif block above
            #if tsXmin < 0:
            #    tsXmax = tsDataList[-1]
            #    tsXmin = tsXmax - tsZoom
            #elif tsXmax > tsDataList[-1]:
            #    tsXmin = 0
            #    tsXmax = tsZoom

        uiSEAx.set_xlim(tsXmin, tsXmax)
        #print(appName + ': tsXmin: ' + str(tsXmin), flush=True)
        #print(appName + ': tsXmax: ' + str(tsXmax), flush=True)

        tsStartpt = 0
        if tsXmin > 0:
            # don't assume 3 timesteps between points, calculate startpt instead
            #tsStartpt = int(tsXmin/3.0)
            for ix in range(len(tsDataList)):
                #print(appName + ': tsStartpt ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                if tsDataList[ix] >= tsXmin:
                    # if it's feasible, set starting point to 1 before the
                    # calculated point so there is no data gap at the left edge
                    if ix > 1:
                        tsStartpt = ix - 1
                    #print(appName + ': tsStartpt break ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                    break

        # don't assume 3 timesteps between points, calculate endpt instead
        #tsEndpt = int(tsXmax/3.0) + 1
        tsEndpt = 0
        if tsXmax > 0:
            tsEndpt = len(tsDataList)-1
            for ix in range(tsEndpt,-1,-1):
                #print(appName + ': tsEndpt ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                if tsDataList[ix] <= tsXmax:
                    # if it's feasible, set ending point to 1 after the
                    # calculated point so there is no data gap at the right edge
                    if ix < tsEndpt:
                        tsEndpt = ix + 1
                    #print(appName + ': tsEndpt break ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                    break

        # always add 1 to endpt because array slice uses -1 for upper bound
        tsEndpt += 1
        #print(appName + ': tsStartpt: ' + str(tsStartpt), flush=True)
        #print(appName + ': tsEndpt: ' + str(tsEndpt) + '\n', flush=True)

        SEYmax = -sys.float_info.max
        SEYmin = sys.float_info.max
        for pair in SEDataDict:
            if len(SEDataDict[pair][tsStartpt:tsEndpt]) > 0:
                if len(SEDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Estimate pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(SEDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                SELinesDict[pair].set_xdata(tsDataList[tsStartpt:tsEndpt])
                SELinesDict[pair].set_ydata(SEDataDict[pair][tsStartpt:tsEndpt])
                SEYmin = min(SEYmin, min(SEDataDict[pair][tsStartpt:tsEndpt]))
                SEYmax = max(SEYmax, max(SEDataDict[pair][tsStartpt:tsEndpt]))
                if firstPlotFlag and len(plotPairDict)>0:
                    SELegendLineList.append(SELinesDict[pair])
                    SELegendLabelList.append(plotPairDict[pair])
        #print(appName + ': SEYmin: ' + str(SEYmin) + ', SEYmax: ' + str(SEYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiSEAx)
            if len(SEDataDict['Mean'][tsStartpt:tsEndpt]) > 0:
                if len(SEDataDict['Mean'][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Estimate statistics, xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(SEDataDict['Mean'][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=SEDataDict['Mean'][tsStartpt:tsEndpt], y2=SEDataDict['Stdev Low'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=SEDataDict['Mean'][tsStartpt:tsEndpt], y2=SEDataDict['Stdev High'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=SEDataDict['Stdev Low'][tsStartpt:tsEndpt], y2=SEDataDict['Min'][tsStartpt:tsEndpt], color=minmaxBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=SEDataDict['Stdev High'][tsStartpt:tsEndpt], y2=SEDataDict['Max'][tsStartpt:tsEndpt], color=minmaxBlue)

        simYmax = -sys.float_info.max
        simYmin = sys.float_info.max
        for pair in simDataDict:
            if len(simDataDict[pair][tsStartpt:tsEndpt]) > 0:
                simDataFlag = True
                if len(simDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Simulation pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(simDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                simLinesDict[pair].set_xdata(tsDataList[tsStartpt:tsEndpt])
                simLinesDict[pair].set_ydata(simDataDict[pair][tsStartpt:tsEndpt])
                simYmin = min(simYmin, min(simDataDict[pair][tsStartpt:tsEndpt]))
                simYmax = max(simYmax, max(simDataDict[pair][tsStartpt:tsEndpt]))
                if firstPlotFlag and len(plotPairDict)>0:
                    simLegendLineList.append(simLinesDict[pair])
                    simLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': simYmin: ' + str(simYmin) + ', simYmax: ' + str(simYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiSimAx)
            if len(simDataDict['Mean'][tsStartpt:tsEndpt]) > 0:
                if len(simDataDict['Mean'][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Simulation statistics, xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(simDataDict['Mean'][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=simDataDict['Mean'][tsStartpt:tsEndpt], y2=simDataDict['Stdev Low'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=simDataDict['Mean'][tsStartpt:tsEndpt], y2=simDataDict['Stdev High'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=simDataDict['Stdev Low'][tsStartpt:tsEndpt], y2=simDataDict['Min'][tsStartpt:tsEndpt], color=minmaxBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=simDataDict['Stdev High'][tsStartpt:tsEndpt], y2=simDataDict['Max'][tsStartpt:tsEndpt], color=minmaxBlue)

        diffYmax = -sys.float_info.max
        diffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in SEDataDict:
                if len(SEDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    if len(SEDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                        print('***MISMATCH Difference Estimate pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(SEDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                    diffLinesDict[pair+' Est'].set_xdata(tsDataList[tsStartpt:tsEndpt])
                    diffLinesDict[pair+' Est'].set_ydata(SEDataDict[pair][tsStartpt:tsEndpt])
                    diffYmin = min(diffYmin, min(SEDataDict[pair][tsStartpt:tsEndpt]))
                    diffYmax = max(diffYmax, max(SEDataDict[pair][tsStartpt:tsEndpt]))

                if len(simDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    if len(simDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                        print('***MISMATCH Difference Simulation pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(simDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                    diffLinesDict[pair+' Actual'].set_xdata(tsDataList[tsStartpt:tsEndpt])
                    diffLinesDict[pair+' Actual'].set_ydata(simDataDict[pair][tsStartpt:tsEndpt])
                    diffYmin = min(diffYmin, min(simDataDict[pair][tsStartpt:tsEndpt]))
                    diffYmax = max(diffYmax, max(simDataDict[pair][tsStartpt:tsEndpt]))

        else:
            for pair in diffDataDict:
                if len(diffDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    diffDataFlag = True
                    if len(diffDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                        print('***MISMATCH Difference pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(diffDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                    diffLinesDict[pair].set_xdata(tsDataList[tsStartpt:tsEndpt])
                    diffLinesDict[pair].set_ydata(diffDataDict[pair][tsStartpt:tsEndpt])
                    diffYmin = min(diffYmin, min(diffDataDict[pair][tsStartpt:tsEndpt]))
                    diffYmax = max(diffYmax, max(diffDataDict[pair][tsStartpt:tsEndpt]))

        #print(appName + ': diffYmin: ' + str(diffYmin) + ', diffYmax: ' + str(diffYmax), flush=True)

    # state-estimator voltage magnitude plot y-axis zoom and pan calculation
    #print(appName + ': state-estimator voltage value y-axis limits...', flush=True)
    newSEYmin, newSEYmax = yAxisLimits(SEYmin, SEYmax, uiSEZoomSldr.val, uiSEPanSldr.val)
    uiSEAx.set_ylim(newSEYmin, newSEYmax)
    uiSEAx.xaxis.set_visible(True)
    uiSEAx.yaxis.set_visible(True)

    # simulation voltage value plot y-axis zoom and pan calculation
    if not simDataFlag:
        print(appName + ': NOTE: no simulation voltage value data to plot yet\n', flush=True)
    #print(appName + ': simulator voltage value y-axis limits...', flush=True)
    newSimYmin, newSimYmax = yAxisLimits(simYmin, simYmax, uiSimZoomSldr.val, uiSimPanSldr.val)
    uiSimAx.set_ylim(newSimYmin, newSimYmax)
    uiSimAx.xaxis.set_visible(True)
    uiSimAx.yaxis.set_visible(True)

    # voltage value difference plot y-axis zoom and pan calculation
    if not plotOverlayFlag and not diffDataFlag:
        print(appName + ': NOTE: no voltage value difference data to plot yet\n', flush=True)
    #print(appName + ': voltage value difference y-axis limits...', flush=True)
    newDiffYmin, newDiffYmax = yAxisLimits(diffYmin, diffYmax, uiDiffZoomSldr.val, uiDiffPanSldr.val)
    uiDiffAx.set_ylim(newDiffYmin, newDiffYmax)
    uiDiffAx.xaxis.set_visible(True)
    uiDiffAx.yaxis.set_visible(True)

    if firstPlotFlag:
        if plotStatsFlag:
            uiSEAx.legend()
            uiSimAx.legend()

        elif len(plotPairDict) > 0:
            if plotLegendFlag or len(SELegendLineList)<=10:
                cols = math.ceil(len(SELegendLineList)/8)
                uiSEAx.legend(SELegendLineList, SELegendLabelList, ncol=cols)

            if plotLegendFlag or len(simLegendLineList)<=10:
                cols = math.ceil(len(simLegendLineList)/8)
                uiSimAx.legend(simLegendLineList, simLegendLabelList, ncol=cols)

    firstPlotFlag = False

    # flush all the plot changes
    plt.draw()


def plotPauseCallback(event):
    global plotPausedFlag
    # toggle whether plot is paused
    plotPausedFlag = not plotPausedFlag

    # update the button icon
    uiPauseAx.images[0].set_data(playIcon if plotPausedFlag else pauseIcon)
    plt.draw()

    if not plotPausedFlag:
        # add all the data that came in since the pause button was hit
        tsDataList.extend(tsDataPausedList)
        # clear the "paused" data so we build from scratch with the next pause
        tsDataPausedList.clear()

        # now do the same extend/clear for all the data
        for pair in SEDataDict:
            SEDataDict[pair].extend(SEDataPausedDict[pair])
            SEDataPausedDict[pair].clear()
            simDataDict[pair].extend(simDataPausedDict[pair])
            simDataPausedDict[pair].clear()

        if not plotOverlayFlag:
            for pair in diffDataDict:
                diffDataDict[pair].extend(diffDataPausedDict[pair])
                diffDataPausedDict[pair].clear()

    plotData(None)


def plotShowAllCallback(event):
    global plotShowAllFlag
    # toggle whether to show all timestamps
    plotShowAllFlag = not plotShowAllFlag

    # update the button icon
    uiShowAx.images[0].set_data(checkedIcon if plotShowAllFlag else uncheckedIcon)
    plt.draw()
    plotData(None)


def plotDataCallback(event):
    plt.draw()
    plotData(None)


def plotButtonPressCallback(event):
    lineFlag = False

    for line in uiSEAx.get_lines():
        if line.contains(event)[0]:
            lineFlag = True
            print(appName + ': clicked on estimate plot node: ' + line.get_label(), flush=True)

    for line in uiSimAx.get_lines():
        if line.contains(event)[0]:
            lineFlag = True
            print(appName + ': clicked on simulation plot node: ' + line.get_label(), flush=True)

    for line in uiDiffAx.get_lines():
        if line.contains(event)[0]:
            lineFlag = True
            print(appName + ': clicked on difference plot node: ' + line.get_label(), flush=True)

    if lineFlag:
        # separate clicks with a blank line
        print('', flush=True)

#def closeWindowCallback(event):
#    gapps.disconnect()
#    exit()


def queryBusToSE():
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

    connectivity_names_response = gapps.get_response('goss.gridappsd.process.request.data.powergridmodel', connectivity_names_request, timeout=1200)

    results = connectivity_names_response['data']['results']['bindings']

    for node in results:
        cnname = node['cnname']['value']
        cnname = cnname.upper()
        cnid = node['cnid']['value']
        busToSEDict[cnname] = cnid
        # add all possible pairs to speed lookup when printing diagnostics
        SEToBusDict[cnid+',A'] = cnname+'.1'
        SEToBusDict[cnid+',B'] = cnname+'.2'
        SEToBusDict[cnid+',C'] = cnname+'.3'
    print(appName + ': start state-estimator bus to semrid query results...', flush=True)
    pprint.pprint(busToSEDict)
    print(appName + ': end state-estimator bus to semrid query results', flush=True)


def initPlot(configFlag):
    global uiTSZoomSldr, uiTSPanSldr
    global uiSEAx, uiSEZoomSldr, uiSEPanSldr
    global uiSimAx, uiSimZoomSldr, uiSimPanSldr
    global uiDiffAx, uiDiffZoomSldr, uiDiffPanSldr
    global uiPauseBtn, uiPauseAx, pauseIcon, playIcon
    global uiShowBtn, uiShowAx, checkedIcon, uncheckedIcon

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

    plotFig = plt.figure(figsize=(10,6))

    if plotMagFlag:
        baseTitle = 'Voltage Magnitude, '
        if plotCompFlag:
            baseTitle += 'Per-Unit'
        else:
            baseTitle += 'Physical Units'
    else:
        baseTitle = 'Voltage Angle, '
        if plotCompFlag:
            baseTitle += 'Relative to Nominal'
        else:
            baseTitle += 'Absolute'

    baseTitle += ', Simulation ID: ' + simID
    if plotTitle:
        baseTitle += ', ' + plotTitle
    plotFig.canvas.set_window_title(baseTitle)

    # shouldn't be necessary to catch close window event, but uncomment
    # if plt.show() doesn't consistently exit when the window is closed
    #plotFig.canvas.mpl_connect('close_event', closeWindowCallback)

    uiSimAx = plotFig.add_subplot(311)
    uiSimAx.xaxis.set_major_locator(MaxNLocator(integer=True))
    uiSimAx.grid()
    # shrink the margins, especially the top since we don't want a label
    plt.subplots_adjust(bottom=0.09, left=0.08, right=0.96, top=0.98, hspace=0.1)
    # simulation measurement y-axis labels
    if plotMagFlag:
        if plotCompFlag:
            plt.ylabel('Field Volt. Mag. (p.u.)')
        else:
            plt.ylabel('Field Volt. Magnitude (V)')
    else:
        plt.ylabel('Field Volt. Angle (deg.)')
    plt.setp(uiSimAx.get_xticklabels(), visible=False)
    uiSimAx.xaxis.set_visible(False)
    uiSimAx.yaxis.set_visible(False)

    uiSEAx = plotFig.add_subplot(312, sharex=uiSimAx)
    uiSEAx.grid()
    # state estimator y-axis labels
    if plotMagFlag:
        if plotCompFlag:
            plt.ylabel('Est. Volt. Magnitude (p.u.)')
        else:
            plt.ylabel('Est. Volt. Magnitude (V)')
    else:
        plt.ylabel('Est. Volt. Angle (deg.)')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(uiSEAx.get_xticklabels(), visible=False)
    uiSEAx.xaxis.set_visible(False)
    uiSEAx.yaxis.set_visible(False)

    uiDiffAx = plotFig.add_subplot(313, sharex=uiSimAx)
    uiDiffAx.grid()
    plt.xlabel('Time (s)')
    if plotOverlayFlag:
        # overlay plot y-axis labels
        if plotMagFlag:
            if plotCompFlag:
                plt.ylabel('Field & Est. Mag. (p.u.)')
            else:
                plt.ylabel('Field & Est. Mag. (V)')
        else:
            plt.ylabel('Field & Est. Angle (deg.)')
    else:
        # difference plot y-axis labels
        if plotMagFlag:
            plt.ylabel('Volt. Magnitude % Diff.')
        else:
            plt.ylabel('Difference (deg.)')
    uiDiffAx.xaxis.set_visible(False)
    uiDiffAx.yaxis.set_visible(False)

    # pause/play button
    uiPauseAx = plt.axes([0.01, 0.01, 0.03, 0.03])
    pauseIcon = plt.imread('icons/pausebtn.png')
    playIcon = plt.imread('icons/playbtn.png')
    uiPauseBtn = Button(uiPauseAx, '', image=pauseIcon, color='1.0')
    uiPauseBtn.on_clicked(plotPauseCallback)

    # timestamp slice zoom slider
    uiTSZoomAx = plt.axes([0.32, 0.01, 0.1, 0.02])
    # note this slider has the label for the show all button as well as the
    # slider that's because the show all button uses a checkbox image and you
    # can't use both an image and a label with a button so this is a clever way
    # to get that behavior since matplotlib doesn't have a simple label widget
    uiTSZoomSldr = Slider(uiTSZoomAx, 'show all              zoom', 0, 1, valfmt='%d', valstep=1.0)
    uiTSZoomSldr.on_changed(plotDataCallback)

    # show all button that's embedded in the middle of the slider above
    uiShowAx = plt.axes([0.14, 0.01, 0.02, 0.02])
    uncheckedIcon = plt.imread('icons/uncheckedbtn.png')
    checkedIcon = plt.imread('icons/checkedbtn.png')
    uiShowBtn = Button(uiShowAx, '', image=uncheckedIcon, color='1.0')
    uiShowBtn.on_clicked(plotShowAllCallback)

    # timestamp slice pan slider
    uiTSPanAx = plt.axes([0.63, 0.01, 0.1, 0.02])
    uiTSPanSldr = Slider(uiTSPanAx, 'pan', 0, 100, valinit=100, valfmt='%d', valstep=1.0)
    uiTSPanSldr.on_changed(plotDataCallback)

    # simulation voltage value slice zoom and pan sliders
    uiSimZoomAx = plt.axes([0.97, 0.87, 0.012, 0.09])
    uiSimZoomSldr = Slider(uiSimZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    uiSimZoomSldr.on_changed(plotDataCallback)

    uiSimPanAx = plt.axes([0.97, 0.72, 0.012, 0.09])
    uiSimPanSldr = Slider(uiSimPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    uiSimPanSldr.on_changed(plotDataCallback)

    # state-estimator voltage value slice zoom and pan sliders
    uiSEZoomAx = plt.axes([0.97, 0.56, 0.012, 0.09])
    uiSEZoomSldr = Slider(uiSEZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    uiSEZoomSldr.on_changed(plotDataCallback)

    uiSEPanAx = plt.axes([0.97, 0.41, 0.012, 0.09])
    uiSEPanSldr = Slider(uiSEPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    uiSEPanSldr.on_changed(plotDataCallback)

    # voltage value difference slice zoom and pan sliders
    uiDiffZoomAx = plt.axes([0.97, 0.26, 0.012, 0.09])
    uiDiffZoomSldr = Slider(uiDiffZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    uiDiffZoomSldr.on_changed(plotDataCallback)

    uiDiffPanAx = plt.axes([0.97, 0.11, 0.012, 0.09])
    uiDiffPanSldr = Slider(uiDiffPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    uiDiffPanSldr.on_changed(plotDataCallback)

    plotFig.canvas.mpl_connect('button_press_event', plotButtonPressCallback)


def configPlot(busList):
    if len(busList) > 0:
        for buspair in busList:
            buspair = buspair.upper()
            if ',' in buspair:
                bus, phase = buspair.split(',')
                if bus in busToSEDict:
                    plotPairDict[busToSEDict[bus] + ',' + phase] = buspair
            else:
                if buspair+'.1' in busToSimDict:
                    plotPairDict[busToSEDict[buspair]+',A'] = buspair+',A'
                if buspair+'.2' in busToSimDict:
                    plotPairDict[busToSEDict[buspair]+',B'] = buspair+',B'
                if buspair+'.3' in busToSimDict:
                    plotPairDict[busToSEDict[buspair]+',C'] = buspair+',C'
    else:
        # match connectivity node,phase pairs with the config file for determining
        # what data to plot
        try:
            with open('../state-plotter-config.csv') as pairfile:
                for buspair in pairfile:
                    # strip all whitespace from line whether at beginning, middle, or end
                    buspair = ''.join(buspair.split())
                    # skip empty and commented out lines
                    if buspair=='' or buspair.startswith('#'):
                        next

                    buspair = buspair.upper()
                    if ',' in buspair:
                        bus, phase = buspair.split(',')
                        if bus in busToSEDict:
                            plotPairDict[busToSEDict[bus] + ',' + phase] = buspair
                    else:
                        if buspair+'.1' in busToSimDict:
                            plotPairDict[busToSEDict[buspair]+',A'] = buspair+',A'
                        if buspair+'.2' in busToSimDict:
                            plotPairDict[busToSEDict[buspair]+',B'] = buspair+',B'
                        if buspair+'.3' in busToSimDict:
                            plotPairDict[busToSEDict[buspair]+',C'] = buspair+',C'
            #print(appName + ': ' + str(plotPairDict), flush=True)
        except:
            print(appName + ': ERROR: node/phase pair configuration file state-plotter-config.csv does not exist.\n', flush=True)
            exit()

    for pair in plotPairDict:
        # create empty lists for the per pair data for each plot so we can
        # just do append calls when data to plot arrives
        SEDataDict[pair] = []
        SEDataPausedDict[pair] = []
        simDataDict[pair] = []
        simDataPausedDict[pair] = []

        if not plotOverlayFlag:
            diffDataDict[pair] = []
            diffDataPausedDict[pair] = []

        # create a lines dictionary entry per node/phase pair for each plot
        if plotOverlayFlag:
            SELinesDict[pair], = uiSEAx.plot([], [], label=plotPairDict[pair], linestyle='--')

            diffLinesDict[pair+' Actual'], = uiDiffAx.plot([], [], label=plotPairDict[pair]+' Actual')
            color = diffLinesDict[pair+' Actual'].get_color()
            diffLinesDict[pair+' Est'], = uiDiffAx.plot([], [], label=plotPairDict[pair]+' Est.', linestyle='--', color=color)
        else:
            SELinesDict[pair], = uiSEAx.plot([], [], label=plotPairDict[pair])

            diffLinesDict[pair], = uiDiffAx.plot([], [], label=plotPairDict[pair])

        simLinesDict[pair], = uiSimAx.plot([], [], label=plotPairDict[pair])


def _main():
    global appName, simID, simReq, gapps
    global plotTitle, plotNumber, plotMagFlag, plotCompFlag, printDataFlag
    global plotStatsFlag, plotOverlayFlag, plotLegendFlag, plotMatchesFlag

    if len(sys.argv)<2 or '-help' in sys.argv:
        usestr =  '\nUsage: ' + sys.argv[0] + ' simID simReq\n'
        usestr += '''
Optional command line arguments:
        -mag[nitude]: voltage magnitude plots should be created (default)
        -ang[le]: voltage angle plots should be created
        -over[lay]: overlays simulation measurement and state estimate values
         in the same bottom plot instead of the default to plot the difference
         between simulation measurement and state estimate values
        -match: only plot state estimates when there is a matching bus,phase
         pair in simulation measurements
        -comp[aritivebasis]: plot comparitive basis values. I.e., per-unit
         voltage magnitudes and relative-to-nominal voltage angles (default)
        -phys[icalunits]: plot voltage magnitude in physical units and voltage
         angle in absolute/non-relative terms. I.e., no shifting is applied to
         the voltage angle; three-phase systems will have voltage angles
         clustered around each of three nominal phase angles.
        -nocomp[aritivebasis]: equivalent to -phys[icalunits], comparitive
         basis values are not plotted
        -stat[s][istics]: plots minimum, maximum, mean and standard deviation
         values over all bus,phase pairs for each timestamp (default if none
         from -bus, -conf, -all, nor -# are specified). Can be used in
         combination with -phase to report statistics for specific phases.
         The standard deviation is shown as a shaded range below and above
         the mean value.  Minimum and maximum value ranges are shaded below
         and above the standard deviation ranges.
        -bus: plots the specified bus name and phase comma-separated pair (no
         spaces) given as the argument that follows. The bus name alone may be
         given without a comma and phase and all phases that are present will
         be plotted, e.g. "-bus 150" will plot phases A, B, and C if present.
         Plotting combinations of bus,phase pairs is done by repeating the -bus
         option, e.g., "-bus 150,A -bus 160,A". Using -bus on the command line
         results in state-plotter-config.csv bus,phase pairs being disregarded.
        -conf[ig]: read bus name and phase pairs from state-plotter-config.csv
         file in parent directory. Each line contains a bus name and phase
         comma-separated pair. The bus name alone may be given without a comma
         and phase and all phases that are present will be plotted. Lines
         starting with the character "#" are treated as comments and ignored
         as are blank lines.
        -all: plots all bus,phase pairs disregarding any pairs specified by
         state-plotter-config.csv or the -bus option
        -#, where # is an integer value: plots the first # bus,phase pairs
         that occur in state estimator output, e.g., "-25" plots the first 25
         bus,phase pairs. Like -all, any pairs specified by
         state-plotter-config.csv or the -bus option are disregarded when
         using this option. If there are fewer pairs than #, all pairs are
         plotted.
        -sim[all]: plots all simulation measurements, not just those for
         for timestamps where there is an estimated state
        -phase: plots only the specified phase (A, B, or C) given as the
         argument that follows. Combinations of phases in the same plot are
         done by repeating the -phase option, e.g., "-phase A -phase B" to
         exclude phase C. If there are bus,phase pairs specified in
         state-plotter-config.csv or with the -bus option, they will be
         excluded if -phase is used and the phase of the pair differs. E.g.,
         "-bus 160,A -phase C" will not plot the 160,A pair, nor any data in
         this case, since the -phase option specifies only phase C.
        -legend: Indicates that a legend should be shown for the plot when
         bus,phase pairs are specified either with the -bus option or in 
         state-plotter-config.csv
        -title: appends argument that follows to the standard title to allow
         plot windows to be distinguished from each other. The argument can be
         quoted to allow spaces.
        -print: print diagnostic bus,phase pair data for each timestamp
        -help: show this usage message
        '''
        print(usestr, flush=True)
        exit()

    appName = sys.argv[0]
    simID = sys.argv[1]
    simReq = sys.argv[2]

    plotConfigFlag = False
    plotBusFlag = False
    plotPhaseFlag = False
    plotTitleFlag = False
    plotBusList = []
    for arg in sys.argv:
        if plotBusFlag:
            plotBusList.append(arg)
            plotBusFlag = False
        elif plotPhaseFlag:
            plotPhaseList.append(arg)
            plotPhaseFlag = False
        elif plotTitleFlag:
            plotTitle = arg
            plotTitleFlag = False
        elif arg == '-legend':
            plotLegendFlag = True
        elif arg == '-all':
            plotNumber = 0 # magic number to plot all pairs
            plotStatsFlag = False
            plotConfigFlag = False
        elif arg.startswith('-stat'):
            plotStatsFlag = True
            plotConfigFlag = False
        elif arg.startswith('-mag'):
            plotMagFlag = True
        elif arg.startswith('-ang'):
            plotMagFlag = False
        elif arg.startswith('-over'):
            plotOverlayFlag = True
        elif arg.startswith('-match'):
            plotMatchesFlag = True
        elif arg.startswith('-phys') or arg.startswith('-nocomp'):
            plotCompFlag = False
        elif arg.startswith('-comp'):
            plotCompFlag = True
        elif arg.startswith('-sim'):
            plotSimAllFlag = True
        elif arg[0]=='-' and arg[1:].isdigit():
            plotNumber = int(arg[1:])
            plotStatsFlag = False
            plotConfigFlag = False
        elif arg == '-bus':
            plotBusFlag = True
            plotStatsFlag = False
        elif arg.startswith('-conf'):
            plotConfigFlag = True
            plotStatsFlag = False
        elif arg == '-phase':
            plotPhaseFlag = True
        elif arg == '-title':
            plotTitleFlag = True
        elif arg == '-print':
            printDataFlag = True

    gapps = GridAPPSD()

    # subscribe to simulation output for comparison with estimates
    # subscribe as early as possible to avoid getting any estimates
    # without corresponding simulation measurements for a timestamp
    gapps.subscribe('/topic/goss.gridappsd.simulation.output.' +
                    simID, simulationOutputCallback)

    # query to get connectivity node,phase pairs
    queryBusToSE()

    # query to get bus to sensor mrid mapping
    queryBusToSim()

    # finally, create map between state-estimator and simulation output
    mapSEToSim()

    # query to get the nominimal voltage mapping
    queryVnom()

    # matplotlib setup done before receiving any messages that reference it
    initPlot(plotConfigFlag)

    if plotConfigFlag or len(plotBusList)>0:
        # determine what to plot based on the state-plotter-config file
        # and finish plot initialization
        configPlot(plotBusList)

        # subscribe to state-estimator output--with config file
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                        simID, estimateConfigCallback)
    else:
        # subscribe to state-estimator output--one of two methods
        # without config file
        if plotStatsFlag:
            gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                            simID, estimateStatsCallback)
        else:
            gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                            simID, estimateNoConfigCallback)

    # interactive plot event loop allows both the ActiveMQ messages to be
    # received and plot GUI events
    plt.show()

    gapps.disconnect()


if __name__ == '__main__':
    _main()

