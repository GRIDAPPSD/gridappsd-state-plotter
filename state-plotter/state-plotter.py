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
simDataDict = {}
SEToVnomMagDict = {}
SEToVnomAngDict = {}

vvalTSDataList = []
vvalTSDataPausedList = []
vvalSEDataDict = {}
vvalSEDataPausedDict = {}
vvalSimDataDict = {}
vvalSimDataPausedDict = {}
vvalDiffDataDict = {}
vvalDiffDataPausedDict = {}
vvalSELinesDict = {}
vvalSimLinesDict = {}
vvalDiffLinesDict = {}
seLegendLineList = []
seLegendLabelList = []
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
plotNominalFlag = True
plotMMMFlag = True
vvalPausedFlag = False
vvalShowFlag = False
firstPassFlag = True
firstPlotFlag = True
plotOverlayFlag = False
plotLegendFlag = False
plotMatchesFlag = False
plotNumber = 0
plotTitle = None
playIcon = None
pauseIcon = None
checkedIcon = None
uncheckedIcon = None
vvalTSZoomSldr = None
vvalTSPanSldr = None
vvalPauseAx = None
vvalPauseBtn = None
vvalShowBtn = None
vvalShowAx = None
vvalSEAx = None
vvalSEZoomSldr = None
vvalSEPanSldr = None
vvalSimAx = None
vvalSimZoomSldr = None
vvalSimPanSldr = None
vvalDiffAx = None
vvalDiffZoomSldr = None
vvalDiffPanSldr = None


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
    print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag: ' + str(sevmag), flush=True)
    if '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F' in simReq:
        if sevmag > 4000:
            print(appName + ': OUTLIER, 13-node, sevmag>4K: ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevmag > 4K: ' + str(sevmag), flush=True)


def vangPrintWithoutSim(ts, sepair, sevang):
    print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', sepair: ' + sepair + ', busname: ' + SEToBusDict[sepair] + ', sevang: ' + str(sevang), flush=True)


def calcVNom(vval, sepair):
    if plotNominalFlag and sepair in SEToVnomMagDict:
        if plotMagFlag:
            return vval / SEToVnomMagDict[sepair]
        else:
            return vval - SEToVnomAngDict[sepair]

    return vval


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
        #print('setting time slider upper limit: ' + str(upper) + ', default value: ' + str(default) + ', matchCount: ' + str(matchCount), flush=True)
        vvalTSZoomSldr.valmin = 1
        vvalTSZoomSldr.valmax = upper
        vvalTSZoomSldr.val = default
        vvalTSZoomSldr.ax.set_xlim(vvalTSZoomSldr.valmin, vvalTSZoomSldr.valmax)
        vvalTSZoomSldr.set_val(vvalTSZoomSldr.val)

        # save first timestamp so what we plot is an offset from this
        tsInit = ts

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
                    vvalTSDataPausedList.append(ts - tsInit) if vvalPausedFlag else vvalTSDataList.append(ts - tsInit)
                vvalSEDataPausedDict[sepair].append(sevval) if vvalPausedFlag else vvalSEDataDict[sepair].append(sevval)
            if simDataTS is not None and sepair in SEToSimDict:
                for simmrid in SEToSimDict[sepair]:
                    if simmrid in simDataTS:
                        simmeas = simDataTS[simmrid]
                        if simkey in simmeas:
                            diffMatchCount += 1
                            if plotMatchesFlag:
                                if diffMatchCount == 1:
                                    vvalTSDataPausedList.append(ts - tsInit) if vvalPausedFlag else vvalTSDataList.append(ts - tsInit)
                                vvalSEDataPausedDict[sepair].append(sevval) if vvalPausedFlag else vvalSEDataDict[sepair].append(sevval)
                            simvval = simmeas[simkey]
                            simvval = calcVNom(simvval, sepair)
                            vvalSimDataPausedDict[sepair].append(simvval) if vvalPausedFlag else vvalSimDataDict[sepair].append(simvval)

                            if not plotMagFlag:
                                diffvval = sevval - simvval
                            elif simvval != 0.0:
                                diffvval = 100.0*(sevval - simvval)/simvval
                            else:
                                diffvval = 0.0
                            if not plotOverlayFlag:
                                vvalDiffDataPausedDict[sepair].append(diffvval) if vvalPausedFlag else vvalDiffDataDict[sepair].append(diffvval)
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

    print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' configuration file node,phase pair matches, ' + str(diffMatchCount) + ' matches to simulation data', flush=True)

    # update plots with the new data
    vvalPlotData(None)


def measurementNoConfigCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    sepairCount = len(estVolt)

    if firstPassFlag:
        # update the timestamp zoom slider upper limit and default value
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
        vvalTSZoomSldr.valmin = 1
        vvalTSZoomSldr.valmax = upper
        vvalTSZoomSldr.val = default
        vvalTSZoomSldr.ax.set_xlim(vvalTSZoomSldr.valmin, vvalTSZoomSldr.valmax)
        vvalTSZoomSldr.set_val(vvalTSZoomSldr.val)
        vvalTSZoomSldr.valmin = 1

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
            vvalSEDataDict[sepair] = []
            vvalSEDataPausedDict[sepair] = []
            vvalSimDataDict[sepair] = []
            vvalSimDataPausedDict[sepair] = []
            if not plotOverlayFlag:
                vvalDiffDataDict[sepair] = []
                vvalDiffDataPausedDict[sepair] = []

            # create a lines dictionary entry per node/phase pair for each plot
            if plotOverlayFlag:
                vvalSELinesDict[sepair], = vvalSEAx.plot([], [], label=SEToBusDict[sepair], linestyle='--')

                vvalDiffLinesDict[sepair+' Actual'], = vvalDiffAx.plot([], [], label=SEToBusDict[sepair]+' Actual')
                color = vvalDiffLinesDict[sepair+' Actual'].get_color()
                vvalDiffLinesDict[sepair+' Est'], = vvalDiffAx.plot([], [], label=SEToBusDict[sepair]+' Est.', linestyle='--', color=color)
            else:
                vvalSELinesDict[sepair], = vvalSEAx.plot([], [], label=SEToBusDict[sepair])

                vvalDiffLinesDict[sepair], = vvalDiffAx.plot([], [], label=SEToBusDict[sepair])

            vvalSimLinesDict[sepair], = vvalSimAx.plot([], [], label=SEToBusDict[sepair])

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
                vvalTSDataPausedList.append(ts - tsInit) if vvalPausedFlag else vvalTSDataList.append(ts - tsInit)
            vvalSEDataPausedDict[sepair].append(sevval) if vvalPausedFlag else vvalSEDataDict[sepair].append(sevval)
        if simDataTS is not None and sepair in SEToSimDict:
            for simmrid in SEToSimDict[sepair]:
                if simmrid in simDataTS:
                    simmeas = simDataTS[simmrid]
                    if simkey in simmeas:
                        diffMatchCount += 1
                        if plotMatchesFlag:
                            if diffMatchCount == 1:
                                vvalTSDataPausedList.append(ts - tsInit) if vvalPausedFlag else vvalTSDataList.append(ts - tsInit)
                            vvalSEDataPausedDict[sepair].append(sevval) if vvalPausedFlag else vvalSEDataDict[sepair].append(sevval)

                        simvval = simmeas[simkey]
                        simvval = calcVNom(simvval, sepair)
                        vvalSimDataPausedDict[sepair].append(simvval) if vvalPausedFlag else vvalSimDataDict[sepair].append(simvval)

                        if not plotMagFlag:
                            diffvval = sevval - simvval
                        elif simvval != 0.0:
                            diffvval = 100.0*(sevval - simvval)/simvval
                        else:
                            diffvval = 0.0
                        if not plotOverlayFlag:
                            vvalDiffDataPausedDict[sepair].append(diffvval) if vvalPausedFlag else vvalDiffDataDict[sepair].append(diffvval)

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

    if plotNumber > 0:
        print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching first ' + str(plotNumber) + '), ' + str(diffMatchCount) + ' matches to simulation data', flush=True)
    else:
        print(appName + ': ' + str(sepairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching all), ' + str(diffMatchCount) + ' matches to simulation data', flush=True)

    # update plots with the new data
    vvalPlotData(None)


def measurementMMMCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    estVolt = msgdict['Estimate']['SvEstVoltages']
    sepairCount = len(estVolt)

    if firstPassFlag:
        # update the timestamp zoom slider upper limit and default value
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
        vvalTSZoomSldr.valmin = 1
        vvalTSZoomSldr.valmax = upper
        vvalTSZoomSldr.val = default
        vvalTSZoomSldr.ax.set_xlim(vvalTSZoomSldr.valmin, vvalTSZoomSldr.valmax)
        vvalTSZoomSldr.set_val(vvalTSZoomSldr.val)
        vvalTSZoomSldr.valmin = 1

        vvalSEDataDict['Min'] = []
        vvalSEDataDict['Max'] = []
        vvalSEDataDict['Mean'] = []
        vvalSEDataDict['Stdev Low'] = []
        vvalSEDataDict['Stdev High'] = []
        vvalSEDataPausedDict['Min'] = []
        vvalSEDataPausedDict['Max'] = []
        vvalSEDataPausedDict['Mean'] = []
        vvalSEDataPausedDict['Stdev Low'] = []
        vvalSEDataPausedDict['Stdev High'] = []
        vvalSimDataDict['Min'] = []
        vvalSimDataDict['Max'] = []
        vvalSimDataDict['Mean'] = []
        vvalSimDataDict['Stdev Low'] = []
        vvalSimDataDict['Stdev High'] = []
        vvalSimDataPausedDict['Min'] = []
        vvalSimDataPausedDict['Max'] = []
        vvalSimDataPausedDict['Mean'] = []
        vvalSimDataPausedDict['Stdev Low'] = []
        vvalSimDataPausedDict['Stdev High'] = []

        # create a lines dictionary entry per node/phase pair for each plot
        if plotOverlayFlag:
            vvalSELinesDict['Min'], = vvalSEAx.plot([], [], label='Minimum', linestyle='--', color='cyan')
            vvalSELinesDict['Max'], = vvalSEAx.plot([], [], label='Maximum', linestyle='--', color='cyan')
            vvalSELinesDict['Stdev Low'], = vvalSEAx.plot([], [], label='Std. Dev. Low', linestyle='--', color='blue')
            vvalSELinesDict['Stdev High'], = vvalSEAx.plot([], [], label='Std. Dev. High', linestyle='--', color='blue')
            vvalSELinesDict['Mean'], = vvalSEAx.plot([], [], label='Mean', linestyle='--', color='red')

            vvalDiffLinesDict['Min Actual'], = vvalDiffAx.plot([], [], label='Minimum Actual', color='cyan')
            color = vvalDiffLinesDict['Min Actual'].get_color()
            vvalDiffLinesDict['Min Est'], = vvalDiffAx.plot([], [], label='Minimum Est.', linestyle='--', color=color)

            vvalDiffLinesDict['Max Actual'], = vvalDiffAx.plot([], [], label='Maximum Actual', color='cyan')
            color = vvalDiffLinesDict['Max Actual'].get_color()
            vvalDiffLinesDict['Max Est'], = vvalDiffAx.plot([], [], label='Maximum Est.', linestyle='--', color=color)

            vvalDiffLinesDict['Stdev Low Actual'], = vvalDiffAx.plot([], [], label='Std. Dev. Low Actual', color='blue')
            color = vvalDiffLinesDict['Stdev Low Actual'].get_color()
            vvalDiffLinesDict['Stdev Low Est'], = vvalDiffAx.plot([], [], label='Std. Dev. Low Est.', linestyle='--', color=color)

            vvalDiffLinesDict['Stdev High Actual'], = vvalDiffAx.plot([], [], label='Std. Dev. High Actual', color='blue')
            color = vvalDiffLinesDict['Stdev High Actual'].get_color()
            vvalDiffLinesDict['Stdev High Est'], = vvalDiffAx.plot([], [], label='Std. Dev. High Est.', linestyle='--', color=color)

            vvalDiffLinesDict['Mean Actual'], = vvalDiffAx.plot([], [], label='Mean Actual', color='red')
            color = vvalDiffLinesDict['Mean Actual'].get_color()
            vvalDiffLinesDict['Mean Est'], = vvalDiffAx.plot([], [], label='Mean Est.', linestyle='--', color=color)

        else:
            vvalSELinesDict['Min'], = vvalSEAx.plot([], [], label='Minimum', color='cyan')
            vvalSELinesDict['Max'], = vvalSEAx.plot([], [], label='Maximum', color='cyan')
            vvalSELinesDict['Stdev Low'], = vvalSEAx.plot([], [], label='Std. Dev. Low', color='blue')
            vvalSELinesDict['Stdev High'], = vvalSEAx.plot([], [], label='Std. Dev. High', color='blue')
            vvalSELinesDict['Mean'], = vvalSEAx.plot([], [], label='Mean', color='red')

            vvalDiffDataDict['Min'] = []
            vvalDiffDataDict['Max'] = []
            vvalDiffDataDict['Stdev Low'] = []
            vvalDiffDataDict['Stdev High'] = []
            vvalDiffDataDict['Mean'] = []
            vvalDiffDataPausedDict['Min'] = []
            vvalDiffDataPausedDict['Max'] = []
            vvalDiffDataPausedDict['Stdev Low'] = []
            vvalDiffDataPausedDict['Stdev High'] = []
            vvalDiffDataPausedDict['Mean'] = []

            vvalDiffLinesDict['Min'], = vvalDiffAx.plot([], [], label='Minimum', color='cyan')
            vvalDiffLinesDict['Max'], = vvalDiffAx.plot([], [], label='Maximum', color='cyan')
            vvalDiffLinesDict['Stdev Low'], = vvalDiffAx.plot([], [], label='Std. Dev. Low', color='blue')
            vvalDiffLinesDict['Stdev High'], = vvalDiffAx.plot([], [], label='Std. Dev. High', color='blue')
            vvalDiffLinesDict['Mean'], = vvalDiffAx.plot([], [], label='Mean', color='red')

        vvalSimLinesDict['Min'], = vvalSimAx.plot([], [], label='Minimum', color='cyan')
        vvalSimLinesDict['Max'], = vvalSimAx.plot([], [], label='Maximum', color='cyan')
        vvalSimLinesDict['Stdev Low'], = vvalSimAx.plot([], [], label='Std. Dev. Low', color='blue')
        vvalSimLinesDict['Stdev High'], = vvalSimAx.plot([], [], label='Std. Dev. High', color='blue')
        vvalSimLinesDict['Mean'], = vvalSimAx.plot([], [], label='Mean', color='red')

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

    vvalTSDataPausedList.append(ts - tsInit) if vvalPausedFlag else vvalTSDataList.append(ts - tsInit)

    semin = min(selist)
    semax = max(selist)
    semean = statistics.mean(selist)
    sestdev = statistics.pstdev(selist, semean)
    vvalSEDataPausedDict['Min'].append(semin) if vvalPausedFlag else vvalSEDataDict['Min'].append(semin)
    vvalSEDataPausedDict['Max'].append(semax) if vvalPausedFlag else vvalSEDataDict['Max'].append(semax)
    vvalSEDataPausedDict['Mean'].append(semean) if vvalPausedFlag else vvalSEDataDict['Mean'].append(semean)
    vvalSEDataPausedDict['Stdev Low'].append(semean-sestdev) if vvalPausedFlag else vvalSEDataDict['Stdev Low'].append(semean-sestdev)
    vvalSEDataPausedDict['Stdev High'].append(semean+sestdev) if vvalPausedFlag else vvalSEDataDict['Stdev High'].append(semean+sestdev)

    simmin = min(simlist)
    simmax = max(simlist)
    simmean = statistics.mean(simlist)
    simstdev = statistics.pstdev(simlist, simmean)
    vvalSimDataPausedDict['Min'].append(simmin) if vvalPausedFlag else vvalSimDataDict['Min'].append(simmin)
    vvalSimDataPausedDict['Max'].append(simmax) if vvalPausedFlag else vvalSimDataDict['Max'].append(simmax)
    vvalSimDataPausedDict['Mean'].append(simmean) if vvalPausedFlag else vvalSimDataDict['Mean'].append(simmean)
    vvalSimDataPausedDict['Stdev Low'].append(simmean-simstdev) if vvalPausedFlag else vvalSimDataDict['Stdev Low'].append(simmean-simstdev)
    vvalSimDataPausedDict['Stdev High'].append(simmean+simstdev) if vvalPausedFlag else vvalSimDataDict['Stdev High'].append(simmean+simstdev)

    if not plotOverlayFlag:
        diffmin = min(difflist)
        diffmax = max(difflist)
        diffmean = statistics.mean(difflist)
        diffstdev = statistics.pstdev(difflist, diffmean)
        vvalDiffDataPausedDict['Min'].append(diffmin) if vvalPausedFlag else vvalDiffDataDict['Min'].append(diffmin)
        vvalDiffDataPausedDict['Max'].append(diffmax) if vvalPausedFlag else vvalDiffDataDict['Max'].append(diffmax)
        vvalDiffDataPausedDict['Mean'].append(diffmean) if vvalPausedFlag else vvalDiffDataDict['Mean'].append(diffmean)
        vvalDiffDataPausedDict['Stdev Low'].append(diffmean-diffstdev) if vvalPausedFlag else vvalDiffDataDict['Stdev Low'].append(diffmean-diffstdev)
        vvalDiffDataPausedDict['Stdev High'].append(diffmean+diffstdev) if vvalPausedFlag else vvalDiffDataDict['Stdev High'].append(diffmean+diffstdev)

    # update plots with the new data
    vvalPlotData(None)


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
    #print(appName + ': starting yMin: ' + str(yMin), flush=True)
    #print(appName + ': starting yMax: ' + str(yMax), flush=True)

    # check for yMin > yMax, which indicates there was no data to drive the
    # min/max determination
    if yMin > yMax:
        print(appName + ': WARNING: y-axis minimum and maximum values were not set due to lack of data--defaulting to avoid Matplotlib error!\n', flush=True)
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


def vvalPlotData(event):
    global firstPlotFlag

    # avoid error by making sure there is data to plot
    if len(vvalTSDataList)==0:
        return

    vvalSimDataFlag = False
    vvalDiffDataFlag = False

    if vvalShowFlag:
        xupper = int(vvalTSDataList[-1])
        if xupper > 0:
            vvalSEAx.set_xlim(0, xupper)

        vvalSEYmax = -sys.float_info.max
        vvalSEYmin = sys.float_info.max
        for pair in vvalSEDataDict:
            if len(vvalSEDataDict[pair]) > 0:
                vvalSELinesDict[pair].set_xdata(vvalTSDataList)
                vvalSELinesDict[pair].set_ydata(vvalSEDataDict[pair])
                vvalSEYmin = min(vvalSEYmin, min(vvalSEDataDict[pair]))
                vvalSEYmax = max(vvalSEYmax, max(vvalSEDataDict[pair]))
                if firstPlotFlag and len(plotPairDict)>0:
                    seLegendLineList.append(vvalSELinesDict[pair])
                    seLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': vvalSEYmin: ' + str(vvalSEYmin) + ', vvalSEYmax: ' + str(vvalSEYmax), flush=True)

        vvalSimYmax = -sys.float_info.max
        vvalSimYmin = sys.float_info.max
        for pair in vvalSimDataDict:
            if len(vvalSimDataDict[pair]) > 0:
                vvalSimDataFlag = True
                vvalSimLinesDict[pair].set_xdata(vvalTSDataList)
                vvalSimLinesDict[pair].set_ydata(vvalSimDataDict[pair])
                vvalSimYmin = min(vvalSimYmin, min(vvalSimDataDict[pair]))
                vvalSimYmax = max(vvalSimYmax, max(vvalSimDataDict[pair]))
                if firstPlotFlag and len(plotPairDict)>0:
                    simLegendLineList.append(vvalSimLinesDict[pair])
                    simLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': vvalSimYmin: ' + str(vvalSimYmin) + ', vvalSimYmax: ' + str(vvalSimYmax), flush=True)

        vvalDiffYmax = -sys.float_info.max
        vvalDiffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in vvalSEDataDict:
                if len(vvalSEDataDict[pair]) > 0:
                    vvalDiffLinesDict[pair+' Est'].set_xdata(vvalTSDataList)
                    vvalDiffLinesDict[pair+' Est'].set_ydata(vvalSEDataDict[pair])
                    vvalDiffYmin = min(vvalDiffYmin, min(vvalSEDataDict[pair]))
                    vvalDiffYmax = max(vvalDiffYmax, max(vvalSEDataDict[pair]))
                if len(vvalSimDataDict[pair]) > 0:
                    vvalDiffLinesDict[pair+' Actual'].set_xdata(vvalTSDataList)
                    vvalDiffLinesDict[pair+' Actual'].set_ydata(vvalSimDataDict[pair])
                    vvalDiffYmin = min(vvalDiffYmin, min(vvalSimDataDict[pair]))
                    vvalDiffYmax = max(vvalDiffYmax, max(vvalSimDataDict[pair]))
        else:
            for pair in vvalDiffDataDict:
                if len(vvalDiffDataDict[pair]) > 0:
                    vvalDiffDataFlag = True
                    vvalDiffLinesDict[pair].set_xdata(vvalTSDataList)
                    vvalDiffLinesDict[pair].set_ydata(vvalDiffDataDict[pair])
                    vvalDiffYmin = min(vvalDiffYmin, min(vvalDiffDataDict[pair]))
                    vvalDiffYmax = max(vvalDiffYmax, max(vvalDiffDataDict[pair]))
        #print(appName + ': vvalDiffYmin: ' + str(vvalDiffYmin) + ', vvalDiffYmax: ' + str(vvalDiffYmax), flush=True)

    else:
        vvalTSZoom = int(vvalTSZoomSldr.val)
        vvalTime = int(vvalTSPanSldr.val)
        if vvalTime == 100:
            # this fills data from the right
            vvalXmax = vvalTSDataList[-1]
            vvalXmin = vvalXmax - vvalTSZoom

            # uncomment this code if filling from the left is preferred
            #if vvalXmin < 0:
            #    vvalXmin = 0
            #    vvalXmax = vvalTSZoom
        elif vvalTime == 0:
            vvalXmin = 0
            vvalXmax = vvalTSZoom
        else:
            vvalMid = int(vvalTSDataList[-1]*vvalTime/100.0)
            vvalXmin = int(vvalMid - vvalTSZoom/2.0)
            vvalXmax = vvalXmin + vvalTSZoom
            # this fills data from the right
            if vvalXmax > vvalTSDataList[-1]:
                vvalXmax = vvalTSDataList[-1]
                vvalXmin = vvalXmax - vvalTSZoom
            elif vvalXmin < 0:
                vvalXmin = 0
                vvalXmax = vvalTSZoom
            # if filling from the left is preferred uncomment the lines
            # below and comment out the block if/elif block above
            #if vvalXmin < 0:
            #    vvalXmax = vvalTSDataList[-1]
            #    vvalXmin = vvalXmax - vvalTSZoom
            #elif vvalXmax > vvalTSDataList[-1]:
            #    vvalXmin = 0
            #    vvalXmax = vvalTSZoom

        vvalSEAx.set_xlim(vvalXmin, vvalXmax)
        print(appName + ': vvalXmin: ' + str(vvalXmin), flush=True)
        print(appName + ': vvalXmax: ' + str(vvalXmax), flush=True)

        vvalStartpt = 0
        if vvalXmin > 0:
            # don't assume 3 timesteps between points, calculate startpt instead
            #vvalStartpt = int(vvalXmin/3.0)
            for ix in range(len(vvalTSDataList)):
                #print(appName + ': vvalStartpt ix: ' + str(ix) + ', vvalTSDataList: ' + str(vvalTSDataList[ix]), flush=True)
                if vvalTSDataList[ix] >= vvalXmin:
                    # if it's feasible, set starting point to 1 before the
                    # calculated point so there is no data gap at the left edge
                    if ix > 1:
                        vvalStartpt = ix - 1
                    #print(appName + ': vvalStartpt break ix: ' + str(ix) + ', vvalTSDataList: ' + str(vvalTSDataList[ix]), flush=True)
                    break

        # don't assume 3 timesteps between points, calculate endpt instead
        #vvalEndpt = int(vvalXmax/3.0) + 1
        vvalEndpt = 0
        if vvalXmax > 0:
            vvalEndpt = len(vvalTSDataList)-1
            for ix in range(vvalEndpt,-1,-1):
                #print(appName + ': vvalEndpt ix: ' + str(ix) + ', vvalTSDataList: ' + str(vvalTSDataList[ix]), flush=True)
                if vvalTSDataList[ix] <= vvalXmax:
                    # if it's feasible, set ending point to 1 after the
                    # calculated point so there is no data gap at the right edge
                    if ix < vvalEndpt:
                        vvalEndpt = ix + 1
                    #print(appName + ': vvalEndpt break ix: ' + str(ix) + ', vvalTSDataList: ' + str(vvalTSDataList[ix]), flush=True)
                    break

        # always add 1 to endpt because array slice uses -1 for upper bound
        vvalEndpt += 1
        print(appName + ': vvalStartpt: ' + str(vvalStartpt), flush=True)
        print(appName + ': vvalEndpt: ' + str(vvalEndpt) + '\n', flush=True)

        vvalSEYmax = -sys.float_info.max
        vvalSEYmin = sys.float_info.max
        for pair in vvalSEDataDict:
            if len(vvalSEDataDict[pair][vvalStartpt:vvalEndpt]) > 0:
                vvalSELinesDict[pair].set_xdata(vvalTSDataList[vvalStartpt:vvalEndpt])
                vvalSELinesDict[pair].set_ydata(vvalSEDataDict[pair][vvalStartpt:vvalEndpt])
                vvalSEYmin = min(vvalSEYmin, min(vvalSEDataDict[pair][vvalStartpt:vvalEndpt]))
                vvalSEYmax = max(vvalSEYmax, max(vvalSEDataDict[pair][vvalStartpt:vvalEndpt]))
                if firstPlotFlag and len(plotPairDict)>0:
                    seLegendLineList.append(vvalSELinesDict[pair])
                    seLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': vvalSEYmin: ' + str(vvalSEYmin) + ', vvalSEYmax: ' + str(vvalSEYmax), flush=True)

        vvalSimYmax = -sys.float_info.max
        vvalSimYmin = sys.float_info.max
        for pair in vvalSimDataDict:
            if len(vvalSimDataDict[pair][vvalStartpt:vvalEndpt]) > 0:
                vvalSimDataFlag = True
                vvalSimLinesDict[pair].set_xdata(vvalTSDataList[vvalStartpt:vvalEndpt])
                vvalSimLinesDict[pair].set_ydata(vvalSimDataDict[pair][vvalStartpt:vvalEndpt])
                vvalSimYmin = min(vvalSimYmin, min(vvalSimDataDict[pair][vvalStartpt:vvalEndpt]))
                vvalSimYmax = max(vvalSimYmax, max(vvalSimDataDict[pair][vvalStartpt:vvalEndpt]))
                if firstPlotFlag and len(plotPairDict)>0:
                    simLegendLineList.append(vvalSimLinesDict[pair])
                    simLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': vvalSimYmin: ' + str(vvalSimYmin) + ', vvalSimYmax: ' + str(vvalSimYmax), flush=True)

        vvalDiffYmax = -sys.float_info.max
        vvalDiffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in vvalSEDataDict:
                if len(vvalSEDataDict[pair][vvalStartpt:vvalEndpt]) > 0:
                    vvalDiffLinesDict[pair+' Est'].set_xdata(vvalTSDataList[vvalStartpt:vvalEndpt])
                    vvalDiffLinesDict[pair+' Est'].set_ydata(vvalSEDataDict[pair][vvalStartpt:vvalEndpt])
                    vvalDiffYmin = min(vvalDiffYmin, min(vvalSEDataDict[pair][vvalStartpt:vvalEndpt]))
                    vvalDiffYmax = max(vvalDiffYmax, max(vvalSEDataDict[pair][vvalStartpt:vvalEndpt]))
                if len(vvalSimDataDict[pair][vvalStartpt:vvalEndpt]) > 0:
                    vvalDiffLinesDict[pair+' Actual'].set_xdata(vvalTSDataList[vvalStartpt:vvalEndpt])
                    vvalDiffLinesDict[pair+' Actual'].set_ydata(vvalSimDataDict[pair][vvalStartpt:vvalEndpt])
                    vvalDiffYmin = min(vvalDiffYmin, min(vvalSimDataDict[pair][vvalStartpt:vvalEndpt]))
                    vvalDiffYmax = max(vvalDiffYmax, max(vvalSimDataDict[pair][vvalStartpt:vvalEndpt]))
        else:
            for pair in vvalDiffDataDict:
                if len(vvalDiffDataDict[pair][vvalStartpt:vvalEndpt]) > 0:
                    vvalDiffDataFlag = True
                    vvalDiffLinesDict[pair].set_xdata(vvalTSDataList[vvalStartpt:vvalEndpt])
                    vvalDiffLinesDict[pair].set_ydata(vvalDiffDataDict[pair][vvalStartpt:vvalEndpt])
                    vvalDiffYmin = min(vvalDiffYmin, min(vvalDiffDataDict[pair][vvalStartpt:vvalEndpt]))
                    vvalDiffYmax = max(vvalDiffYmax, max(vvalDiffDataDict[pair][vvalStartpt:vvalEndpt]))
        #print(appName + ': vvalDiffYmin: ' + str(vvalDiffYmin) + ', vvalDiffYmax: ' + str(vvalDiffYmax), flush=True)

    # state-estimator voltage magnitude plot y-axis zoom and pan calculation
    #print(appName + ': state-estimator voltage value y-axis limits...', flush=True)
    newvvalSEYmin, newvvalSEYmax = yAxisLimits(vvalSEYmin, vvalSEYmax, vvalSEZoomSldr.val, vvalSEPanSldr.val)
    vvalSEAx.set_ylim(newvvalSEYmin, newvvalSEYmax)

    # simulation voltage value plot y-axis zoom and pan calculation
    if not vvalSimDataFlag:
        print(appName + ': WARNING: no simulation voltage value data to plot!\n', flush=True)
    #print(appName + ': simulator voltage value y-axis limits...', flush=True)
    newvvalSimYmin, newvvalSimYmax = yAxisLimits(vvalSimYmin, vvalSimYmax, vvalSimZoomSldr.val, vvalSimPanSldr.val)
    vvalSimAx.set_ylim(newvvalSimYmin, newvvalSimYmax)

    # voltage value difference plot y-axis zoom and pan calculation
    if not plotOverlayFlag and not vvalDiffDataFlag:
        print(appName + ': WARNING: no voltage value difference data to plot!\n', flush=True)
    #print(appName + ': voltage value difference y-axis limits...', flush=True)
    newvvalDiffYmin, newvvalDiffYmax = yAxisLimits(vvalDiffYmin, vvalDiffYmax, vvalDiffZoomSldr.val, vvalDiffPanSldr.val)
    vvalDiffAx.set_ylim(newvvalDiffYmin, newvvalDiffYmax)

    if firstPlotFlag:
        if plotMMMFlag:
            vvalSEAx.legend()
            vvalSimAx.legend()

        elif len(plotPairDict) > 0:
            if plotLegendFlag or len(seLegendLineList)<=10:
                cols = math.ceil(len(seLegendLineList)/12)
                vvalSEAx.legend(seLegendLineList, seLegendLabelList, ncol=cols)

            if plotLegendFlag or len(simLegendLineList)<=10:
                cols = math.ceil(len(simLegendLineList)/12)
                vvalSimAx.legend(simLegendLineList, simLegendLabelList, ncol=cols)

    firstPlotFlag = False

    # flush all the plot changes
    plt.draw()


