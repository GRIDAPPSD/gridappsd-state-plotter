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
import matplotlib.ticker as ticker
from matplotlib.widgets import Slider
from matplotlib.widgets import Button
from matplotlib.widgets import CheckButtons
from matplotlib.ticker import MaxNLocator
from matplotlib import backend_bases

# global dictionaries and lists
busToEstDict = {}
estToBusDict = {}
plotPairDict = {}
busToMeasDict = {}
estToMeasDict = {}
estToVnomMagDict = {}
estToVnomAngDict = {}
simAllDataDict = {}
senAllDataDict = {}

tsDataList = []
tsDataPausedList = []
estDataDict = {}
estDataPausedDict = {}
measDataDict = {}
measDataPausedDict = {}
diffDataDict = {}
diffDataPausedDict = {}
estLinesDict = {}
measLinesDict = {}
diffLinesDict = {}
estLegendLineList = []
estLegendLabelList = []
measLegendLineList = []
measLegendLabelList = []
plotPhaseList = []

# global variables
gapps = None
appName = None
simID = None
modelMRID = None
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
sensorSimulatorRunningFlag = False
useSensorsForEstimatesFlag = False
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
uiEstAx = None
uiEstZoomSldr = None
uiEstPanSldr = None
uiMeasAx = None
uiMeasZoomSldr = None
uiMeasPanSldr = None
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
                if busup in busToMeasDict:
                    measList = busToMeasDict[busup]
                    measList.append(meas['mRID'])
                    busToMeasDict[busup] = measList
                else:
                    measList = [meas['mRID']]
                    busToMeasDict[busup] = measList

    print(appName + ': start bus to measurement mrid query results...', flush=True)
    pprint.pprint(busToMeasDict)
    print(appName + ': end bus to measurement mrid query results', flush=True)


def mapEstToMeas():
    estMatchCount = 0

    for busname, measList in busToMeasDict.items():
        bus, phase = busname.split('.')
        if bus in busToEstDict:
            estMatchCount += 1
            estmrid = busToEstDict[bus]
            if phase == '1':
                estToMeasDict[estmrid+',A'] = measList
            elif phase == '2':
                estToMeasDict[estmrid+',B'] = measList
            elif phase == '3':
                estToMeasDict[estmrid+',C'] = measList
    print(appName + ': start estimate to measurement mrid mapping...', flush=True)
    pprint.pprint(estToMeasDict)
    print(appName + ': end estimate to measurement mrid mapping', flush=True)

    print(appName + ': ' + str(estMatchCount) + ' estimate node,phase pair matches out of ' + str(len(busToMeasDict)) + ' total measurement mrids', flush=True)


def mapEstToVnomMag(estmrid, phase, magnitude):
    if phase == 1:
        estToVnomMagDict[estmrid+',A'] = magnitude
    elif phase == 2:
        estToVnomMagDict[estmrid+',B'] = magnitude
    elif phase == 3:
        estToVnomMagDict[estmrid+',C'] = magnitude


def mapEstToVnomAngle(estmrid, phase, angle):
    if phase == 1:
        estToVnomAngDict[estmrid+',A'] = angle
    elif phase == 2:
        estToVnomAngDict[estmrid+',B'] = angle
    elif phase == 3:
        estToVnomAngDict[estmrid+',C'] = angle


def queryVnom():
    vnomRequestText = '{"configurationType":"Vnom Export","parameters":{"simulation_id":"' + simID + '"}}';
    vnomResponse = gapps.get_response('goss.gridappsd.process.request.config', vnomRequestText, timeout=1200)
    # use busToEstDict dictionary to map to estpair (node,phase)

    if plotMagFlag:
        for line in vnomResponse['data']['vnom']:
            vnom = line.split(',')
            bus = vnom[0].strip('"')
            if bus in busToEstDict:
                estmrid = busToEstDict[bus]
                mapEstToVnomMag(estmrid, int(vnom[2]), float(vnom[3]))
                mapEstToVnomMag(estmrid, int(vnom[6]), float(vnom[7]))
                mapEstToVnomMag(estmrid, int(vnom[10]), float(vnom[11]))

        print(appName + ': start state-estimator to vnom magnitude mapping...', flush=True)
        pprint.pprint(estToVnomMagDict)
        print(appName + ': end state-estimator to vnom magnitude mapping', flush=True)

    else:
        for line in vnomResponse['data']['vnom']:
            vnom = line.split(',')
            bus = vnom[0].strip('"')
            if bus in busToEstDict:
                estmrid = busToEstDict[bus]
                mapEstToVnomAngle(estmrid, int(vnom[2]), float(vnom[4]))
                mapEstToVnomAngle(estmrid, int(vnom[6]), float(vnom[8]))
                mapEstToVnomAngle(estmrid, int(vnom[10]), float(vnom[12]))

        print(appName + ': start state-estimator to vnom angle mapping...', flush=True)
        pprint.pprint(estToVnomAngDict)
        print(appName + ': end state-estimator to vnom angle mapping', flush=True)


def vmagPrintWithMeas(ts, estpair, estvmag, measvmag, vmagdiff):
    if printDataFlag:
        print(appName + ', ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % mag diff: ' + str(vmagdiff), flush=True)
        # 13-node
        if modelMRID == '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F':
            if vmagdiff < -2.0:
                print(appName + ': OUTLIER, 13-node, vmagdiff<-2.0%: ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        # 123-node
        elif modelMRID == '_C1C3E687-6FFD-C753-582B-632A27E28507':
            if vmagdiff > 3.0:
                print(appName + ': OUTLIER, 123-node, vmagdiff>3.0%: ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % diff: ' + str(vmagdiff), flush=True)
            if vmagdiff < -2.5:
                print(appName + ': OUTLIER, 123-node, vmagdiff<-2.5%: ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        # 9500-node
        #elif modelMRID == '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44':


def vangPrintWithMeas(ts, estpair, estvang, measvang, vangdiff):
    if printDataFlag:
        print(appName + ', ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvang: ' + str(estvang) + ', measvang: ' + str(measvang) + ', diff: ' + str(vangdiff), flush=True)
        # 13-node
        if modelMRID == '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F':
            if vangdiff > 34.0:
                print(appName + ': OUTLIER, 13-node, vangdiff>34.0: ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvang: ' + str(estvang) + ', measvang: ' + str(measvang) + ', diff: ' + str(vangdiff), flush=True)
        # 123-node
        #elif modelMRID == '_C1C3E687-6FFD-C753-582B-632A27E28507':
        #    if vangdiff < -10.0:
        #        print(appName + ': OUTLIER, 123-node, vangdiff<-100.0: ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvang: ' + str(estvang) + ', measvang: ' + str(measvang) + ', diff: ' + str(vangdiff), flush=True)
        # 9500-node
        #elif modelMRID == '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44':


def vmagPrintWithoutMeas(ts, estpair, estvmag):
    if printDataFlag:
        print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvmag: ' + str(estvmag), flush=True)
        if modelMRID == '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F':
            if estvmag > 4000:
                print(appName + ': OUTLIER, 13-node, estvmag>4K: ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvmag > 4K: ' + str(estvmag), flush=True)


def vangPrintWithoutMeas(ts, estpair, estvang):
    if printDataFlag:
        print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', estpair: ' + estpair + ', busname: ' + estToBusDict[estpair] + ', estvang: ' + str(estvang), flush=True)


def calcVNom(vval, estpair):
    if plotMagFlag:
        if plotCompFlag and estpair in estToVnomMagDict:
            return vval / estToVnomMagDict[estpair]
    else:
        if plotCompFlag and estpair in estToVnomAngDict:
            vval -= estToVnomAngDict[estpair]
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
    # simulation and sensor dictionaries and toss all measurements until we
    # reach the current timestamp since they won't be referenced again and
    # will just drain memory
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

    if sensorSimulatorRunningFlag:
        senDataTS = None
        for tskey in list(senAllDataDict):
            if tskey < ts:
                del senAllDataDict[tskey]
            elif tskey == ts:
                senDataTS = senAllDataDict[tskey]
                break
            else:
                break

        if not senDataTS:
            print(appName + ': NOTE: No sensor measurement for timestamp: ' + str(ts) + ', disregarding estimate', flush=True)
            return

    # determine whether simulation or sensor data should be used for
    # the second plot
    if useSensorsForEstimatesFlag:
        measDataTS = senDataTS
    else:
        measDataTS = simDataTS

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    estpairCount = len(estVolt)

    # update the timestamp zoom slider upper limit and default value
    if firstPassFlag:
        # scale based on cube root of number of node/phase pairs
        # The multiplier is just a magic scaling factor that seems to produce
        # reasonable values for the 3 models used as test cases
        upper = 100 * (estpairCount**(1./3))
        #upper = 18 * (estpairCount**(1./3))
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
        estkey = 'v'
        measkey = 'magnitude'
    else:
        estkey = 'angle'
        measkey = 'angle'

    for item in estVolt:
        # only consider phases A, B, C
        phase = item['phase']
        if phase!='A' and phase!='B' and phase!='C':
            continue

        estpair = item['ConnectivityNode'] + ',' + phase

        if estpair in plotPairDict:
            estvval = item[estkey]
            estvval = calcVNom(estvval, estpair)

            #print(appName + ': node,phase pair: ' + estpair, flush=True)
            #print(appName + ': timestamp: ' + str(ts), flush=True)
            #print(appName + ': estvval: ' + str(estvval), flush=True)

            matchCount += 1

            measvval = None
            if not plotMatchesFlag:
                if matchCount == 1:
                    tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
                estDataPausedDict[estpair].append(estvval) if plotPausedFlag else estDataDict[estpair].append(estvval)
            if measDataTS is not None and estpair in estToMeasDict:
                for measmrid in estToMeasDict[estpair]:
                    if measmrid in measDataTS:
                        meas = measDataTS[measmrid]
                        if measkey in meas:
                            diffMatchCount += 1
                            if plotMatchesFlag:
                                if diffMatchCount == 1:
                                    tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
                                estDataPausedDict[estpair].append(estvval) if plotPausedFlag else estDataDict[estpair].append(estvval)
                            measvval = meas[measkey]
                            measvval = calcVNom(measvval, estpair)
                            measDataPausedDict[estpair].append(measvval) if plotPausedFlag else measDataDict[estpair].append(measvval)

                            if measmrid in simDataTS:
                                sim = simDataTS[measmrid]
                                if measkey in sim:
                                    simvval = sim[measkey]
                                    simvval = calcVNom(simvval, estpair)

                                    if not plotMagFlag:
                                        diffestvval = estvval - simvval
                                    elif simvval != 0.0:
                                        diffestvval = 100.0*(estvval - simvval)/simvval
                                    else:
                                        diffestvval = 0.0

                                    if not plotOverlayFlag:
                                        if plotMagFlag:
                                            diffDataPausedDict[estpair+' Est'].append(abs(diffestvval)) if plotPausedFlag else diffDataDict[estpair+' Est'].append(abs(diffestvval))
                                        else:
                                            diffDataPausedDict[estpair+' Est'].append(diffestvval) if plotPausedFlag else diffDataDict[estpair+' Est'].append(diffestvval)

                                    if sensorSimulatorRunningFlag and measmrid in senDataTS:
                                        sen = senDataTS[measmrid]
                                        if measkey in sen:
                                            senvval = sen[measkey]
                                            senvval = calcVNom(senvval, estpair)

                                            if not plotMagFlag:
                                                diffmeasvval = senvval - simvval
                                            elif simvval != 0.0:
                                                diffmeasvval = 100.0*(senvval - simvval)/simvval
                                            else:
                                                diffmeasvval = 0.0

                                            if not plotOverlayFlag:
                                                if plotMagFlag:
                                                    diffDataPausedDict[estpair+' Meas'].append(abs(diffmeasvval)) if plotPausedFlag else diffDataDict[estpair+' Meas'].append(abs(diffmeasvval))
                                                else:
                                                    diffDataPausedDict[estpair+' Meas'].append(diffmeasvval) if plotPausedFlag else diffDataDict[estpair+' Meas'].append(diffmeasvval)

                                    if plotMagFlag:
                                        vmagPrintWithMeas(ts, estpair, estvval, measvval, diffestvval)
                                    else:
                                        vangPrintWithMeas(ts, estpair, estvval, measvval, diffestvval)
                                    break

            if not measvval:
                if plotMagFlag:
                    vmagPrintWithoutMeas(ts, estpair, estvval)
                else:
                    vangPrintWithoutMeas(ts, estpair, estvval)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if not plotMatchesFlag and matchCount==len(plotPairDict):
                break
            elif plotMatchesFlag and diffMatchCount==len(plotPairDict):
                break

    #print(appName + ': ' + str(estpairCount) + ' state-estimator measurements, ' + str(matchCount) + ' configuration file node,phase pair matches, ' + str(diffMatchCount) + ' matches to measurement data', flush=True)

    # update plots with the new data
    plotData(None)


def estimateNoConfigCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    # to account for state estimator work queue draining design, iterate over
    # simulation and sensor dictionaries and toss all measurements until we
    # reach the current timestamp since they won't be referenced again and
    # will just drain memory
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

    if sensorSimulatorRunningFlag:
        senDataTS = None
        for tskey in list(senAllDataDict):
            if tskey < ts:
                del senAllDataDict[tskey]
            elif tskey == ts:
                senDataTS = senAllDataDict[tskey]
                break
            else:
                break

        if not senDataTS:
            print(appName + ': NOTE: No sensor measurement for timestamp: ' + str(ts) + ', disregarding estimate', flush=True)
            return

    # determine whether simulation or sensor data should be used for
    # the second plot
    if useSensorsForEstimatesFlag:
        measDataTS = senDataTS
    else:
        measDataTS = simDataTS

    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    diffMatchCount = 0
    estpairCount = len(estVolt)

    if firstPassFlag:
        # update the timestamp zoom slider upper limit and default value
        # scale based on cube root of number of node/phase pairs
        # The multiplier is just a magic scaling factor that seems to produce
        # reasonable values for the 3 models used as test cases
        upper = 100 * (estpairCount**(1./3))
        #upper = 18 * (estpairCount**(1./3))
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
        estkey = 'v'
        measkey = 'magnitude'
    else:
        estkey = 'angle'
        measkey = 'angle'

    for item in estVolt:
        # only consider phases A, B, C
        phase = item['phase']
        if phase!='A' and phase!='B' and phase!='C':
            continue

        estpair = item['ConnectivityNode'] + ',' + phase
        estvval = item[estkey]
        estvval = calcVNom(estvval, estpair)

        #print(appName + ': node,phase pair: ' + estpair + ', matchCount: ' + str(matchCount), flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': estvval: ' + str(estvval), flush=True)

        # only do the dictionary initializtion code on the first call
        if firstPassFlag:
            estDataDict[estpair] = []
            estDataPausedDict[estpair] = []
            measDataDict[estpair] = []
            measDataPausedDict[estpair] = []
            if not plotOverlayFlag:
                diffDataDict[estpair+' Est'] = []
                diffDataPausedDict[estpair+' Est'] = []
                if sensorSimulatorRunningFlag:
                    diffDataDict[estpair+' Meas'] = []
                    diffDataPausedDict[estpair+' Meas'] = []

            # create a lines dictionary entry per node/phase pair for each plot
            measLinesDict[estpair], = uiMeasAx.plot([], [], label=estToBusDict[estpair])

            if plotOverlayFlag:
                estLinesDict[estpair], = uiEstAx.plot([], [], label=estToBusDict[estpair], linestyle='--')

                diffLinesDict[estpair+' Actual'], = uiDiffAx.plot([], [], label=estToBusDict[estpair]+' Actual')
                color = diffLinesDict[estpair+' Actual'].get_color()
                diffLinesDict[estpair+' Est'], = uiDiffAx.plot([], [], label=estToBusDict[estpair]+' Est.', linestyle='--', color=color)
            else:
                estLinesDict[estpair], = uiEstAx.plot([], [], label=estToBusDict[estpair])

                diffLinesDict[estpair+' Est'], = uiDiffAx.plot([], [], label=estToBusDict[estpair]+' Est.', linestyle='--')
                if sensorSimulatorRunningFlag:
                    color = diffLinesDict[estpair+' Est'].get_color()
                    diffLinesDict[estpair+' Meas'], = uiDiffAx.plot([], [], label=estToBusDict[estpair]+' Meas.', color=color)

        # 123-node angle plots:
        #   phase A heads to -60 degrees right away
        #   phase B heads to -20 degrees around 500 seconds
        #   phase C stays around 0, ranging from 0 to 2.5 degrees away from
        #     the actual angle

        # Phase exclusion logic
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        matchCount += 1

        measvval = None
        if not plotMatchesFlag:
            if matchCount == 1:
                tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
            estDataPausedDict[estpair].append(estvval) if plotPausedFlag else estDataDict[estpair].append(estvval)
        if measDataTS is not None and estpair in estToMeasDict:
            for measmrid in estToMeasDict[estpair]:
                if measmrid in measDataTS:
                    meas = measDataTS[measmrid]
                    if measkey in meas:
                        diffMatchCount += 1
                        if plotMatchesFlag:
                            if diffMatchCount == 1:
                                tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)
                            estDataPausedDict[estpair].append(estvval) if plotPausedFlag else estDataDict[estpair].append(estvval)

                        measvval = meas[measkey]
                        measvval = calcVNom(measvval, estpair)
                        measDataPausedDict[estpair].append(measvval) if plotPausedFlag else measDataDict[estpair].append(measvval)

                        if measmrid in simDataTS:
                            sim = simDataTS[measmrid]
                            if measkey in sim:
                                simvval = sim[measkey]
                                simvval = calcVNom(simvval, estpair)

                                if not plotMagFlag:
                                    diffestvval = estvval - simvval
                                elif simvval != 0.0:
                                    diffestvval = 100.0*(estvval - simvval)/simvval
                                else:
                                    diffestvval = 0.0

                                if not plotOverlayFlag:
                                    if plotMagFlag:
                                        diffDataPausedDict[estpair+' Est'].append(abs(diffestvval)) if plotPausedFlag else diffDataDict[estpair+' Est'].append(abs(diffestvval))
                                    else:
                                        diffDataPausedDict[estpair+' Est'].append(diffestvval) if plotPausedFlag else diffDataDict[estpair+' Est'].append(diffestvval)

                                if sensorSimulatorRunningFlag and measmrid in senDataTS:
                                    sen = senDataTS[measmrid]
                                    if measkey in sen:
                                        senvval = sen[measkey]
                                        senvval = calcVNom(senvval, estpair)

                                        if not plotMagFlag:
                                            diffmeasvval = senvval - simvval
                                        elif simvval != 0.0:
                                            diffmeasvval = 100.0*(senvval - simvval)/simvval
                                        else:
                                            diffmeasvval = 0.0

                                        if not plotOverlayFlag:
                                            if plotMagFlag:
                                                diffDataPausedDict[estpair+' Meas'].append(abs(diffmeasvval)) if plotPausedFlag else diffDataDict[estpair+' Meas'].append(abs(diffmeasvval))
                                            else:
                                                diffDataPausedDict[estpair+' Meas'].append(diffmeasvval) if plotPausedFlag else diffDataDict[estpair+' Meas'].append(diffmeasvval)

                                if plotMagFlag:
                                    vmagPrintWithMeas(ts, estpair, estvval, measvval, diffestvval)
                                else:
                                    vangPrintWithMeas(ts, estpair, estvval, measvval, diffestvval)
                                break

        if not measvval:
            if plotMagFlag:
                vmagPrintWithoutMeas(ts, estpair, estvval)
            else:
                vangPrintWithoutMeas(ts, estpair, estvval)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if not plotMatchesFlag and plotNumber>0 and matchCount==plotNumber:
            break
        elif plotMatchesFlag and plotNumber>0 and diffMatchCount==plotNumber:
            break

    firstPassFlag = False

    #if plotNumber > 0:
    #    print(appName + ': ' + str(estpairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching first ' + str(plotNumber) + '), ' + str(diffMatchCount) + ' matches to measurement data', flush=True)
    #else:
    #    print(appName + ': ' + str(estpairCount) + ' state-estimator measurements, ' + str(matchCount) + ' node,phase pair matches (matching all), ' + str(diffMatchCount) + ' matches to measurement data', flush=True)

    # update plots with the new data
    plotData(None)