def vvalPauseCallback(event):
    global vvalPausedFlag
    # toggle whether plot is paused
    vvalPausedFlag = not vvalPausedFlag

    # update the button icon
    vvalPauseAx.images[0].set_data(playIcon if vvalPausedFlag else pauseIcon)
    plt.draw()

    if not vvalPausedFlag:
        # add all the data that came in since the pause button was hit
        vvalTSDataList.extend(vvalTSDataPausedList)
        # clear the "paused" data so we build from scratch with the next pause
        vvalTSDataPausedList.clear()

        # now do the same extend/clear for all the data
        for pair in vvalSEDataDict:
            vvalSEDataDict[pair].extend(vvalSEDataPausedDict[pair])
            vvalSEDataPausedDict[pair].clear()
            vvalSimDataDict[pair].extend(vvalSimDataPausedDict[pair])
            vvalSimDataPausedDict[pair].clear()

        if not plotOverlayFlag:
            for pair in vvalDiffDataDict:
                vvalDiffDataDict[pair].extend(vvalDiffDataPausedDict[pair])
                vvalDiffDataPausedDict[pair].clear()

    vvalPlotData(None)


def vvalShowCallback(event):
    global vvalShowFlag
    # toggle whether to show all timestamps
    vvalShowFlag = not vvalShowFlag

    # update the button icon
    vvalShowAx.images[0].set_data(checkedIcon if vvalShowFlag else uncheckedIcon)
    plt.draw()

    vvalPlotData(None)


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
    global vvalTSZoomSldr, vvalTSPanSldr
    global vvalSEAx, vvalSEZoomSldr, vvalSEPanSldr
    global vvalSimAx, vvalSimZoomSldr, vvalSimPanSldr
    global vvalDiffAx, vvalDiffZoomSldr, vvalDiffPanSldr
    global vvalPauseBtn, vvalPauseAx, pauseIcon, playIcon
    global vvalShowBtn, vvalShowAx, checkedIcon, uncheckedIcon

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

    vvalFig = plt.figure(figsize=(10,6))

    baseTitle = ''
    if plotNominalFlag:
        baseTitle = 'Nominal '
    if plotMagFlag:
        baseTitle += 'Voltage Magnitude'
    else:
        baseTitle += 'Voltage Angle'
    baseTitle += ', Simulation ID: ' + simID
    if plotTitle:
        baseTitle += ', ' + plotTitle
    vvalFig.canvas.set_window_title(baseTitle)

    # shouldn't be necessary to catch close window event, but uncomment
    # if plt.show() doesn't consistently exit when the window is closed
    #vvalFig.canvas.mpl_connect('close_event', closeWindowCallback)

    vvalSEAx = vvalFig.add_subplot(311)
    vvalSEAx.xaxis.set_major_locator(MaxNLocator(integer=True))
    vvalSEAx.grid()
    # shrink the margins, especially the top since we don't want a label
    plt.subplots_adjust(bottom=0.09, left=0.08, right=0.96, top=0.98, hspace=0.1)
    if plotMagFlag:
        if plotNominalFlag:
            plt.ylabel('Est. Volt. Magnitude (p.u.)')
        else:
            plt.ylabel('Est. Volt. Magnitude (V)')
    else:
        plt.ylabel('Est. Volt. Angle (deg.)')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(vvalSEAx.get_xticklabels(), visible=False)

    vvalSimAx = vvalFig.add_subplot(312, sharex=vvalSEAx)
    vvalSimAx.grid()
    if plotMagFlag:
        if plotNominalFlag:
            plt.ylabel('Actual Volt. Mag. (p.u.)')
        else:
            plt.ylabel('Actual Volt. Magnitude (V)')
    else:
        plt.ylabel('Actual Volt. Angle (deg.)')
    plt.setp(vvalSimAx.get_xticklabels(), visible=False)

    vvalDiffAx = vvalFig.add_subplot(313, sharex=vvalSEAx)
    vvalDiffAx.grid()
    plt.xlabel('Time (s)')
    if plotOverlayFlag:
        if plotMagFlag:
            plt.ylabel('Actual & Est. Magnitude')
        else:
            plt.ylabel('Actual & Est. Angle')
    else:
        if plotMagFlag:
            plt.ylabel('Volt. Magnitude % Diff.')
        else:
            plt.ylabel('Voltage Angle Diff.')

    # pause/play button
    vvalPauseAx = plt.axes([0.01, 0.01, 0.03, 0.03])
    pauseIcon = plt.imread('icons/pausebtn.png')
    playIcon = plt.imread('icons/playbtn.png')
    vvalPauseBtn = Button(vvalPauseAx, '', image=pauseIcon, color='1.0')
    vvalPauseBtn.on_clicked(vvalPauseCallback)

    # timestamp slice zoom slider
    vvalTSZoomAx = plt.axes([0.32, 0.01, 0.1, 0.02])
    # note this slider has the label for the show all button as well as the
    # slider that's because the show all button uses a checkbox image and you
    # can't use both an image and a label with a button so this is a clever way
    # to get that behavior since matplotlib doesn't have a simple label widget
    vvalTSZoomSldr = Slider(vvalTSZoomAx, 'show all              zoom', 0, 1, valfmt='%d', valstep=1.0)
    vvalTSZoomSldr.on_changed(vvalPlotData)

    # show all button that's embedded in the middle of the slider above
    vvalShowAx = plt.axes([0.14, 0.01, 0.02, 0.02])
    uncheckedIcon = plt.imread('icons/uncheckedbtn.png')
    checkedIcon = plt.imread('icons/checkedbtn.png')
    vvalShowBtn = Button(vvalShowAx, '', image=uncheckedIcon, color='1.0')
    vvalShowBtn.on_clicked(vvalShowCallback)

    # timestamp slice pan slider
    vvalTSPanAx = plt.axes([0.63, 0.01, 0.1, 0.02])
    vvalTSPanSldr = Slider(vvalTSPanAx, 'pan', 0, 100, valinit=100, valfmt='%d', valstep=1.0)
    vvalTSPanSldr.on_changed(vvalPlotData)

    # state-estimator voltage value slice zoom and pan sliders
    vvalSEZoomAx = plt.axes([0.97, 0.87, 0.012, 0.09])
    vvalSEZoomSldr = Slider(vvalSEZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vvalSEZoomSldr.on_changed(vvalPlotData)

    vvalSEPanAx = plt.axes([0.97, 0.72, 0.012, 0.09])
    vvalSEPanSldr = Slider(vvalSEPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vvalSEPanSldr.on_changed(vvalPlotData)

    # simulation voltage value slice zoom and pan sliders
    vvalSimZoomAx = plt.axes([0.97, 0.56, 0.012, 0.09])
    vvalSimZoomSldr = Slider(vvalSimZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vvalSimZoomSldr.on_changed(vvalPlotData)

    vvalSimPanAx = plt.axes([0.97, 0.41, 0.012, 0.09])
    vvalSimPanSldr = Slider(vvalSimPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vvalSimPanSldr.on_changed(vvalPlotData)

    # voltage value difference slice zoom and pan sliders
    vvalDiffZoomAx = plt.axes([0.97, 0.26, 0.012, 0.09])
    vvalDiffZoomSldr = Slider(vvalDiffZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    vvalDiffZoomSldr.on_changed(vvalPlotData)

    vvalDiffPanAx = plt.axes([0.97, 0.11, 0.012, 0.09])
    vvalDiffPanSldr = Slider(vvalDiffPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    vvalDiffPanSldr.on_changed(vvalPlotData)


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
        vvalSEDataDict[pair] = []
        vvalSEDataPausedDict[pair] = []
        vvalSimDataDict[pair] = []
        vvalSimDataPausedDict[pair] = []

        if not plotOverlayFlag:
            vvalDiffDataDict[pair] = []
            vvalDiffDataPausedDict[pair] = []

        # create a lines dictionary entry per node/phase pair for each plot
        if plotOverlayFlag:
            vvalSELinesDict[pair], = vvalSEAx.plot([], [], label=plotPairDict[pair], linestyle='--')

            vvalDiffLinesDict[pair+' Actual'], = vvalDiffAx.plot([], [], label=plotPairDict[pair]+' Actual')
            color = vvalDiffLinesDict[pair+' Actual'].get_color()
            vvalDiffLinesDict[pair+' Est'], = vvalDiffAx.plot([], [], label=plotPairDict[pair]+' Est.', linestyle='--', color=color)
        else:
            vvalSELinesDict[pair], = vvalSEAx.plot([], [], label=plotPairDict[pair])

            vvalDiffLinesDict[pair], = vvalDiffAx.plot([], [], label=plotPairDict[pair])

        vvalSimLinesDict[pair], = vvalSimAx.plot([], [], label=plotPairDict[pair])


def _main():
    global appName, simID, simReq, gapps
    global plotTitle, plotNumber, plotMagFlag, plotNominalFlag
    global plotMMMFlag, plotOverlayFlag, plotLegendFlag, plotMatchesFlag

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
        -nom[inal]: plot nominal voltage magnitudes and angles instead of
         actual (default)
        -act[ual]: plot actual voltage magnitudes and angles instead of the
         default nominal values
        -nonom[inal]: equivalent to -act[ual], nominal values are not plotted
        -min[maxmean]: plots minimum, maximum, and mean values over all
         bus,phase pairs for each timestamp (default if none from -bus, -conf,
         -all, nor -# are specified). Can be used in combination with -phase
         to report statistics for specific phases.
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
            plotMMMFlag = False
            plotConfigFlag = False
        elif arg.startswith('-min'):
            plotMMMFlag = True
            plotConfigFlag = False
        elif arg.startswith('-mag'):
            plotMagFlag = True
        elif arg.startswith('-ang'):
            plotMagFlag = False
        elif arg.startswith('-over'):
            plotOverlayFlag = True
        elif arg.startswith('-match'):
            plotMatchesFlag = True
        elif arg.startswith('-act') or arg.startswith('-nonom'):
            plotNominalFlag = False
        elif arg.startswith('-nom'):
            plotNominalFlag = True
        elif arg[0]=='-' and arg[1:].isdigit():
            plotNumber = int(arg[1:])
            plotMMMFlag = False
            plotConfigFlag = False
        elif arg == '-bus':
            plotBusFlag = True
            plotMMMFlag = False
        elif arg.startswith('-conf'):
            plotConfigFlag = True
            plotMMMFlag = False
        elif arg == '-phase':
            plotPhaseFlag = True
        elif arg == '-title':
            plotTitleFlag = True

    gapps = GridAPPSD()

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

        # subscribe to state-estimator measurement output--with config file
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                        simID, measurementConfigCallback)
    else:
        # subscribe to state-estimator measurement output--one of two methods
        # without config file
        if plotMMMFlag:
            gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.' +
                            simID, measurementMMMCallback)
        else:
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