def estimateStatsCallback(header, message):
    global firstPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    # to account for state estimator work queue draining design, iterate over
    # simulation and sensor dictionaries and toss all measurements until we
    # reach the current timestamp since they won't be referenced again and
    # will just drain memory
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

    if sensorSimulatorRunningFlag:
        senDataTS = None
        for tskey in list(senAllDataDict):
            if tskey < ts:
                del senAllDataDict[tskey]
            elif tskey == ts:
                senDataTS = senAllDataDict[tskey]
                break
            else:
                break

        if not senDataTS:
            print(appName + ': NOTE: No sensor measurement for timestamp: ' + str(ts) + ', disregarding estimate', flush=True)
            return

    # determine whether simulation or sensor data should be used for
    # the second plot
    if useSensorsForEstimatesFlag:
        measDataTS = senDataTS
    else:
        measDataTS = simDataTS

    estVolt = msgdict['Estimate']['SvEstVoltages']
    estpairCount = len(estVolt)

    if firstPassFlag:
        # update the timestamp zoom slider upper limit and default value
        # scale based on cube root of number of node/phase pairs
        # The multiplier is just a magic scaling factor that seems to produce
        # reasonable values for the 3 models used as test cases
        upper = 100 * (estpairCount**(1./3))
        #upper = 18 * (estpairCount**(1./3))
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

        estDataDict['Min'] = []
        estDataDict['Max'] = []
        estDataDict['Mean'] = []
        estDataDict['Stdev Low'] = []
        estDataDict['Stdev High'] = []
        estDataPausedDict['Min'] = []
        estDataPausedDict['Max'] = []
        estDataPausedDict['Mean'] = []
        estDataPausedDict['Stdev Low'] = []
        estDataPausedDict['Stdev High'] = []
        measDataDict['Min'] = []
        measDataDict['Max'] = []
        measDataDict['Mean'] = []
        measDataDict['Stdev Low'] = []
        measDataDict['Stdev High'] = []
        measDataPausedDict['Min'] = []
        measDataPausedDict['Max'] = []
        measDataPausedDict['Mean'] = []
        measDataPausedDict['Stdev Low'] = []
        measDataPausedDict['Stdev High'] = []

        # create a lines dictionary entry per node/phase pair for each plot
        if plotOverlayFlag:
            estLinesDict['Min'], = uiEstAx.plot([], [], label='Minimum', linestyle='--', color='cyan')
            estLinesDict['Max'], = uiEstAx.plot([], [], label='Maximum', linestyle='--', color='cyan')
            estLinesDict['Stdev Low'], = uiEstAx.plot([], [], label='Std. Dev. Low', linestyle='--', color='blue')
            estLinesDict['Stdev High'], = uiEstAx.plot([], [], label='Std. Dev. High', linestyle='--', color='blue')
            estLinesDict['Mean'], = uiEstAx.plot([], [], label='Mean', linestyle='--', color='red')

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
            estLinesDict['Min'], = uiEstAx.plot([], [], label='Minimum', color='cyan')
            estLinesDict['Max'], = uiEstAx.plot([], [], label='Maximum', color='cyan')
            estLinesDict['Stdev Low'], = uiEstAx.plot([], [], label='Std. Dev. Low', color='blue')
            estLinesDict['Stdev High'], = uiEstAx.plot([], [], label='Std. Dev. High', color='blue')
            estLinesDict['Mean'], = uiEstAx.plot([], [], label='Mean', color='red')

            diffDataDict['Mean Est'] = []
            diffDataPausedDict['Mean Est'] = []
            if sensorSimulatorRunningFlag:
                diffDataDict['Mean Meas'] = []
                diffDataPausedDict['Mean Meas'] = []

            # hardwire colors to magenta and green specifically for this plot
            diffLinesDict['Mean Est'], = uiDiffAx.plot([], [], label='Mean Estimate Error', color='magenta')
            if sensorSimulatorRunningFlag:
                diffLinesDict['Mean Meas'], = uiDiffAx.plot([], [], label='Mean Measurement Error', color='green')

        measLinesDict['Min'], = uiMeasAx.plot([], [], label='Minimum', color='cyan')
        measLinesDict['Max'], = uiMeasAx.plot([], [], label='Maximum', color='cyan')
        measLinesDict['Stdev Low'], = uiMeasAx.plot([], [], label='Std. Dev. Low', color='blue')
        measLinesDict['Stdev High'], = uiMeasAx.plot([], [], label='Std. Dev. High', color='blue')
        measLinesDict['Mean'], = uiMeasAx.plot([], [], label='Mean', color='red')

    if firstPassFlag:
        # save first timestamp so what we plot is an offset from this
        tsInit = ts
        firstPassFlag = False

    # set the data element keys we want to extract
    if plotMagFlag:
        estkey = 'v'
        measkey = 'magnitude'
    else:
        estkey = 'angle'
        measkey = 'angle'

    estlist = []
    measlist = []
    diffestlist = []
    if sensorSimulatorRunningFlag:
        diffmeaslist = []

    for item in estVolt:
        # only consider phases A, B, C and user-specified phases
        phase = item['phase']
        if phase!='A' and phase!='B' and phase!='C' or \
           len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        estpair = item['ConnectivityNode'] + ',' + phase
        estvval = item[estkey]
        estvval = calcVNom(estvval, estpair)

        #print(appName + ': node,phase pair: ' + estpair, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': estvval: ' + str(estvval), flush=True)

        measvval = None
        if not plotMatchesFlag:
            estlist.append(estvval)
        if measDataTS is not None and estpair in estToMeasDict:
            for measmrid in estToMeasDict[estpair]:
                if measmrid in measDataTS:
                    meas = measDataTS[measmrid]
                    if measkey in meas:
                        if plotMatchesFlag:
                            estlist.append(estvval)

                        measvval = meas[measkey]
                        measvval = calcVNom(measvval, estpair)
                        measlist.append(measvval)

                        if measmrid in simDataTS:
                            sim = simDataTS[measmrid]
                            if measkey in sim:
                                simvval = sim[measkey]
                                simvval = calcVNom(simvval, estpair)

                                if not plotMagFlag:
                                    diffestvval = estvval - simvval
                                elif simvval != 0.0:
                                    diffestvval = 100.0*(estvval - simvval)/simvval
                                else:
                                    diffestvval = 0.0

                                if not plotOverlayFlag:
                                    if plotMagFlag:
                                        diffestlist.append(abs(diffestvval))
                                    else:
                                        diffestlist.append(diffestvval)

                                if sensorSimulatorRunningFlag and measmrid in senDataTS:
                                    sen = senDataTS[measmrid]
                                    if measkey in sen:
                                        senvval = sen[measkey]
                                        senvval = calcVNom(senvval, estpair)

                                        if not plotMagFlag:
                                            diffmeasvval = senvval - simvval
                                        elif simvval != 0.0:
                                            diffmeasvval = 100.0*(senvval - simvval)/simvval
                                        else:
                                            diffmeasvval = 0.0

                                        if not plotOverlayFlag:
                                            if plotMagFlag:
                                                diffmeaslist.append(abs(diffmeasvval))
                                            else:
                                                diffmeaslist.append(diffmeasvval)

                                if plotMagFlag:
                                    vmagPrintWithMeas(ts, estpair, estvval, measvval, diffestvval)
                                else:
                                    vangPrintWithMeas(ts, estpair, estvval, measvval, diffestvval)
                                break

        if not measvval:
            if plotMagFlag:
                vmagPrintWithoutMeas(ts, estpair, estvval)
            else:
                vangPrintWithoutMeas(ts, estpair, estvval)

    tsDataPausedList.append(ts - tsInit) if plotPausedFlag else tsDataList.append(ts - tsInit)

    estmin = min(estlist)
    estmax = max(estlist)
    estmean = statistics.mean(estlist)
    eststdev = statistics.pstdev(estlist, estmean)
    estDataPausedDict['Min'].append(estmin) if plotPausedFlag else estDataDict['Min'].append(estmin)
    estDataPausedDict['Max'].append(estmax) if plotPausedFlag else estDataDict['Max'].append(estmax)
    estDataPausedDict['Mean'].append(estmean) if plotPausedFlag else estDataDict['Mean'].append(estmean)
    estDataPausedDict['Stdev Low'].append(estmean-eststdev) if plotPausedFlag else estDataDict['Stdev Low'].append(estmean-eststdev)
    estDataPausedDict['Stdev High'].append(estmean+eststdev) if plotPausedFlag else estDataDict['Stdev High'].append(estmean+eststdev)

    if len(measlist) > 0:
        measmin = min(measlist)
        measmax = max(measlist)
        measmean = statistics.mean(measlist)
        measstdev = statistics.pstdev(measlist, measmean)
        measDataPausedDict['Min'].append(measmin) if plotPausedFlag else measDataDict['Min'].append(measmin)
        measDataPausedDict['Max'].append(measmax) if plotPausedFlag else measDataDict['Max'].append(measmax)
        measDataPausedDict['Mean'].append(measmean) if plotPausedFlag else measDataDict['Mean'].append(measmean)
        measDataPausedDict['Stdev Low'].append(measmean-measstdev) if plotPausedFlag else measDataDict['Stdev Low'].append(measmean-measstdev)
        measDataPausedDict['Stdev High'].append(measmean+measstdev) if plotPausedFlag else measDataDict['Stdev High'].append(measmean+measstdev)

    if not plotOverlayFlag:
        if len(diffestlist) > 0:
            diffestmean = statistics.mean(diffestlist)
            diffDataPausedDict['Mean Est'].append(diffestmean) if plotPausedFlag else diffDataDict['Mean Est'].append(diffestmean)
            if plotMagFlag:
                print(appName + ': mean magnitude % diff estimate: ' + str(diffestmean), flush=True)
            else:
                print(appName + ': mean angle diff estimate: ' + str(diffestmean), flush=True)

        if sensorSimulatorRunningFlag and len(diffmeaslist)>0:
            diffmeasmean = statistics.mean(diffmeaslist)
            diffDataPausedDict['Mean Meas'].append(diffmeasmean) if plotPausedFlag else diffDataDict['Mean Meas'].append(diffmeasmean)
            if plotMagFlag:
                print(appName + ': mean magnitude % diff measurement: ' + str(diffmeasmean), flush=True)
            else:
                print(appName + ': mean angle diff measurement: ' + str(diffmeasmean), flush=True)

    # update plots with the new data
    plotData(None)


def simulationCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': meaurement message timestamp: ' + str(ts), flush=True)
    print('<', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    simAllDataDict[ts] = msgdict['measurements']


def sensorCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': meaurement message timestamp: ' + str(ts), flush=True)
    print('>', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    senAllDataDict[ts] = msgdict['measurements']


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
    # lines, or 2 points, since single points don't show up and that little
    # optimization keeps the plots from jumping around at the start before
    # there is anything useful to look at
    if len(tsDataList) < 2:
        return

    measDataFlag = False
    diffDataFlag = False

    if plotShowAllFlag:
        xupper = int(tsDataList[-1])
        if xupper > 0:
            uiEstAx.set_xlim(0, xupper)

        estYmax = -sys.float_info.max
        estYmin = sys.float_info.max
        for pair in estDataDict:
            if len(estDataDict[pair]) > 0:
                if len(estDataDict[pair]) != len(tsDataList):
                    print('***MISMATCH Estimate show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(estDataDict[pair])), flush=True)
                estLinesDict[pair].set_xdata(tsDataList)
                estLinesDict[pair].set_ydata(estDataDict[pair])
                estYmin = min(estYmin, min(estDataDict[pair]))
                estYmax = max(estYmax, max(estDataDict[pair]))
                if firstPlotFlag and len(plotPairDict)>0:
                    estLegendLineList.append(estLinesDict[pair])
                    estLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': estYmin: ' + str(estYmin) + ', estYmax: ' + str(estYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiEstAx)
            if len(estDataDict['Mean']) > 0:
                if len(estDataDict['Mean']) != len(tsDataList):
                    print('***MISMATCH Estimate show all statistics, xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(estDataDict['Mean'])), flush=True)
                plt.fill_between(x=tsDataList, y1=estDataDict['Mean'], y2=estDataDict['Stdev Low'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=estDataDict['Mean'], y2=estDataDict['Stdev High'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=estDataDict['Stdev Low'], y2=estDataDict['Min'], color=minmaxBlue)
                plt.fill_between(x=tsDataList, y1=estDataDict['Stdev High'], y2=estDataDict['Max'], color=minmaxBlue)

        measYmax = -sys.float_info.max
        measYmin = sys.float_info.max
        for pair in measDataDict:
            if len(measDataDict[pair]) > 0:
                measDataFlag = True
                if len(measDataDict[pair]) != len(tsDataList):
                    print('***MISMATCH Measurement show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(measDataDict[pair])), flush=True)
                measLinesDict[pair].set_xdata(tsDataList)
                measLinesDict[pair].set_ydata(measDataDict[pair])
                measYmin = min(measYmin, min(measDataDict[pair]))
                measYmax = max(measYmax, max(measDataDict[pair]))
                if firstPlotFlag and len(plotPairDict)>0:
                    measLegendLineList.append(measLinesDict[pair])
                    measLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': measYmin: ' + str(measYmin) + ', measYmax: ' + str(measYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiMeasAx)
            if len(measDataDict['Mean']) > 0:
                if len(measDataDict['Mean']) != len(tsDataList):
                    print('***MISMATCH Measurement show all statistics, xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(measDataDict['Mean'])), flush=True)
                plt.fill_between(x=tsDataList, y1=measDataDict['Mean'], y2=measDataDict['Stdev Low'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=measDataDict['Mean'], y2=measDataDict['Stdev High'], color=stdevBlue)
                plt.fill_between(x=tsDataList, y1=measDataDict['Stdev Low'], y2=measDataDict['Min'], color=minmaxBlue)
                plt.fill_between(x=tsDataList, y1=measDataDict['Stdev High'], y2=measDataDict['Max'], color=minmaxBlue)

        diffYmax = -sys.float_info.max
        diffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in estDataDict:
                if len(estDataDict[pair]) > 0:
                    if len(estDataDict[pair]) != len(tsDataList):
                        print('***MISMATCH Difference Estimate show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(estDataDict[pair])), flush=True)
                    diffLinesDict[pair+' Est'].set_xdata(tsDataList)
                    diffLinesDict[pair+' Est'].set_ydata(estDataDict[pair])
                    diffYmin = min(diffYmin, min(estDataDict[pair]))
                    diffYmax = max(diffYmax, max(estDataDict[pair]))

                if len(measDataDict[pair]) > 0:
                    if len(measDataDict[pair]) != len(tsDataList):
                        print('***MISMATCH Difference Measurement show all pair: ' + pair + ', xdata #: ' + str(len(tsDataList)) + ', ydata #: ' + str(len(measDataDict[pair])), flush=True)
                    diffLinesDict[pair+' Actual'].set_xdata(tsDataList)
                    diffLinesDict[pair+' Actual'].set_ydata(measDataDict[pair])
                    diffYmin = min(diffYmin, min(measDataDict[pair]))
                    diffYmax = max(diffYmax, max(measDataDict[pair]))

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

        uiEstAx.set_xlim(tsXmin, tsXmax)
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

        estYmax = -sys.float_info.max
        estYmin = sys.float_info.max
        for pair in estDataDict:
            if len(estDataDict[pair][tsStartpt:tsEndpt]) > 0:
                if len(estDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Estimate pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(estDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                estLinesDict[pair].set_xdata(tsDataList[tsStartpt:tsEndpt])
                estLinesDict[pair].set_ydata(estDataDict[pair][tsStartpt:tsEndpt])
                estYmin = min(estYmin, min(estDataDict[pair][tsStartpt:tsEndpt]))
                estYmax = max(estYmax, max(estDataDict[pair][tsStartpt:tsEndpt]))
                if firstPlotFlag and len(plotPairDict)>0:
                    estLegendLineList.append(estLinesDict[pair])
                    estLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': estYmin: ' + str(estYmin) + ', estYmax: ' + str(estYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiEstAx)
            if len(estDataDict['Mean'][tsStartpt:tsEndpt]) > 0:
                if len(estDataDict['Mean'][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Estimate statistics, xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(estDataDict['Mean'][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=estDataDict['Mean'][tsStartpt:tsEndpt], y2=estDataDict['Stdev Low'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=estDataDict['Mean'][tsStartpt:tsEndpt], y2=estDataDict['Stdev High'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=estDataDict['Stdev Low'][tsStartpt:tsEndpt], y2=estDataDict['Min'][tsStartpt:tsEndpt], color=minmaxBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=estDataDict['Stdev High'][tsStartpt:tsEndpt], y2=estDataDict['Max'][tsStartpt:tsEndpt], color=minmaxBlue)

        measYmax = -sys.float_info.max
        measYmin = sys.float_info.max
        for pair in measDataDict:
            if len(measDataDict[pair][tsStartpt:tsEndpt]) > 0:
                measDataFlag = True
                if len(measDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Measurement pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(measDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                measLinesDict[pair].set_xdata(tsDataList[tsStartpt:tsEndpt])
                measLinesDict[pair].set_ydata(measDataDict[pair][tsStartpt:tsEndpt])
                measYmin = min(measYmin, min(measDataDict[pair][tsStartpt:tsEndpt]))
                measYmax = max(measYmax, max(measDataDict[pair][tsStartpt:tsEndpt]))
                if firstPlotFlag and len(plotPairDict)>0:
                    measLegendLineList.append(measLinesDict[pair])
                    measLegendLabelList.append(plotPairDict[pair])
        #print(appName + ': measYmin: ' + str(measYmin) + ', measYmax: ' + str(measYmax), flush=True)

        if plotStatsFlag:
            plt.sca(uiMeasAx)
            if len(measDataDict['Mean'][tsStartpt:tsEndpt]) > 0:
                if len(measDataDict['Mean'][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                    print('***MISMATCH Measurement statistics, xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(measDataDict['Mean'][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=measDataDict['Mean'][tsStartpt:tsEndpt], y2=measDataDict['Stdev Low'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=measDataDict['Mean'][tsStartpt:tsEndpt], y2=measDataDict['Stdev High'][tsStartpt:tsEndpt], color=stdevBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=measDataDict['Stdev Low'][tsStartpt:tsEndpt], y2=measDataDict['Min'][tsStartpt:tsEndpt], color=minmaxBlue)
                plt.fill_between(x=tsDataList[tsStartpt:tsEndpt], y1=measDataDict['Stdev High'][tsStartpt:tsEndpt], y2=measDataDict['Max'][tsStartpt:tsEndpt], color=minmaxBlue)

        diffYmax = -sys.float_info.max
        diffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in estDataDict:
                if len(estDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    if len(estDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                        print('***MISMATCH Difference Estimate pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(estDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                    diffLinesDict[pair+' Est'].set_xdata(tsDataList[tsStartpt:tsEndpt])
                    diffLinesDict[pair+' Est'].set_ydata(estDataDict[pair][tsStartpt:tsEndpt])
                    diffYmin = min(diffYmin, min(estDataDict[pair][tsStartpt:tsEndpt]))
                    diffYmax = max(diffYmax, max(estDataDict[pair][tsStartpt:tsEndpt]))

                if len(measDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    if len(measDataDict[pair][tsStartpt:tsEndpt]) != len(tsDataList[tsStartpt:tsEndpt]):
                        print('***MISMATCH Difference Measurement pair: ' + pair + ', xdata #: ' + str(len(tsDataList[tsStartpt:tsEndpt])) + ', ydata #: ' + str(len(measDataDict[pair][tsStartpt:tsEndpt])) + ', tsStartpt: ' + str(tsStartpt) + ', tsEndpt: ' + str(tsEndpt), flush=True)
                    diffLinesDict[pair+' Actual'].set_xdata(tsDataList[tsStartpt:tsEndpt])
                    diffLinesDict[pair+' Actual'].set_ydata(measDataDict[pair][tsStartpt:tsEndpt])
                    diffYmin = min(diffYmin, min(measDataDict[pair][tsStartpt:tsEndpt]))
                    diffYmax = max(diffYmax, max(measDataDict[pair][tsStartpt:tsEndpt]))

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
    newEstYmin, newEstYmax = yAxisLimits(estYmin, estYmax, uiEstZoomSldr.val, uiEstPanSldr.val)
    uiEstAx.set_ylim(newEstYmin, newEstYmax)
    uiEstAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiEstAx.grid(True)

    # measurement voltage value plot y-axis zoom and pan calculation
    if not measDataFlag:
        print(appName + ': NOTE: no measurement voltage value data to plot yet\n', flush=True)
    #print(appName + ': measurement voltage value y-axis limits...', flush=True)
    newMeasYmin, newMeasYmax = yAxisLimits(measYmin, measYmax, uiMeasZoomSldr.val, uiMeasPanSldr.val)
    uiMeasAx.set_ylim(newMeasYmin, newMeasYmax)
    uiMeasAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiMeasAx.grid(True)

    # voltage value difference plot y-axis zoom and pan calculation
    if not plotOverlayFlag and not diffDataFlag:
        print(appName + ': NOTE: no voltage value difference data to plot yet\n', flush=True)
    #print(appName + ': voltage value difference y-axis limits...', flush=True)
    newDiffYmin, newDiffYmax = yAxisLimits(diffYmin, diffYmax, uiDiffZoomSldr.val, uiDiffPanSldr.val)
    if not plotOverlayFlag and plotMagFlag:
        # always show 0% lower limit for magnitude % difference plots
        # when the upper limit drops below 1%, force it to 1%
        if newDiffYmax < 1.0:
            uiDiffAx.set_ylim(0.0, 1.0)
        else:
            uiDiffAx.set_ylim(0.0, newDiffYmax)
    else:
        uiDiffAx.set_ylim(newDiffYmin, newDiffYmax)
    uiDiffAx.xaxis.set_major_formatter(ticker.ScalarFormatter())
    uiDiffAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiDiffAx.grid(True)

    if firstPlotFlag:
        if plotStatsFlag:
            uiEstAx.legend()
            uiMeasAx.legend()
            uiDiffAx.legend()

        elif len(plotPairDict) > 0:
            if plotLegendFlag or len(estLegendLineList)<=10:
                cols = math.ceil(len(estLegendLineList)/8)
                uiEstAx.legend(estLegendLineList, estLegendLabelList, ncol=cols)

            if plotLegendFlag or len(measLegendLineList)<=10:
                cols = math.ceil(len(measLegendLineList)/8)
                uiMeasAx.legend(measLegendLineList, measLegendLabelList, ncol=cols)

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
        for pair in estDataDict:
            estDataDict[pair].extend(estDataPausedDict[pair])
            estDataPausedDict[pair].clear()
            measDataDict[pair].extend(measDataPausedDict[pair])
            measDataPausedDict[pair].clear()

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

    for line in uiEstAx.get_lines():
        if line.contains(event)[0]:
            lineFlag = True
            print(appName + ': clicked on estimate plot node: ' + line.get_label(), flush=True)

    for line in uiMeasAx.get_lines():
        if line.contains(event)[0]:
            lineFlag = True
            print(appName + ': clicked on measurement plot node: ' + line.get_label(), flush=True)

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


def queryBusToEst():
    connectivity_names_query = \
            'PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> ' + \
            'PREFIX c:  <http://iec.ch/TC57/CIM100#> ' + \
            'SELECT ?cnid ?cnname WHERE { ' + \
              '?term c:Terminal.ConnectivityNode ?cn. ' + \
              '?cn c:IdentifiedObject.mRID ?cnid. ' + \
              '?cn c:IdentifiedObject.name ?cnname. ' + \
              'VALUES ?fdrid {"' + modelMRID + '"}' + \
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
        busToEstDict[cnname] = cnid
        # add all possible pairs to speed lookup when printing diagnostics
        estToBusDict[cnid+',A'] = cnname+'.1'
        estToBusDict[cnid+',B'] = cnname+'.2'
        estToBusDict[cnid+',C'] = cnname+'.3'
    print(appName + ': start bus to estimate mrid query results...', flush=True)
    pprint.pprint(busToEstDict)
    print(appName + ': end bus to estimate mrid query results', flush=True)


def initPlot(configFlag):
    global uiTSZoomSldr, uiTSPanSldr
    global uiEstAx, uiEstZoomSldr, uiEstPanSldr
    global uiMeasAx, uiMeasZoomSldr, uiMeasPanSldr
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

    uiMeasAx = plotFig.add_subplot(311)
    uiMeasAx.xaxis.set_major_locator(MaxNLocator(integer=True))
    # shrink the margins, especially the top since we don't want a label
    plt.subplots_adjust(bottom=0.09, left=0.08, right=0.96, top=0.98, hspace=0.1)

    if useSensorsForEstimatesFlag:
        yLabelPrefix = 'Sensor ';
    else:
        yLabelPrefix = 'Simulated ';

    # measurement y-axis labels
    if plotMagFlag:
        if plotCompFlag:
            plt.ylabel(yLabelPrefix+'Volt. Mag. (p.u.)')
        else:
            plt.ylabel(yLabelPrefix+'Volt. Mag. (V)')
    else:
        plt.ylabel(yLabelPrefix+'Volt. Angle (deg.)')
    plt.setp(uiMeasAx.get_xticklabels(), visible=False)
    uiMeasAx.yaxis.set_major_formatter(ticker.NullFormatter())

    uiEstAx = plotFig.add_subplot(312, sharex=uiMeasAx)
    # state estimator y-axis labels
    if plotMagFlag:
        if plotCompFlag:
            plt.ylabel('Est. Volt. Mag. (p.u.)')
        else:
            plt.ylabel('Est. Volt. Mag. (V)')
    else:
        plt.ylabel('Est. Volt. Angle (deg.)')
    # make time axis numbers invisible because the bottom plot will have them
    plt.setp(uiEstAx.get_xticklabels(), visible=False)
    uiEstAx.yaxis.set_major_formatter(ticker.NullFormatter())

    uiDiffAx = plotFig.add_subplot(313, sharex=uiMeasAx)
    plt.xlabel('Time (s)')
    if plotOverlayFlag:
        # overlay plot y-axis labels
        if plotMagFlag:
            if plotCompFlag:
                plt.ylabel(yLabelPrefix+'& Est. Mag. (p.u.)')
            else:
                plt.ylabel(yLabelPrefix+'& Est. Mag. (V)')
        else:
            plt.ylabel(yLabelPrefix+'& Est. Angle (deg.)')
    else:
        # difference plot y-axis labels
        if plotMagFlag:
            plt.ylabel('Volt. Mag. Abs. % Diff.')
        else:
            plt.ylabel('Difference (deg.)')
    uiDiffAx.xaxis.set_major_formatter(ticker.NullFormatter())
    uiDiffAx.yaxis.set_major_formatter(ticker.NullFormatter())

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

    # measurement voltage value slice zoom and pan sliders
    uiMeasZoomAx = plt.axes([0.97, 0.87, 0.012, 0.09])
    uiMeasZoomSldr = Slider(uiMeasZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    uiMeasZoomSldr.on_changed(plotDataCallback)

    uiMeasPanAx = plt.axes([0.97, 0.72, 0.012, 0.09])
    uiMeasPanSldr = Slider(uiMeasPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    uiMeasPanSldr.on_changed(plotDataCallback)

    # state-estimator voltage value slice zoom and pan sliders
    uiEstZoomAx = plt.axes([0.97, 0.56, 0.012, 0.09])
    uiEstZoomSldr = Slider(uiEstZoomAx, '  zoom', 1, 100, valinit=100, valfmt='%d', valstep=1.0, orientation='vertical')
    uiEstZoomSldr.on_changed(plotDataCallback)

    uiEstPanAx = plt.axes([0.97, 0.41, 0.012, 0.09])
    uiEstPanSldr = Slider(uiEstPanAx, 'pan', 0, 100, valinit=50, valfmt='%d', valstep=1.0, orientation='vertical')
    uiEstPanSldr.on_changed(plotDataCallback)

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
                if bus in busToEstDict:
                    plotPairDict[busToEstDict[bus] + ',' + phase] = buspair
            else:
                if buspair+'.1' in busToMeasDict:
                    plotPairDict[busToEstDict[buspair]+',A'] = buspair+',A'
                if buspair+'.2' in busToMeasDict:
                    plotPairDict[busToEstDict[buspair]+',B'] = buspair+',B'
                if buspair+'.3' in busToMeasDict:
                    plotPairDict[busToEstDict[buspair]+',C'] = buspair+',C'
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
                        if bus in busToEstDict:
                            plotPairDict[busToEstDict[bus] + ',' + phase] = buspair
                    else:
                        if buspair+'.1' in busToMeasDict:
                            plotPairDict[busToEstDict[buspair]+',A'] = buspair+',A'
                        if buspair+'.2' in busToMeasDict:
                            plotPairDict[busToEstDict[buspair]+',B'] = buspair+',B'
                        if buspair+'.3' in busToMeasDict:
                            plotPairDict[busToEstDict[buspair]+',C'] = buspair+',C'
            #print(appName + ': ' + str(plotPairDict), flush=True)
        except:
            print(appName + ': ERROR: node/phase pair configuration file state-plotter-config.csv does not exist.\n', flush=True)
            exit()

    for pair in plotPairDict:
        # create empty lists for the per pair data for each plot so we can
        # just do append calls when data to plot arrives
        estDataDict[pair] = []
        estDataPausedDict[pair] = []
        measDataDict[pair] = []
        measDataPausedDict[pair] = []

        if not plotOverlayFlag:
            diffDataDict[pair+' Est'] = []
            diffDataPausedDict[pair+' Est'] = []
            if sensorSimulatorRunningFlag:
                diffDataDict[pair+' Meas'] = []
                diffDataPausedDict[pair+' Meas'] = []

        # create a lines dictionary entry per node/phase pair for each plot
        measLinesDict[pair], = uiMeasAx.plot([], [], label=plotPairDict[pair])

        if plotOverlayFlag:
            estLinesDict[pair], = uiEstAx.plot([], [], label=plotPairDict[pair], linestyle='--')

            diffLinesDict[pair+' Actual'], = uiDiffAx.plot([], [], label=plotPairDict[pair]+' Actual')
            color = diffLinesDict[pair+' Actual'].get_color()
            diffLinesDict[pair+' Est'], = uiDiffAx.plot([], [], label=plotPairDict[pair]+' Est.', linestyle='--', color=color)
        else:
            estLinesDict[pair], = uiEstAx.plot([], [], label=plotPairDict[pair])

            diffLinesDict[pair+' Est'], = uiDiffAx.plot([], [], label=plotPairDict[pair]+' Est.', linestyle='--')
            if sensorSimulatorRunningFlag:
                color = diffLinesDict[pair+' Est'].get_color()
                diffLinesDict[pair+' Meas'], = uiDiffAx.plot([], [], label=plotPairDict[pair]+' Meas.', color=color)


def _main():
    global appName, simID, modelMRID, gapps
    global plotTitle, plotNumber, plotMagFlag, plotCompFlag, printDataFlag
    global plotStatsFlag, plotOverlayFlag, plotLegendFlag, plotMatchesFlag
    global sensorSimulatorRunningFlag, useSensorsForEstimatesFlag

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

    # interrogate simReq to determine whether to subscribe to the sensor-
    # simulator service or to simulation output measurements
    simDict = json.loads(simReq)
    modelMRID = simDict['power_system_config']['Line_name']

    for jsc in simDict['service_configs']:
        if jsc['id'] == 'gridappsd-sensor-simulator':
            sensorSimulatorRunningFlag = True
        elif jsc['id'] == 'state-estimator':
            useSensorsForEstimatesFlag = jsc['user_options']['use-sensors-for-estimates']

    if not sensorSimulatorRunningFlag:
        useSensorsForEstimatesFlag = False

    # subscribe as early as possible to simulation and sensor measurements
    # to avoid getting any estimates without corresponding measurements for
    # a timestamp
    gapps.subscribe('/topic/goss.gridappsd.simulation.output.' +
                    simID, simulationCallback)

    if sensorSimulatorRunningFlag:
        gapps.subscribe('/topic/goss.gridappsd.simulation.'+
                   'gridappsd-sensor-simulator.'+simID+'.output',sensorCallback)

    # query to get connectivity node,phase pairs
    queryBusToEst()

    # query to get bus to sensor mrid mapping
    queryBusToSim()

    # finally, create map between estimate and measurement output
    mapEstToMeas()

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

