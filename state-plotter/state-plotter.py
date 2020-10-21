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
from gridappsd.topics import simulation_output_topic, service_output_topic


# requires matplotlib 3.1.0+ for vertical sliders
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.widgets import Slider
from matplotlib.widgets import Button
from matplotlib.widgets import CheckButtons
from matplotlib.ticker import MaxNLocator
from matplotlib import backend_bases

# global dictionaries and lists
busToMeasDict = {}
measToBusDict = {}
busToEstDict = {}
estToBusDict = {}
busToVnomMagDict = {}
busToVnomAngDict = {}
plotBusDict = {}
simAllDataDict = {}
senAllDataDict = {}

measDataDict = {}
measDataPausedDict = {}
estDataDict = {}
estDataPausedDict = {}
diffMeasDataDict = {}
diffMeasDataPausedDict = {}
diffEstDataDict = {}
diffEstDataPausedDict = {}

tsMeasDataDict = {}
tsMeasDataPausedDict = {}
tsEstDataDict = {}
tsEstDataPausedDict = {}
tsDiffMeasDataDict = {}
tsDiffMeasDataPausedDict = {}
tsDiffEstDataDict = {}
tsDiffEstDataPausedDict = {}

measLinesDict = {}
estLinesDict = {}
diffMeasLinesDict = {}
diffEstLinesDict = {}
measLegendLineList = []
measLegendLabelList = []
estLegendLineList = []
estLegendLabelList = []
plotPhaseList = []

# global variables
gapps = None
appName = None
simID = None
modelMRID = None
tsInit = 0
estDiffYmax = -sys.float_info.max
estDiffYmin = sys.float_info.max
measDiffYmax = -sys.float_info.max
measDiffYmin = sys.float_info.max
plotMagFlag = True
plotCompFlag = True
plotStatsFlag = True
plotSimAllFlag = False
plotPausedFlag = False
plotShowAllFlag = False
firstMeasurementPassFlag = True
firstSensorPassFlag = True
firstEstimatePassFlag = True
plotOverlayFlag = False
plotLegendFlag = False
plotMatchesFlag = True
printDataFlag = False
sensorSimulatorRunningFlag = False
useSensorsForEstimatesFlag = False
plotNumber = 0

plotFig = None
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
                buspair = meas['ConnectivityNode'] + ',' + meas['phases']
                buspair = buspair.upper()

                if buspair in busToMeasDict:
                    measList = busToMeasDict[buspair]
                    measList.append(meas['mRID'])
                    busToMeasDict[buspair] = measList
                    for measmrid in measList:
                        measToBusDict[measmrid] = buspair
                else:
                    measList = [meas['mRID']]
                    busToMeasDict[buspair] = measList
                    measToBusDict[meas['mRID']] = buspair

    print(appName + ': start bus to measurement mrid query results...', flush=True)
    pprint.pprint(busToMeasDict)
    print(appName + ': end bus to measurement mrid query results', flush=True)


def mapBusToVnomMag(bus, phase, magnitude):
    if phase == 1:
        busToVnomMagDict[bus+',A'] = magnitude
        busToVnomMagDict[bus+',S1'] = magnitude
    elif phase == 2:
        busToVnomMagDict[bus+',B'] = magnitude
        busToVnomMagDict[bus+',S2'] = magnitude
    elif phase == 3:
        busToVnomMagDict[bus+',C'] = magnitude


def mapBusToVnomAngle(bus, phase, angle):
    if phase == 1:
        busToVnomAngDict[bus+',A'] = angle
        busToVnomAngDict[bus+',S1'] = angle
    elif phase == 2:
        busToVnomAngDict[bus+',B'] = angle
        busToVnomAngDict[bus+',S2'] = angle
    elif phase == 3:
        busToVnomAngDict[bus+',C'] = angle


def queryVnom():
    vnomRequestText = '{"configurationType":"Vnom Export","parameters":{"simulation_id":"' + simID + '"}}';
    vnomResponse = gapps.get_response('goss.gridappsd.process.request.config', vnomRequestText, timeout=1200)

    lineCount = 0

    if plotMagFlag:
        for line in vnomResponse['data']['vnom']:
            lineCount += 1
            # skip header line
            if lineCount == 1:
                continue

            vnom = line.split(',')
            bus = vnom[0].strip('"')

            mapBusToVnomMag(bus, int(vnom[2]), float(vnom[3]))
            mapBusToVnomMag(bus, int(vnom[6]), float(vnom[7]))
            mapBusToVnomMag(bus, int(vnom[10]), float(vnom[11]))

        print(appName + ': start bus,phase to vnom magnitude mapping...', flush=True)
        pprint.pprint(busToVnomMagDict)
        print(appName + ': end bus,phase to vnom magnitude mapping', flush=True)

    else:
        for line in vnomResponse['data']['vnom']:
            lineCount += 1
            # skip header line
            if lineCount == 1:
                continue

            vnom = line.split(',')
            bus = vnom[0].strip('"')

            mapBusToVnomAngle(bus, int(vnom[2]), float(vnom[4]))
            mapBusToVnomAngle(bus, int(vnom[6]), float(vnom[8]))
            mapBusToVnomAngle(bus, int(vnom[10]), float(vnom[12]))

        print(appName + ': start bus,phase to vnom angle mapping...', flush=True)
        pprint.pprint(busToVnomAngDict)
        print(appName + ': end bus,phase to vnom angle mapping', flush=True)


def vmagPrintWithMeas(ts, buspair, estvmag, measvmag, vmagdiff):
    if printDataFlag:
        print(appName + ', ts: ' + str(ts) + ', buspair: ' + buspair + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % mag diff: ' + str(vmagdiff), flush=True)
        # 13-node
        if modelMRID == '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F':
            if vmagdiff < -2.0:
                print(appName + ': OUTLIER, 13-node, vmagdiff<-2.0%: ts: ' + str(ts) + ', buspair: ' + buspair + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        # 123-node
        elif modelMRID == '_C1C3E687-6FFD-C753-582B-632A27E28507':
            if vmagdiff > 3.0:
                print(appName + ': OUTLIER, 123-node, vmagdiff>3.0%: ts: ' + str(ts) + ', buspair: ' + buspair + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % diff: ' + str(vmagdiff), flush=True)
            if vmagdiff < -2.5:
                print(appName + ': OUTLIER, 123-node, vmagdiff<-2.5%: ts: ' + str(ts) + ', buspair: ' + buspair + ', estvmag: ' + str(estvmag) + ', measvmag: ' + str(measvmag) + ', % diff: ' + str(vmagdiff), flush=True)
        # 9500-node
        #elif modelMRID == '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44':


def vangPrintWithMeas(ts, buspair, estvang, measvang, vangdiff):
    if printDataFlag:
        print(appName + ', ts: ' + str(ts) + ', buspair: ' + buspair + ', estvang: ' + str(estvang) + ', measvang: ' + str(measvang) + ', diff: ' + str(vangdiff), flush=True)
        # 13-node
        if modelMRID == '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F':
            if vangdiff > 34.0:
                print(appName + ': OUTLIER, 13-node, vangdiff>34.0: ts: ' + str(ts) + ', buspair: ' + buspair + ', estvang: ' + str(estvang) + ', measvang: ' + str(measvang) + ', diff: ' + str(vangdiff), flush=True)
        # 123-node
        #elif modelMRID == '_C1C3E687-6FFD-C753-582B-632A27E28507':
        #    if vangdiff < -10.0:
        #        print(appName + ': OUTLIER, 123-node, vangdiff<-100.0: ts: ' + str(ts) + ', buspair: ' + buspair + ', estvang: ' + str(estvang) + ', measvang: ' + str(measvang) + ', diff: ' + str(vangdiff), flush=True)
        # 9500-node
        #elif modelMRID == '_AAE94E4A-2465-6F5E-37B1-3E72183A4E44':


def vmagPrintWithoutMeas(ts, buspair, estvmag):
    if printDataFlag:
        print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', buspair: ' + buspair + ', estvmag: ' + str(estvmag), flush=True)
        if modelMRID == '_5B816B93-7A5F-B64C-8460-47C17D6E4B0F':
            if estvmag > 4000:
                print(appName + ': OUTLIER, 13-node, estvmag>4K: ts: ' + str(ts) + ', buspair: ' + buspair + ', estvmag > 4K: ' + str(estvmag), flush=True)


def vangPrintWithoutMeas(ts, buspair, estvang):
    if printDataFlag:
        print(appName + ', NO SIM MATCH, ts: ' + str(ts) + ', buspair: ' + buspair + ', estvang: ' + str(estvang), flush=True)


def calcBusVNom(vval, buspair):
    if plotMagFlag:
        if plotCompFlag and buspair in busToVnomMagDict:
            return vval / busToVnomMagDict[buspair]
    else:
        if plotCompFlag and buspair in busToVnomAngDict:
            vval -= busToVnomAngDict[buspair]
            # -165 <= vval <= 195.0
            while vval > 195.0:
                vval -= 360.0
            while vval < -165.0:
                vval += 360.0

    return vval


def setTSZoomSliderVals(pairCount):
    # scale based on cube root of number of node/phase pairs
    # The multiplier is just a magic scaling factor that seems to produce
    # reasonable values for the 3 models used as test cases
    upper = 100 * (pairCount**(1./3))
    #upper = 18 * (pairCount**(1./3))
    # round to the nearest 10 to keep the slider from looking odd
    upper = int(round(upper/10.0)) * 10;
    # sanity check just in case
    upper = max(upper, 60)
    # // is integer floor division operator
    default = upper // 2;
    #print('setting time slider upper limit: ' + str(upper) + ', default value: ' + str(default), flush=True)
    uiTSZoomSldr.valmin = 1
    uiTSZoomSldr.valmax = upper
    uiTSZoomSldr.val = default
    uiTSZoomSldr.ax.set_xlim(uiTSZoomSldr.valmin, uiTSZoomSldr.valmax)
    uiTSZoomSldr.set_val(uiTSZoomSldr.val)


def findMeasTS(ts):
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
        return None, None

    senDataTS = None
    if sensorSimulatorRunningFlag:
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
            return None, None

    # determine whether simulation or sensor data should be used for
    # the second plot
    if useSensorsForEstimatesFlag:
        measDataTS = senDataTS
    else:
        measDataTS = simDataTS

    return measDataTS, simDataTS


def findSimTS(ts):
    simDataTS = None
    if ts in simAllDataDict:
        simDataTS = simAllDataDict[ts]

    return simDataTS


def estimateConfigAppend(ts, buspair, item, estkey, measkey,
                         foundSet, foundDiffSet, measDataTS, simDataTS):
    # for estimates, there should never be more than a single match
    # for a given bus,phase pair so skip check for that
    foundSet.add(buspair)

    estvval = item[estkey]
    estvval = calcBusVNom(estvval, buspair)

    #print(appName + ': estimate bus,phase pair: ' + buspair, flush=True)
    #print(appName + ': timestamp: ' + str(ts), flush=True)
    #print(appName + ': estvval: ' + str(estvval), flush=True)

    measvval = None
    if not plotMatchesFlag:
        if plotPausedFlag:
            estDataPausedDict[buspair].append(estvval)
            tsEstDataPausedDict[buspair].append(ts - tsInit)
        else:
            estDataDict[buspair].append(estvval)
            tsEstDataDict[buspair].append(ts - tsInit)

    if measDataTS is not None and buspair in busToMeasDict:
        for measmrid in busToMeasDict[buspair]:
            if buspair in foundDiffSet:
                break

            if measmrid in measDataTS:
                meas = measDataTS[measmrid]
                if measkey in meas:
                    foundDiffSet.add(buspair)

                    if plotMatchesFlag:
                        if plotPausedFlag:
                            estDataPausedDict[buspair].append(estvval)
                            tsEstDataPausedDict[buspair].append(ts - tsInit)
                        else:
                            estDataDict[buspair].append(estvval)
                            tsEstDataDict[buspair].append(ts - tsInit)

                    if measmrid in simDataTS:
                        sim = simDataTS[measmrid]
                        if measkey in sim:
                            simvval = sim[measkey]
                            simvval = calcBusVNom(simvval, buspair)

                            if not plotMagFlag:
                                diffestvval = estvval - simvval
                            elif simvval != 0.0:
                                diffestvval = abs(100.0*(estvval - simvval)/simvval)
                            else:
                                diffestvval = 0.0

                            if not plotOverlayFlag:
                                if plotPausedFlag:
                                    diffEstDataPausedDict[buspair+' Est'].append(diffestvval)
                                    tsDiffEstDataPausedDict[buspair+' Est'].append(ts - tsInit)
                                else:
                                    diffEstDataDict[buspair+' Est'].append(diffestvval)
                                    tsDiffEstDataDict[buspair+' Est'].append(ts - tsInit)

                            measvval = meas[measkey]
                            measvval = calcBusVNom(measvval, buspair)

                            if plotMagFlag:
                                vmagPrintWithMeas(ts, buspair, estvval, measvval, diffestvval)
                            else:
                                vangPrintWithMeas(ts, buspair, estvval, measvval, diffestvval)
                            break

    if not measvval:
        if plotMagFlag:
            vmagPrintWithoutMeas(ts, buspair, estvval)
        else:
            vangPrintWithoutMeas(ts, buspair, estvval)

    # no reason to keep checking more pairs if we've found all we
    # are looking for
    if not plotMatchesFlag and len(foundSet)==len(plotBusDict):
        return True
    elif plotMatchesFlag and len(foundDiffSet)==len(plotBusDict):
        return True

    return False


def estimateConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    measDataTS, simDataTS = findMeasTS(ts)
    if not measDataTS:
        return

    estVolt = msgdict['Estimate']['SvEstVoltages']

    foundSet = set()
    foundDiffSet = set()

    # set the data element keys we want to extract
    if plotMagFlag:
        estkey = 'v'
        measkey = 'magnitude'
    else:
        estkey = 'angle'
        measkey = 'angle'

    if plotMatchesFlag:
        for buspair in measDataDict:
            if buspair in plotBusDict:
                bus, phase = buspair.split(',')
                #if phase!='A' and phase!='B' and phase!='C' or \
                #   len(plotPhaseList)>0 and phase not in plotPhaseList:
                if len(plotPhaseList)>0 and phase not in plotPhaseList:
                    continue

                cnid = busToEstDict[bus]
                estlist = list(filter(lambda x:x['ConnectivityNode']==cnid and x['phase'].upper()==phase, estVolt))
                if (len(estlist) == 0):
                    continue

                item = estlist[0]
                if estimateConfigAppend(ts, buspair, item, estkey, measkey,
                                 foundSet, foundDiffSet, measDataTS, simDataTS):
                    break

    else:
        for item in estVolt:
            # only consider phases A, B, C and user-specified phases
            phase = item['phase']
            #if phase!='A' and phase!='B' and phase!='C' or \
            #   len(plotPhaseList)>0 and phase not in plotPhaseList:
            if len(plotPhaseList)>0 and phase not in plotPhaseList:
                continue

            buspair = estToBusDict[item['ConnectivityNode']+','+phase]
            if buspair in plotBusDict:
                if estimateConfigAppend(ts, buspair, item, estkey, measkey,
                                 foundSet, foundDiffSet, measDataTS, simDataTS):
                    break

    #print(appName + ': ' + str(len(estVolt)) + ' state-estimator measurements, ' + str(len(foundSet)) + ' configuration file node,phase pair matches, ' + str(len(foundDiffSet)) + ' matches to measurement data', flush=True)

    # update plots with the new data
    plotEstimateData()


def estimateNoConfigAppend(ts, buspair, item, estkey, measkey,
                           foundSet, foundDiffSet, measDataTS, simDataTS):
    # for estimates, there should never be more than a single match
    # for a given bus,phase pair so skip check for that
    foundSet.add(buspair)

    estvval = item[estkey]
    estvval = calcBusVNom(estvval, buspair)

    #print(appName + ': estimate bus,phase pair: ' + buspair, flush=True)
    #print(appName + ': timestamp: ' + str(ts), flush=True)
    #print(appName + ': estvval: ' + str(estvval), flush=True)

    # do dictionary and plot lines initialization the first time
    # the buspair is encountered
    if buspair not in estDataDict:
        estDataDict[buspair] = []
        tsEstDataDict[buspair] = []
        estDataPausedDict[buspair] = []
        tsEstDataPausedDict[buspair] = []
        if not plotOverlayFlag:
            diffEstDataDict[buspair+' Est'] = []
            tsDiffEstDataDict[buspair+' Est'] = []
            diffEstDataPausedDict[buspair+' Est'] = []
            tsDiffEstDataPausedDict[buspair+' Est'] = []

        # create a lines dictionary entry per bus,phase pair for each plot
        if plotOverlayFlag:
            if buspair in measLinesDict:
                color = measLinesDict[buspair].get_color()
                estLinesDict[buspair], = uiEstAx.plot([], [], label=buspair, linestyle='dashed', color=color)
            else:
                estLinesDict[buspair], = uiEstAx.plot([], [], label=buspair, linestyle='dashed')

            if buspair+' Actual' in diffMeasLinesDict:
                color = diffMeasLinesDict[buspair+' Actual'].get_color()
                diffEstLinesDict[buspair+' Est'], = uiDiffAx.plot([], [], label=buspair+' Est.', linestyle='dashed', color=color)
            else:
                color = estLinesDict[buspair].get_color()
                diffEstLinesDict[buspair+' Est'], = uiDiffAx.plot([], [], label=buspair+' Est.', color=color)

        else:
            if buspair in measLinesDict:
                color = measLinesDict[buspair].get_color()
                estLinesDict[buspair], = uiEstAx.plot([], [], label=buspair, color=color)
            else:
                estLinesDict[buspair], = uiEstAx.plot([], [], label=buspair)

            linestyle = 'solid'
            if sensorSimulatorRunningFlag:
                linestyle = 'dashed'

            if buspair+' Meas' in diffMeasLinesDict:
                color = diffMeasLinesDict[buspair+' Meas'].get_color()
                diffEstLinesDict[buspair+' Est'], = uiDiffAx.plot([], [], label=buspair+' Est.', linestyle=linestyle, color=color)
            else:
                color = estLinesDict[buspair].get_color()
                diffEstLinesDict[buspair+' Est'], = uiDiffAx.plot([], [], label=buspair+' Est.', color=color)

    measvval = None
    if not plotMatchesFlag:
        if plotPausedFlag:
            estDataPausedDict[buspair].append(estvval)
            tsEstDataPausedDict[buspair].append(ts - tsInit)
        else:
            estDataDict[buspair].append(estvval)
            tsEstDataDict[buspair].append(ts - tsInit)

    if measDataTS is not None and buspair in busToMeasDict:
        for measmrid in busToMeasDict[buspair]:
            if buspair in foundDiffSet:
                break

            if measmrid in measDataTS:
                meas = measDataTS[measmrid]
                if measkey in meas:
                    foundDiffSet.add(buspair)

                    if plotMatchesFlag:
                        if plotPausedFlag:
                            estDataPausedDict[buspair].append(estvval)
                            tsEstDataPausedDict[buspair].append(ts - tsInit)
                        else:
                            estDataDict[buspair].append(estvval)
                            tsEstDataDict[buspair].append(ts - tsInit)

                    if measmrid in simDataTS:
                        sim = simDataTS[measmrid]
                        if measkey in sim:
                            simvval = sim[measkey]
                            simvval = calcBusVNom(simvval, buspair)

                            if not plotMagFlag:
                                diffestvval = estvval - simvval
                            elif simvval != 0.0:
                                diffestvval = abs(100.0*(estvval - simvval)/simvval)
                            else:
                                diffestvval = 0.0

                            if not plotOverlayFlag:
                                if plotPausedFlag:
                                    diffEstDataPausedDict[buspair+' Est'].append(diffestvval)
                                    tsDiffEstDataPausedDict[buspair+' Est'].append(ts - tsInit)
                                else:
                                    diffEstDataDict[buspair+' Est'].append(diffestvval)
                                    tsDiffEstDataDict[buspair+' Est'].append(ts - tsInit)

                            measvval = meas[measkey]
                            measvval = calcBusVNom(measvval, buspair)

                            if plotMagFlag:
                                vmagPrintWithMeas(ts, buspair, estvval, measvval, diffestvval)
                            else:
                                vangPrintWithMeas(ts, buspair, estvval, measvval, diffestvval)
                            break

    if not measvval:
        if plotMagFlag:
            vmagPrintWithoutMeas(ts, buspair, estvval)
        else:
            vangPrintWithoutMeas(ts, buspair, estvval)

    # no reason to keep checking more pairs if we've found all we
    # are looking for
    if not plotMatchesFlag and plotNumber>0 and len(foundSet)==plotNumber:
        return True
    elif plotMatchesFlag and plotNumber>0 and len(foundDiffSet)==plotNumber:
        return True

    return False


def estimateNoConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    measDataTS, simDataTS = findMeasTS(ts)
    if not measDataTS:
        return

    estVolt = msgdict['Estimate']['SvEstVoltages']

    foundSet = set()
    foundDiffSet = set()

    # set the data element keys we want to extract
    if plotMagFlag:
        estkey = 'v'
        measkey = 'magnitude'
    else:
        estkey = 'angle'
        measkey = 'angle'

    if plotMatchesFlag:
        for buspair in measDataDict:
            bus, phase = buspair.split(',')
            #if phase!='A' and phase!='B' and phase!='C' or \
            #   len(plotPhaseList)>0 and phase not in plotPhaseList:
            if len(plotPhaseList)>0 and phase not in plotPhaseList:
                continue

            cnid = busToEstDict[bus]
            estlist = list(filter(lambda x:x['ConnectivityNode']==cnid and x['phase'].upper()==phase, estVolt))
            if (len(estlist) == 0):
                continue

            item = estlist[0]
            if estimateNoConfigAppend(ts, buspair, item, estkey, measkey,
                                 foundSet, foundDiffSet, measDataTS, simDataTS):
                break

    else:
        for item in estVolt:
            # only consider phases A, B, C and user-specified phases
            phase = item['phase']
            #if phase!='A' and phase!='B' and phase!='C' or \
            #   len(plotPhaseList)>0 and phase not in plotPhaseList:
            if len(plotPhaseList)>0 and phase not in plotPhaseList:
                continue

            buspair = estToBusDict[item['ConnectivityNode']+','+phase]
            if estimateNoConfigAppend(ts, buspair, item, estkey, measkey,
                                 foundSet, foundDiffSet, measDataTS, simDataTS):
                break

    #if plotNumber > 0:
    #    print(appName + ': ' + str(len(estVolt)) + ' state-estimator measurements, ' + str(len(foundSet)) + ' node,phase pair matches (matching first ' + str(plotNumber) + '), ' + str(len(foundDiffSet)) + ' matches to measurement data', flush=True)
    #else:
    #    print(appName + ': ' + str(len(estVolt)) + ' state-estimator measurements, ' + str(len(foundSet)) + ' node,phase pair matches (matching all), ' + str(len(foundDiffSet)) + ' matches to measurement data', flush=True)

    # update plots with the new data
    plotEstimateData()


def estimateStatsCallback(header, message):
    global firstEstimatePassFlag

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': estimate timestamp: ' + str(ts), flush=True)

    measDataTS, simDataTS = findMeasTS(ts)
    if not measDataTS:
        return

    if firstEstimatePassFlag:
        firstEstimatePassFlag = False

        estDataDict['Min'] = []
        tsEstDataDict['Min'] = []
        estDataDict['Max'] = []
        tsEstDataDict['Max'] = []
        estDataDict['Mean'] = []
        tsEstDataDict['Mean'] = []
        estDataDict['Stdev Low'] = []
        tsEstDataDict['Stdev Low'] = []
        estDataDict['Stdev High'] = []
        tsEstDataDict['Stdev High'] = []
        estDataPausedDict['Min'] = []
        tsEstDataPausedDict['Min'] = []
        estDataPausedDict['Max'] = []
        tsEstDataPausedDict['Max'] = []
        estDataPausedDict['Mean'] = []
        tsEstDataPausedDict['Mean'] = []
        estDataPausedDict['Stdev Low'] = []
        tsEstDataPausedDict['Stdev Low'] = []
        estDataPausedDict['Stdev High'] = []
        tsEstDataPausedDict['Stdev High'] = []

        # create a lines dictionary entry for each plot line
        if plotOverlayFlag:
            estLinesDict['Min'], = uiEstAx.plot([], [], label='Minimum', linestyle='dashed', color='cyan')
            estLinesDict['Max'], = uiEstAx.plot([], [], label='Maximum', linestyle='dashed', color='cyan')
            estLinesDict['Stdev Low'], = uiEstAx.plot([], [], label='Std. Dev. Low', linestyle='dashed', color='blue')
            estLinesDict['Stdev High'], = uiEstAx.plot([], [], label='Std. Dev. High', linestyle='dashed', color='blue')
            estLinesDict['Mean'], = uiEstAx.plot([], [], label='Mean', linestyle='dashed', color='red')

            diffEstLinesDict['Min Est'], = uiDiffAx.plot([], [], label='Minimum Est.', linestyle='dashed', color='cyan')
            diffEstLinesDict['Max Est'], = uiDiffAx.plot([], [], label='Maximum Est.', linestyle='dashed', color='cyan')
            diffEstLinesDict['Stdev Low Est'], = uiDiffAx.plot([], [], label='Std. Dev. Low Est.', linestyle='dashed', color='blue')
            diffEstLinesDict['Stdev High Est'], = uiDiffAx.plot([], [], label='Std. Dev. High Est.', linestyle='dashed', color='blue')
            diffEstLinesDict['Mean Est'], = uiDiffAx.plot([], [], label='Mean Est.', linestyle='dashed', color='red')

        else:
            estLinesDict['Min'], = uiEstAx.plot([], [], label='Minimum', color='cyan')
            estLinesDict['Max'], = uiEstAx.plot([], [], label='Maximum', color='cyan')
            estLinesDict['Stdev Low'], = uiEstAx.plot([], [], label='Std. Dev. Low', color='blue')
            estLinesDict['Stdev High'], = uiEstAx.plot([], [], label='Std. Dev. High', color='blue')
            estLinesDict['Mean'], = uiEstAx.plot([], [], label='Mean', color='red')

            diffEstDataDict['Mean Est'] = []
            tsDiffEstDataDict['Mean Est'] = []
            diffEstDataPausedDict['Mean Est'] = []
            tsDiffEstDataPausedDict['Mean Est'] = []

            # hardwire color to magenta specifically for this plot
            diffEstLinesDict['Mean Est'], = uiDiffAx.plot([], [], label='Mean Estimate Error', color='magenta')

    estlist = []
    diffestlist = []

    estVolt = msgdict['Estimate']['SvEstVoltages']
    foundDiffSet = set()

    # set the data element keys we want to extract
    if plotMagFlag:
        estkey = 'v'
        measkey = 'magnitude'
    else:
        estkey = 'angle'
        measkey = 'angle'

    for item in estVolt:
        # only consider phases A, B, C and user-specified phases
        phase = item['phase']
        #if phase!='A' and phase!='B' and phase!='C' or \
        #   len(plotPhaseList)>0 and phase not in plotPhaseList:
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        buspair = estToBusDict[item['ConnectivityNode']+','+phase]

        estvval = item[estkey]
        estvval = calcBusVNom(estvval, buspair)

        #print(appName + ': estimate bus,phase pair: ' + buspair, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': estvval: ' + str(estvval), flush=True)

        measvval = None
        if measDataTS is not None and buspair in busToMeasDict:
            for measmrid in busToMeasDict[buspair]:
                if buspair in foundDiffSet:
                    break

                if measmrid in measDataTS:
                    meas = measDataTS[measmrid]
                    if measkey in meas:
                        foundDiffSet.add(buspair)
                        estlist.append(estvval)

                        if measmrid in simDataTS:
                            sim = simDataTS[measmrid]
                            if measkey in sim:
                                simvval = sim[measkey]
                                simvval = calcBusVNom(simvval, buspair)

                                if not plotMagFlag:
                                    diffestvval = estvval - simvval
                                elif simvval != 0.0:
                                    diffestvval = abs(100.0*(estvval - simvval)/simvval)
                                else:
                                    diffestvval = 0.0

                                if not plotOverlayFlag:
                                    diffestlist.append(diffestvval)

                                measvval = meas[measkey]
                                measvval = calcBusVNom(measvval, buspair)

                                if plotMagFlag:
                                    vmagPrintWithMeas(ts, buspair, estvval, measvval, diffestvval)
                                else:
                                    vangPrintWithMeas(ts, buspair, estvval, measvval, diffestvval)
                                break

        if not measvval:
            if plotMagFlag:
                vmagPrintWithoutMeas(ts, buspair, estvval)
            else:
                vangPrintWithoutMeas(ts, buspair, estvval)

    estmin = min(estlist)
    estmax = max(estlist)
    estmean = statistics.mean(estlist)
    eststdev = statistics.pstdev(estlist, estmean)
    if plotPausedFlag:
        estDataPausedDict['Min'].append(estmin)
        tsEstDataPausedDict['Min'].append(ts - tsInit)
        estDataPausedDict['Max'].append(estmax)
        tsEstDataPausedDict['Max'].append(ts - tsInit)
        estDataPausedDict['Mean'].append(estmean)
        tsEstDataPausedDict['Mean'].append(ts - tsInit)
        estDataPausedDict['Stdev Low'].append(estmean-eststdev)
        tsEstDataPausedDict['Stdev Low'].append(ts - tsInit)
        estDataPausedDict['Stdev High'].append(estmean+eststdev)
        tsEstDataPausedDict['Stdev High'].append(ts - tsInit)
    else:
        estDataDict['Min'].append(estmin)
        tsEstDataDict['Min'].append(ts - tsInit)
        estDataDict['Max'].append(estmax)
        tsEstDataDict['Max'].append(ts - tsInit)
        estDataDict['Mean'].append(estmean)
        tsEstDataDict['Mean'].append(ts - tsInit)
        estDataDict['Stdev Low'].append(estmean-eststdev)
        tsEstDataDict['Stdev Low'].append(ts - tsInit)
        estDataDict['Stdev High'].append(estmean+eststdev)
        tsEstDataDict['Stdev High'].append(ts - tsInit)

    if not plotOverlayFlag:
        if len(diffestlist) > 0:
            diffestmean = statistics.mean(diffestlist)
            if plotPausedFlag:
                diffEstDataPausedDict['Mean Est'].append(diffestmean)
                tsDiffEstDataPausedDict['Mean Est'].append(ts - tsInit)
            else:
                diffEstDataDict['Mean Est'].append(diffestmean)
                tsDiffEstDataDict['Mean Est'].append(ts - tsInit)

            if plotMagFlag:
                print(appName + ': mean magnitude % diff estimate: ' + str(diffestmean), flush=True)
            else:
                print(appName + ': mean angle diff estimate: ' + str(diffestmean), flush=True)

    # update plots with the new data
    plotEstimateData()


def measurementConfigCallback(header, message):
    global firstMeasurementPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    measVolt = msgdict['measurements']

    if useSensorsForEstimatesFlag:
        #print('>', end='', flush=True)
        print('[sen]', end='', flush=True)
        #print('('+str(ts)+')', end='', flush=True)
        #pprint.pprint(msgdict)

        # because we require Python 3.6, we can count on insertion ordered
        # dictionaries
        # otherwise a list should be used, but then I have to make it a list
        # of tuples to store the timestamp as well
        senAllDataDict[ts] = measVolt

    else:
        #print('<', end='', flush=True)
        print('[sim]', end='', flush=True)
        #print('('+str(ts)+')', end='', flush=True)
        #pprint.pprint(msgdict)

        # because we require Python 3.6, we can count on insertion ordered
        # dictionaries
        # otherwise a list should be used, but then I have to make it a list
        # of tuples to store the timestamp as well
        simAllDataDict[ts] = measVolt

    simDataTS = None
    if useSensorsForEstimatesFlag:
        # this must be a sensor measurement triggering this callback so
        # get the corresponding simulation measurement that was sent
        simDataTS = findSimTS(ts)

    if firstMeasurementPassFlag:
        firstMeasurementPassFlag = False
        # save first timestamp so what we plot is an offset from this
        tsInit = ts
        setTSZoomSliderVals(len(measVolt))

    # set the data element keys we want to extract
    if plotMagFlag:
        measkey = 'magnitude'
    else:
        measkey = 'angle'

    foundSet = set()

    for measmrid in measVolt:
        if measmrid not in measToBusDict:
            continue

        buspair = measToBusDict[measmrid]
        bus, phase = buspair.split(',')

        # only consider phases A, B, C and user-specified phases
        #if phase!='A' and phase!='B' and phase!='C' or \
        #   len(plotPhaseList)>0 and phase not in plotPhaseList:
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        # skip if this is a buspair that's not in the plot configuration
        # or if the buspair was previously processed (multiple mrids for
        # bus,phase pairs are possible where we just take the first)
        if buspair in plotBusDict and buspair not in foundSet:
            meas = measVolt[measmrid]

            if measkey not in meas:
                continue

            foundSet.add(buspair)

            measvval = meas[measkey]
            measvval = calcBusVNom(measvval, buspair)

            #print(appName + ': measurement bus,phase pair: ' + buspair, flush=True)
            #print(appName + ': timestamp: ' + str(ts), flush=True)
            #print(appName + ': measvval: ' + str(measvval), flush=True)

            if plotPausedFlag:
                measDataPausedDict[buspair].append(measvval)
                tsMeasDataPausedDict[buspair].append(ts - tsInit)
            else:
                measDataDict[buspair].append(measvval)
                tsMeasDataDict[buspair].append(ts - tsInit)

            if not plotOverlayFlag and simDataTS and measmrid in simDataTS:
                sim = simDataTS[measmrid]
                if measkey in sim:
                    simvval = sim[measkey]
                    simvval = calcBusVNom(simvval, buspair)

                    if not plotMagFlag:
                        diffmeasvval = measvval - simvval
                    elif simvval != 0.0:
                        diffmeasvval = abs(100.0*(measvval - simvval)/simvval)
                    else:
                        diffmeasvval = 0.0

                    if plotPausedFlag:
                        diffMeasDataPausedDict[buspair+' Meas'].append(diffmeasvval)
                        tsDiffMeasDataPausedDict[buspair+' Meas'].append(ts - tsInit)
                    else:
                        diffMeasDataDict[buspair+' Meas'].append(diffmeasvval)
                        tsDiffMeasDataDict[buspair+' Meas'].append(ts - tsInit)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if len(foundSet) == len(plotBusDict):
                break

    #print(appName + ': ' + str(len(measVolt)) + ' measurements, ' + str(measCount) + ' configuration file bus,phase pair matches, ' + str(len(plotBusDict)) + ' configuration file bus,phase total pairs', flush=True)

    # update measurement plot with the new data
    plotMeasurementData()


def measurementNoConfigCallback(header, message):
    global firstMeasurementPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    measVolt = msgdict['measurements']

    if useSensorsForEstimatesFlag:
        #print('>', end='', flush=True)
        print('[sen]', end='', flush=True)
        #print('('+str(ts)+')', end='', flush=True)
        #pprint.pprint(msgdict)

        # because we require Python 3.6, we can count on insertion ordered
        # dictionaries
        # otherwise a list should be used, but then I have to make it a list
        # of tuples to store the timestamp as well
        senAllDataDict[ts] = measVolt
    else:
        #print('<', end='', flush=True)
        print('[sim]', end='', flush=True)
        #print('('+str(ts)+')', end='', flush=True)
        #pprint.pprint(msgdict)

        # because we require Python 3.6, we can count on insertion ordered
        # dictionaries
        # otherwise a list should be used, but then I have to make it a list
        # of tuples to store the timestamp as well
        simAllDataDict[ts] = measVolt

    simDataTS = None
    if useSensorsForEstimatesFlag:
        # this must be a sensor measurement triggering this callback so
        # get the corresponding simulation measurement that was sent
        simDataTS = findSimTS(ts)

    if firstMeasurementPassFlag:
        firstMeasurementPassFlag = False
        # save first timestamp so what we plot is an offset from this
        tsInit = ts
        setTSZoomSliderVals(len(measVolt))

    # set the data element keys we want to extract
    if plotMagFlag:
        measkey = 'magnitude'
    else:
        measkey = 'angle'

    foundSet = set()

    for measmrid in measVolt:
        if measmrid not in measToBusDict:
            continue

        buspair = measToBusDict[measmrid]
        bus, phase = buspair.split(',')

        # check user-specified phases
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        # skip if this is a buspair that was previously processed
        # (multiple mrids for bus,phase pairs are possible where we
        # just take the first)
        if buspair in foundSet:
            continue

        meas = measVolt[measmrid]

        # TODO handle missing measurement values
        if measkey not in meas:
            print('*** ' + measkey + ' NOT FOUND for buspair: ' + buspair + ', meas: ' + str(meas), flush=True)
            continue

        # only consider the buspair as found if the measurement value
        # needed exists
        foundSet.add(buspair)
        #print('(' + buspair + ')', end='', flush=True) # DEBUG

        measvval = meas[measkey]
        measvval = calcBusVNom(measvval, buspair)

        #print(appName + ': measurement bus,phase pair: ' + buspair, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': measvval: ' + str(measvval), flush=True)

        # do dictionary and plot lines initialization the first time
        # the buspair is encountered
        if buspair not in measDataDict:
            measDataDict[buspair] = []
            tsMeasDataDict[buspair] = []
            measDataPausedDict[buspair] = []
            tsMeasDataPausedDict[buspair] = []
            if not plotOverlayFlag and sensorSimulatorRunningFlag:
                diffMeasDataDict[buspair+' Meas'] = []
                tsDiffMeasDataDict[buspair+' Meas'] = []
                diffMeasDataPausedDict[buspair+' Meas'] = []
                tsDiffMeasDataPausedDict[buspair+' Meas'] = []

            # create a lines dictionary entry per node/phase pair
            measLinesDict[buspair], = uiMeasAx.plot([], [], label=buspair)
            color = measLinesDict[buspair].get_color()

            if plotOverlayFlag:
                diffMeasLinesDict[buspair+' Actual'], = uiDiffAx.plot([], [], label=buspair+' Actual', color=color)
            else:
                diffMeasLinesDict[buspair+' Meas'], = uiDiffAx.plot([], [], label=buspair+' Meas.', color=color)

        if plotPausedFlag:
            measDataPausedDict[buspair].append(measvval)
            tsMeasDataPausedDict[buspair].append(ts - tsInit)
        else:
            measDataDict[buspair].append(measvval)
            tsMeasDataDict[buspair].append(ts - tsInit)

        if not plotOverlayFlag and simDataTS and measmrid in simDataTS:
            sim = simDataTS[measmrid]
            if measkey in sim:
                simvval = sim[measkey]
                simvval = calcBusVNom(simvval, buspair)

                if not plotMagFlag:
                    diffmeasvval = measvval - simvval
                elif simvval != 0.0:
                    diffmeasvval = abs(100.0*(measvval - simvval)/simvval)
                else:
                    diffmeasvval = 0.0

                if plotPausedFlag:
                    diffMeasDataPausedDict[buspair+' Meas'].append(diffmeasvval)
                    tsDiffMeasDataPausedDict[buspair+' Meas'].append(ts - tsInit)
                else:
                    diffMeasDataDict[buspair+' Meas'].append(diffmeasvval)
                    tsDiffMeasDataDict[buspair+' Meas'].append(ts - tsInit)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if plotNumber>0 and len(foundSet)==plotNumber:
            break

    #if plotNumber > 0:
    #    print(appName + ': ' + str(len(measVolt)) + ' measurements, ' + str(len(foundSet)) + ' node,phase pair matches (matching first ' + str(plotNumber) + ')', flush=True)
    #else:
    #    print(appName + ': ' + str(len(len(measVolt))) + ' measurements, ' + str(len(foundSet)) + ' node,phase pair matches (matching all)', flush=True)

    #print('DEBUG: # of pairs: ' + str(len(foundSet)), flush=True)
    # update measurement plot with the new data
    plotMeasurementData()


def measurementStatsCallback(header, message):
    global firstMeasurementPassFlag, tsInit

    msgdict = message['message']
    ts = msgdict['timestamp']
    #print(appName + ': measurement timestamp: ' + str(ts), flush=True)

    measVolt = msgdict['measurements']

    if useSensorsForEstimatesFlag:
        #print('>', end='', flush=True)
        print('[sen]', end='', flush=True)
        #print('('+str(ts)+')', end='', flush=True)
        #pprint.pprint(msgdict)

        # because we require Python 3.6, we can count on insertion ordered
        # dictionaries
        # otherwise a list should be used, but then I have to make it a list
        # of tuples to store the timestamp as well
        senAllDataDict[ts] = measVolt
    else:
        #print('<', end='', flush=True)
        print('[sim]', end='', flush=True)
        #print('('+str(ts)+')', end='', flush=True)
        #pprint.pprint(msgdict)

        # because we require Python 3.6, we can count on insertion ordered
        # dictionaries
        # otherwise a list should be used, but then I have to make it a list
        # of tuples to store the timestamp as well
        simAllDataDict[ts] = measVolt

    simDataTS = None
    if useSensorsForEstimatesFlag:
        # this must be a sensor measurement triggering this callback so
        # get the corresponding simulation measurement that was sent
        simDataTS = findSimTS(ts)

    if firstMeasurementPassFlag:
        firstMeasurementPassFlag = False
        # save first timestamp so what we plot is an offset from this
        tsInit = ts
        setTSZoomSliderVals(len(measVolt))

        measDataDict['Min'] = []
        tsMeasDataDict['Min'] = []
        measDataDict['Max'] = []
        tsMeasDataDict['Max'] = []
        measDataDict['Mean'] = []
        tsMeasDataDict['Mean'] = []
        measDataDict['Stdev Low'] = []
        tsMeasDataDict['Stdev Low'] = []
        measDataDict['Stdev High'] = []
        tsMeasDataDict['Stdev High'] = []
        measDataPausedDict['Min'] = []
        tsMeasDataPausedDict['Min'] = []
        measDataPausedDict['Max'] = []
        tsMeasDataPausedDict['Max'] = []
        measDataPausedDict['Mean'] = []
        tsMeasDataPausedDict['Mean'] = []
        measDataPausedDict['Stdev Low'] = []
        tsMeasDataPausedDict['Stdev Low'] = []
        measDataPausedDict['Stdev High'] = []
        tsMeasDataPausedDict['Stdev High'] = []

        # create a lines dictionary entry for each measurement plot line
        measLinesDict['Min'], = uiMeasAx.plot([], [], label='Minimum', color='cyan')
        measLinesDict['Max'], = uiMeasAx.plot([], [], label='Maximum', color='cyan')
        measLinesDict['Stdev Low'], = uiMeasAx.plot([], [], label='Std. Dev. Low', color='blue')
        measLinesDict['Stdev High'], = uiMeasAx.plot([], [], label='Std. Dev. High', color='blue')
        measLinesDict['Mean'], = uiMeasAx.plot([], [], label='Mean', color='red')

        # create a lines dictionary entry for each plot line
        if plotOverlayFlag:
            diffMeasLinesDict['Min Actual'], = uiDiffAx.plot([], [], label='Minimum Actual', color='cyan')
            diffMeasLinesDict['Max Actual'], = uiDiffAx.plot([], [], label='Maximum Actual', color='cyan')
            diffMeasLinesDict['Stdev Low Actual'], = uiDiffAx.plot([], [], label='Std. Dev. Low Actual', color='blue')
            diffMeasLinesDict['Stdev High Actual'], = uiDiffAx.plot([], [], label='Std. Dev. High Actual', color='blue')
            diffMeasLinesDict['Mean Actual'], = uiDiffAx.plot([], [], label='Mean Actual', color='red')

        else:
            if sensorSimulatorRunningFlag:
                diffMeasDataDict['Mean Meas'] = []
                diffMeasDataPausedDict['Mean Meas'] = []

                # hardwire color to green specifically for this plot
                diffMeasLinesDict['Mean Meas'], = uiDiffAx.plot([], [], label='Mean Measurement Error', color='green')

    measlist = []
    if sensorSimulatorRunningFlag:
        diffmeaslist = []

    foundSet = set()

    # set the data element keys we want to extract
    if plotMagFlag:
        measkey = 'magnitude'
    else:
        measkey = 'angle'

    for measmrid in measVolt:
        if measmrid not in measToBusDict:
            continue

        buspair = measToBusDict[measmrid]
        bus, phase = buspair.split(',')

        # only consider phases A, B, C and user-specified phases
        #if phase!='A' and phase!='B' and phase!='C' or \
        #   len(plotPhaseList)>0 and phase not in plotPhaseList:
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        if buspair in foundSet:
            continue

        meas = measVolt[measmrid]

        if measkey not in meas:
            continue

        foundSet.add(buspair)

        measvval = meas[measkey]
        measvval = calcBusVNom(measvval, buspair)

        #print(appName + ': measurement bus,phase pair: ' + buspair, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': measvval: ' + str(measvval), flush=True)

        measlist.append(measvval)

        if not plotOverlayFlag and simDataTS and measmrid in simDataTS:
            sim = simDataTS[measmrid]
            if measkey in sim:
                simvval = sim[measkey]
                simvval = calcBusVNom(simvval, buspair)

                if not plotMagFlag:
                    diffmeasvval = measvval - simvval
                elif simvval != 0.0:
                    diffmeasvval = abs(100.0*(measvval - simvval)/simvval)
                else:
                    diffmeasvval = 0.0

                diffmeaslist.append(diffmeasvval)

    if len(measlist) > 0:
        measmin = min(measlist)
        measmax = max(measlist)
        measmean = statistics.mean(measlist)
        measstdev = statistics.pstdev(measlist, measmean)
        if plotPausedFlag:
            measDataPausedDict['Min'].append(measmin)
            tsMeasDataPausedDict['Min'].append(ts - tsInit)
            measDataPausedDict['Max'].append(measmax)
            tsMeasDataPausedDict['Max'].append(ts - tsInit)
            measDataPausedDict['Mean'].append(measmean)
            tsMeasDataPausedDict['Mean'].append(ts - tsInit)
            measDataPausedDict['Stdev Low'].append(measmean-measstdev)
            tsMeasDataPausedDict['Stdev Low'].append(ts - tsInit)
            measDataPausedDict['Stdev High'].append(measmean+measstdev)
            tsMeasDataPausedDict['Stdev High'].append(ts - tsInit)
        else:
            measDataDict['Min'].append(measmin)
            tsMeasDataDict['Min'].append(ts - tsInit)
            measDataDict['Max'].append(measmax)
            tsMeasDataDict['Max'].append(ts - tsInit)
            measDataDict['Mean'].append(measmean)
            tsMeasDataDict['Mean'].append(ts - tsInit)
            measDataDict['Stdev Low'].append(measmean-measstdev)
            tsMeasDataDict['Stdev Low'].append(ts - tsInit)
            measDataDict['Stdev High'].append(measmean+measstdev)
            tsMeasDataDict['Stdev High'].append(ts - tsInit)

    if not plotOverlayFlag and sensorSimulatorRunningFlag and len(diffmeaslist)>0:
        diffmeasmean = statistics.mean(diffmeaslist)
        if plotPausedFlag:
            diffMeasDataPausedDict['Mean Meas'].append(diffmeasmean)
            tsDiffMeasDataPausedDict['Mean Meas'].append(ts - tsInit)
        else:
            diffMeasDataDict['Mean Meas'].append(diffmeasmean)
            tsDiffMeasDataDict['Mean Meas'].append(ts - tsInit)

        if plotMagFlag:
            print(appName + ': mean magnitude % diff measurement: ' + str(diffmeasmean), flush=True)
        else:
            print(appName + ': mean angle diff measurement: ' + str(diffmeasmean), flush=True)

    # update measurement plot with the new data
    plotMeasurementData()


def simulationCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': meaurement message timestamp: ' + str(ts), flush=True)
    #print('<', end='', flush=True)
    print('[sim]', end='', flush=True)
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
    #print('>', end='', flush=True)
    print('[sen]', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    senAllDataDict[ts] = msgdict['measurements']


def sensorConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': meaurement message timestamp: ' + str(ts), flush=True)
    #print('>', end='', flush=True)
    print('[sen]', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    measVolt = msgdict['measurements']
    senAllDataDict[ts] = measVolt

    # get the corresponding simulation measurement that was sent
    simDataTS = findSimTS(ts)

    # set the data element keys we want to extract
    if plotMagFlag:
        measkey = 'magnitude'
    else:
        measkey = 'angle'

    foundSet = set()

    for measmrid in measVolt:
        if measmrid not in measToBusDict:
            continue

        buspair = measToBusDict[measmrid]
        bus, phase = buspair.split(',')

        # only consider phases A, B, C and user-specified phases
        #if phase!='A' and phase!='B' and phase!='C' or \
        #   len(plotPhaseList)>0 and phase not in plotPhaseList:
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        # skip if this is a buspair that's not in the plot configuration
        # or if the buspair was previously processed (multiple mrids for
        # bus,phase pairs are possible where we just take the first)
        if buspair in plotBusDict and buspair not in foundSet:
            meas = measVolt[measmrid]

            if measkey not in meas:
                continue

            foundSet.add(buspair)

            measvval = meas[measkey]
            measvval = calcBusVNom(measvval, buspair)

            #print(appName + ': bus,phase pair: ' + buspair, flush=True)
            #print(appName + ': timestamp: ' + str(ts), flush=True)
            #print(appName + ': measvval: ' + str(measvval), flush=True)

            # TODO we only process when not plotOverlayFlag so any reason
            # not to move that check up earlier?
            if not plotOverlayFlag and simDataTS and measmrid in simDataTS:
                sim = simDataTS[measmrid]
                if measkey in sim:
                    simvval = sim[measkey]
                    simvval = calcBusVNom(simvval, buspair)

                    if not plotMagFlag:
                        diffmeasvval = measvval - simvval
                    elif simvval != 0.0:
                        diffmeasvval = abs(100.0*(measvval - simvval)/simvval)
                    else:
                        diffmeasvval = 0.0

                    if plotPausedFlag:
                        diffMeasDataPausedDict[buspair+' Meas'].append(diffmeasvval)
                        tsDiffMeasDataPausedDict[buspair+' Meas'].append(ts - tsInit)
                    else:
                        diffMeasDataDict[buspair+' Meas'].append(diffmeasvval)
                        tsDiffMeasDataDict[buspair+' Meas'].append(ts - tsInit)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if len(foundSet) == len(plotBusDict):
                break

    #print(appName + ': ' + str(len(measVolt)) + ' measurements, ' + str(measCount) + ' configuration file bus,phase pair matches, ' + str(len(plotBusDict)) + ' configuration file bus,phase total pairs', flush=True)

    # update measurement plot with the new data
    plotMeasurementData()


def sensorNoConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': meaurement message timestamp: ' + str(ts), flush=True)
    #print('>', end='', flush=True)
    print('[sen]', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    measVolt = msgdict['measurements']
    senAllDataDict[ts] = measVolt

    # get the corresponding simulation measurement that was sent
    simDataTS = findSimTS(ts)

    # set the data element keys we want to extract
    if plotMagFlag:
        measkey = 'magnitude'
    else:
        measkey = 'angle'

    foundSet = set()

    for measmrid in measVolt:
        if measmrid not in measToBusDict:
            continue

        buspair = measToBusDict[measmrid]
        bus, phase = buspair.split(',')

        # consider user-specified phases
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        # skip if this is a buspair that was previously processed
        # (multiple mrids for bus,phase pairs are possible where we
        # just take the first)
        if buspair in foundSet:
            continue

        meas = measVolt[measmrid]

        if measkey not in meas:
            continue

        foundSet.add(buspair)

        measvval = meas[measkey]
        measvval = calcBusVNom(measvval, buspair)

        #print(appName + ': bus,phase pair: ' + buspair, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': measvval: ' + str(measvval), flush=True)

        # do dictionary and plot lines initialization the first time
        # the buspair is encountered
        if buspair+' Meas' not in diffMeasDataDict:
            diffMeasDataDict[buspair+' Meas'] = []
            diffMeasDataPausedDict[buspair+' Meas'] = []

            # create a lines dictionary entry per node/phase pair for each plot
            if plotOverlayFlag:
                diffMeasLinesDict[buspair+' Actual'], = uiDiffAx.plot([], [], label=buspair+' Actual')
            else:
                diffMeasLinesDict[buspair+' Meas'], = uiDiffAx.plot([], [], label=buspair+' Meas.')

        if not plotOverlayFlag and simDataTS and measmrid in simDataTS:
            sim = simDataTS[measmrid]
            if measkey in sim:
                simvval = sim[measkey]
                simvval = calcBusVNom(simvval, buspair)

                if not plotMagFlag:
                    diffmeasvval = measvval - simvval
                elif simvval != 0.0:
                    diffmeasvval = abs(100.0*(measvval - simvval)/simvval)
                else:
                    diffmeasvval = 0.0

                if plotPausedFlag:
                    diffMeasDataPausedDict[buspair+' Meas'].append(diffmeasvval)
                    tsDiffMeasDataPausedDict[buspair+' Meas'].append(ts - tsInit)
                else:
                    diffMeasDataDict[buspair+' Meas'].append(diffmeasvval)
                    tsDiffMeasDataDict[buspair+' Meas'].append(ts - tsInit)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if plotNumber>0 and len(foundSet)==plotNumber:
            break

    #if plotNumber > 0:
    #    print(appName + ': ' + str(len(measVolt)) + ' measurements, ' + str(len(foundSet)) + ' node,phase pair matches (matching first ' + str(plotNumber) + ')', flush=True)
    #else:
    #    print(appName + ': ' + str(len(len(measVolt))) + ' measurements, ' + str(len(foundSet)) + ' node,phase pair matches (matching all)', flush=True)

    # update measurement plot with the new data
    plotMeasurementData()


def sensorStatsCallback(header, message):
    global firstSensorPassFlag

    msgdict = message['message']
    ts = msgdict['timestamp']

    #print(appName + ': meaurement message timestamp: ' + str(ts), flush=True)
    #print('>', end='', flush=True)
    print('[sen]', end='', flush=True)
    #print('('+str(ts)+')', end='', flush=True)
    #pprint.pprint(msgdict)

    # because we require Python 3.6, we can count on insertion ordered
    # dictionaries
    # otherwise a list should be used, but then I have to make it a list
    # of tuples to store the timestamp as well
    measVolt = msgdict['measurements']
    senAllDataDict[ts] = measVolt

    # get the corresponding simulation measurement that was sent
    simDataTS = findSimTS(ts)

    if firstSensorPassFlag:
        firstSensorPassFlag = False

        # create a lines dictionary entry for each plot line
        if plotOverlayFlag:
            diffMeasLinesDict['Min Actual'], = uiDiffAx.plot([], [], label='Minimum Actual', color='cyan')
            diffMeasLinesDict['Max Actual'], = uiDiffAx.plot([], [], label='Maximum Actual', color='cyan')
            diffMeasLinesDict['Stdev Low Actual'], = uiDiffAx.plot([], [], label='Std. Dev. Low Actual', color='blue')
            diffMeasLinesDict['Stdev High Actual'], = uiDiffAx.plot([], [], label='Std. Dev. High Actual', color='blue')
            diffMeasLinesDict['Mean Actual'], = uiDiffAx.plot([], [], label='Mean Actual', color='red')

        else:
            diffMeasDataDict['Mean Meas'] = []
            diffMeasDataPausedDict['Mean Meas'] = []

            # hardwire color to green specifically for this plot
            diffMeasLinesDict['Mean Meas'], = uiDiffAx.plot([], [], label='Mean Measurement Error', color='green')

    diffmeaslist = []

    foundSet = set()

    # set the data element keys we want to extract
    if plotMagFlag:
        measkey = 'magnitude'
    else:
        measkey = 'angle'

    for measmrid in measVolt:
        if measmrid not in measToBusDict:
            continue

        buspair = measToBusDict[measmrid]
        bus, phase = buspair.split(',')

        # only consider phases A, B, C and user-specified phases
        #if phase!='A' and phase!='B' and phase!='C' or \
        #   len(plotPhaseList)>0 and phase not in plotPhaseList:
        if len(plotPhaseList)>0 and phase not in plotPhaseList:
            continue

        if buspair in foundSet:
            continue

        meas = measVolt[measmrid]

        if measkey not in measvval:
            continue

        foundSet.add(buspair)

        measvval = meas[measkey]
        measvval = calcBusVNom(measvval, buspair)

        #print(appName + ': measmrid: ' + measmrid, flush=True)
        #print(appName + ': timestamp: ' + str(ts), flush=True)
        #print(appName + ': measvval: ' + str(measvval), flush=True)

        measlist.append(measvval)

        if not plotOverlayFlag and simDataTS and measmrid in simDataTS:
            sim = simDataTS[measmrid]
            if measkey in sim:
                simvval = sim[measkey]
                simvval = calcBusVNom(simvval, buspair)

                if not plotMagFlag:
                    diffmeasvval = measvval - simvval
                elif simvval != 0.0:
                    diffmeasvval = abs(100.0*(measvval - simvval)/simvval)
                else:
                    diffmeasvval = 0.0

                diffmeaslist.append(diffmeasvval)

    if not plotOverlayFlag and len(diffmeaslist)>0:
        diffmeasmean = statistics.mean(diffmeaslist)
        if plotPausedFlag:
            diffMeasDataPausedDict['Mean Meas'].append(diffmeasmean)
            tsDiffMeasDataPausedDict['Mean Meas'].append(ts - tsInit)
        else:
            diffMeasDataDict['Mean Meas'].append(diffmeasmean)
            tsDiffMeasDataDict['Mean Meas'].append(ts - tsInit)

        if plotMagFlag:
            print(appName + ': mean magnitude % diff measurement: ' + str(diffmeasmean), flush=True)
        else:
            print(appName + ': mean angle diff measurement: ' + str(diffmeasmean), flush=True)

    # update measurement plot with the new data
    plotMeasurementData()


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


def updatePlots():
    # now just do this to cause a redraw
    plotFig.canvas.draw_idle()

    # but I used to do all of these instead, but it doesn't seem to
    # make a difference and the draw_idle() call seems more CPU friendly
    # plt.sca(uiMeasAx)
    # plt.draw()
    # plt.sca(uiEstAx)
    # plt.draw()
    # plt.sca(uiDiffAx)
    # plt.draw()
    # plotFig.canvas.flush_events()


def tsSlice(tsDataList, tsXmin, tsXmax):
    tsStartpt = 0
    if tsXmin > 0:
        # don't assume 3 timesteps between points, calculate startpt
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

    # don't assume 3 timesteps between points, calculate endpt
    #tsEndpt = int(tsXmax/3.0) + 1
    tsEndpt = 0
    if tsXmax > 0:
        tsEndpt = len(tsDataList)-1
        for ix in range(tsEndpt,-1,-1):
            #print(appName + ': tsEndpt ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
            if tsDataList[ix] <= tsXmax:
                # if it's feasible, set ending point to 1 after the calculated
                # point so there is no data gap at the right edge
                if ix < tsEndpt:
                    tsEndpt = ix + 1
                #print(appName + ': tsEndpt break ix: ' + str(ix) + ', tsDataList: ' + str(tsDataList[ix]), flush=True)
                break

    # always add 1 to endpt because array slice uses -1 for upper bound
    tsEndpt += 1
    #print(appName + ': tsStartpt: ' + str(tsStartpt), flush=True)
    #print(appName + ': tsEndpt: ' + str(tsEndpt) + '\n', flush=True)

    return tsStartpt, tsEndpt


def plotMeasurementData():
    global measDiffYmin, measDiffYmax

    measDataFlag = False
    diffMeasDataFlag = False

    if plotShowAllFlag:
        measXmax = -sys.float_info.max
        measYmax = -sys.float_info.max
        measYmin = sys.float_info.max
        for pair in measDataDict:
            if len(measDataDict[pair]) > 0:
                measDataFlag = True
                measLinesDict[pair].set_data(tsMeasDataDict[pair], measDataDict[pair])
                measXmax = max(measXmax, int(tsMeasDataDict[pair][-1]))
                measYmin = min(measYmin, min(measDataDict[pair]))
                measYmax = max(measYmax, max(measDataDict[pair]))

                if pair in plotBusDict and \
                   plotBusDict[pair] not in measLegendLabelList:
                    measLegendLabelList.append(plotBusDict[pair])
                    measLegendLineList.append(measLinesDict[pair])

        #print(appName + ': measYmin: ' + str(measYmin) + ', measYmax: ' + str(measYmax), flush=True)

        #if plotStatsFlag:
        #    plt.sca(uiMeasAx)
        #    if len(measDataDict['Mean']) > 0:
                # disable filling between lines because it's too much work
                # for big models and causes matplotlib to freeze
                #plt.fill_between(x=tsMeasDataDict['Mean'], y1=measDataDict['Mean'], y2=measDataDict['Stdev Low'], color=stdevBlue)
                #plt.fill_between(x=tsMeasDataDict['Mean'], y1=measDataDict['Mean'], y2=measDataDict['Stdev High'], color=stdevBlue)
                #plt.fill_between(x=tsMeasDataDict['Stdev Low'], y1=measDataDict['Stdev Low'], y2=measDataDict['Min'], color=minmaxBlue)
                #plt.fill_between(x=tsMeasDataDict['Stdev High'], y1=measDataDict['Stdev High'], y2=measDataDict['Max'], color=minmaxBlue)

        if measDataFlag:
            uiMeasAx.set_xlim(0, measXmax)
        else:
            return;

        if plotOverlayFlag:
            measDiffYmin = measYmin
            measDiffYmax = measYmax

            for pair in measDataDict:
                if len(measDataDict[pair]) > 0:
                    diffMeasDataFlag = True
                    diffMeasLinesDict[pair+' Actual'].set_data(tsMeasDataDict[pair], measDataDict[pair])

        else:
            measDiffYmin = sys.float_info.max
            measDiffYmax = -sys.float_info.max

            for pair in diffMeasDataDict:
                if len(diffMeasDataDict[pair]) > 0:
                    diffMeasDataFlag = True
                    diffMeasLinesDict[pair].set_data(tsDiffMeasDataDict[pair], diffMeasDataDict[pair])
                    measDiffYmin = min(measDiffYmin, min(diffMeasDataDict[pair]))
                    measDiffYmax = max(measDiffYmax, max(diffMeasDataDict[pair]))
        #print(appName + ': measDiffYmin: ' + str(measDiffYmin) + ', measDiffYmax: ' + str(measDiffYmax), flush=True)

    else:
        measXmax = -sys.float_info.max
        for pair in measDataDict:
            if len(measDataDict[pair]) > 0:
                measDataFlag = True
                measXmax = max(measXmax, int(tsMeasDataDict[pair][-1]))

        if not measDataFlag:
            return

        tsZoom = int(uiTSZoomSldr.val)
        tsPan = int(uiTSPanSldr.val)
        if tsPan == 100:
            # this fills data from the right
            tsXmax = measXmax
            tsXmin = tsXmax - tsZoom

            # uncomment this code if filling from the left is preferred
            #if tsXmin < 0:
            #    tsXmin = 0
            #    tsXmax = tsZoom
        elif tsPan == 0:
            tsXmin = 0
            tsXmax = tsZoom
        else:
            tsMid = int(measXmax*tsPan/100.0)
            tsXmin = int(tsMid - tsZoom/2.0)
            tsXmax = tsXmin + tsZoom
            # this fills data from the right
            if tsXmax > measXmax:
                tsXmax = measXmax
                tsXmin = tsXmax - tsZoom
            elif tsXmin < 0:
                tsXmin = 0
                tsXmax = tsZoom
            # if filling from the left is preferred uncomment the lines
            # below and comment out the block if/elif block above
            #if tsXmin < 0:
            #    tsXmax = measXmax
            #    tsXmin = tsXmax - tsZoom
            #elif tsXmax > measXmax:
            #    tsXmin = 0
            #    tsXmax = tsZoom

        uiMeasAx.set_xlim(tsXmin, tsXmax)
        #print(appName + ': tsXmin: ' + str(tsXmin), flush=True)
        #print(appName + ': tsXmax: ' + str(tsXmax), flush=True)

        measYmax = -sys.float_info.max
        measYmin = sys.float_info.max
        for pair in measDataDict:
            tsStartpt, tsEndpt = tsSlice(tsMeasDataDict[pair], tsXmin, tsXmax)

            if len(measDataDict[pair][tsStartpt:tsEndpt]) > 0:
                measDataFlag = True
                measLinesDict[pair].set_data(tsMeasDataDict[pair][tsStartpt:tsEndpt], measDataDict[pair][tsStartpt:tsEndpt])
                measYmin = min(measYmin, min(measDataDict[pair][tsStartpt:tsEndpt]))
                measYmax = max(measYmax, max(measDataDict[pair][tsStartpt:tsEndpt]))

                if pair in plotBusDict and \
                   plotBusDict[pair] not in measLegendLabelList:
                    measLegendLineList.append(measLinesDict[pair])
                    measLegendLabelList.append(plotBusDict[pair])
        #print(appName + ': measYmin: ' + str(measYmin) + ', measYmax: ' + str(measYmax), flush=True)

        #if plotStatsFlag:
        #    plt.sca(uiMeasAx)
        #    if len(measDataDict['Mean'][tsStartpt:tsEndpt]) > 0:
                # disable filling between lines because it's too much work
                # for big models and causes matplotlib to freeze
                #plt.fill_between(x=tsMeasDataDict['Mean'][tsStartpt:tsEndpt], y1=measDataDict['Mean'][tsStartpt:tsEndpt], y2=measDataDict['Stdev Low'][tsStartpt:tsEndpt], color=stdevBlue)
                #plt.fill_between(x=tsMeasDataDict['Mean'][tsStartpt:tsEndpt], y1=measDataDict['Mean'][tsStartpt:tsEndpt], y2=measDataDict['Stdev High'][tsStartpt:tsEndpt], color=stdevBlue)
                #plt.fill_between(x=tsMeasDataDict['Stdev Low'][tsStartpt:tsEndpt], y1=measDataDict['Stdev Low'][tsStartpt:tsEndpt], y2=measDataDict['Min'][tsStartpt:tsEndpt], color=minmaxBlue)
                #plt.fill_between(x=tsMeasDataDict['Stdev High'][tsStartpt:tsEndpt], y1=measDataDict['Stdev High'][tsStartpt:tsEndpt], y2=measDataDict['Max'][tsStartpt:tsEndpt], color=minmaxBlue)

        measDiffYmax = -sys.float_info.max
        measDiffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in measDataDict:
                tsStartpt, tsEndpt = tsSlice(tsMeasDataDict[pair],
                                             tsXmin, tsXmax)

                if len(measDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    diffMeasDataFlag = True
                    diffMeasLinesDict[pair+' Actual'].set_data(tsMeasDataDict[pair][tsStartpt:tsEndpt], measDataDict[pair][tsStartpt:tsEndpt])
                    measDiffYmin = min(measDiffYmin, min(measDataDict[pair][tsStartpt:tsEndpt]))
                    measDiffYmax = max(measDiffYmax, max(measDataDict[pair][tsStartpt:tsEndpt]))

        else:
            for pair in diffMeasDataDict:
                tsStartpt, tsEndpt = tsSlice(tsDiffMeasDataDict[pair],
                                             tsXmin, tsXmax)

                if len(diffMeasDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    diffMeasDataFlag = True
                    diffMeasLinesDict[pair].set_data(tsDiffMeasDataDict[pair][tsStartpt:tsEndpt], diffMeasDataDict[pair][tsStartpt:tsEndpt])
                    measDiffYmin = min(measDiffYmin, min(diffMeasDataDict[pair][tsStartpt:tsEndpt]))
                    measDiffYmax = max(measDiffYmax, max(diffMeasDataDict[pair][tsStartpt:tsEndpt]))

        #print(appName + ': measDiffYmin: ' + str(measDiffYmin) + ', measDiffYmax: ' + str(measDiffYmax), flush=True)

    # measurement voltage value plot y-axis zoom and pan calculation
    if not measDataFlag:
        print(appName + ': NOTE: no measurement voltage value data to plot yet\n', flush=True)
    #print(appName + ': measurement voltage value y-axis limits...', flush=True)
    newMeasYmin, newMeasYmax = yAxisLimits(measYmin, measYmax, uiMeasZoomSldr.val, uiMeasPanSldr.val)
    uiMeasAx.set_ylim(newMeasYmin, newMeasYmax)
    uiMeasAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiMeasAx.grid(True)

    if diffMeasDataFlag:
        # voltage value difference plot y-axis zoom and pan calculation

        # compare estimate with measurement min/max to get overall min/max
        diffYmin = min(estDiffYmin, measDiffYmin)
        diffYmax = max(estDiffYmax, measDiffYmax)

        newDiffYmin, newDiffYmax = yAxisLimits(diffYmin, diffYmax, uiDiffZoomSldr.val, uiDiffPanSldr.val)

        if not plotOverlayFlag and plotMagFlag:
            # always show 0% lower limit for magnitude % difference plots
            # when the upper limit drops below 1%, force it to 1%
            if newDiffYmax < 1.0:
                newDiffYmin, newDiffYmax = yAxisLimits(0.0, 1.0, uiDiffZoomSldr.val, uiDiffPanSldr.val)
            else:
                newDiffYmin, newDiffYmax = yAxisLimits(0.0, diffYmax, uiDiffZoomSldr.val, uiDiffPanSldr.val)

        uiDiffAx.set_ylim(newDiffYmin, newDiffYmax)

    # even though we aren't updating the estimate plot and may not be updating
    # the difference plot, the formatter and grid calls will make the plot
    # look good, including displaying the x-axis time, until those plots do
    # have data
    uiEstAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiEstAx.grid(True)

    uiDiffAx.xaxis.set_major_formatter(ticker.ScalarFormatter())
    uiDiffAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiDiffAx.grid(True)

    if plotStatsFlag:
        uiMeasAx.legend()
        if not plotOverlayFlag:
            uiDiffAx.legend()

    elif len(plotBusDict) > 0:
        if plotLegendFlag or len(measLegendLineList)<=10:
            cols = math.ceil(len(measLegendLineList)/8)
            uiMeasAx.legend(measLegendLineList, measLegendLabelList, ncol=cols)

            if not plotOverlayFlag:
                # bottom difference plot needs a legend because it has
                # double the lines with different line types
                cols = math.ceil((len(diffMeasLinesDict) + len(diffEstLinesDict))/8)
                uiDiffAx.legend(ncol=cols)

    # flush all the plot changes
    updatePlots()


def plotEstimateData():
    global estDiffYmin, estDiffYmax

    estDataFlag = False
    diffEstDataFlag = False

    if plotShowAllFlag:
        estXmax = -sys.float_info.max
        estYmax = -sys.float_info.max
        estYmin = sys.float_info.max
        for pair in estDataDict:
            if len(estDataDict[pair]) > 0:
                estDataFlag = True
                estLinesDict[pair].set_data(tsEstDataDict[pair], estDataDict[pair])
                estXmax = max(estXmax, int(tsEstDataDict[pair][-1]))
                estYmin = min(estYmin, min(estDataDict[pair]))
                estYmax = max(estYmax, max(estDataDict[pair]))

                if pair in plotBusDict and \
                   plotBusDict[pair] not in estLegendLabelList:
                    estLegendLabelList.append(plotBusDict[pair])
                    estLegendLineList.append(estLinesDict[pair])
        #print(appName + ': estYmin: ' + str(estYmin) + ', estYmax: ' + str(estYmax), flush=True)

        #if plotStatsFlag:
        #    plt.sca(uiEstAx)
        #    if len(estDataDict['Mean']) > 0:
                # disable filling between lines because it's too much work
                # for big models and causes matplotlib to freeze
                #plt.fill_between(x=tsEstDataDict['Mean'], y1=estDataDict['Mean'], y2=estDataDict['Stdev Low'], color=stdevBlue)
                #plt.fill_between(x=tsEstDataDict['Mean'], y1=estDataDict['Mean'], y2=estDataDict['Stdev High'], color=stdevBlue)
                #plt.fill_between(x=tsEstDataDict['Stdev Low'], y1=estDataDict['Stdev Low'], y2=estDataDict['Min'], color=minmaxBlue)
                #plt.fill_between(x=tsEstDataDict['Stdev High'], y1=estDataDict['Stdev High'], y2=estDataDict['Max'], color=minmaxBlue)

        if estDataFlag:
            uiEstAx.set_xlim(0, estXmax)
        else:
            return;

        if plotOverlayFlag:
            estDiffYmin = estYmin
            estDiffYmax = estYmax

            for pair in estDataDict:
                if len(estDataDict[pair]) > 0:
                    diffEstDataFlag = True
                    diffEstLinesDict[pair+' Est'].set_data(tsEstDataDict[pair], estDataDict[pair])

        else:
            estDiffYmin = sys.float_info.max
            estDiffYmax = -sys.float_info.max

            for pair in diffEstDataDict:
                if len(diffEstDataDict[pair]) > 0:
                    diffEstDataFlag = True
                    diffEstLinesDict[pair].set_data(tsDiffEstDataDict[pair], diffEstDataDict[pair])
                    estDiffYmin = min(estDiffYmin, min(diffEstDataDict[pair]))
                    estDiffYmax = max(estDiffYmax, max(diffEstDataDict[pair]))
        #print(appName + ': estDiffYmin: ' + str(estDiffYmin) + ', estDiffYmax: ' + str(estDiffYmax), flush=True)

    else:
        estXmax = -sys.float_info.max
        for pair in estDataDict:
            if len(estDataDict[pair]) > 0:
                estDataFlag = True
                estXmax = max(estXmax, int(tsEstDataDict[pair][-1]))

        if not estDataFlag:
            return

        tsZoom = int(uiTSZoomSldr.val)
        tsPan = int(uiTSPanSldr.val)
        if tsPan == 100:
            # this fills data from the right
            tsXmax = estXmax
            tsXmin = tsXmax - tsZoom

            # uncomment this code if filling from the left is preferred
            #if tsXmin < 0:
            #    tsXmin = 0
            #    tsXmax = tsZoom
        elif tsPan == 0:
            tsXmin = 0
            tsXmax = tsZoom
        else:
            tsMid = int(estXmax*tsPan/100.0)
            tsXmin = int(tsMid - tsZoom/2.0)
            tsXmax = tsXmin + tsZoom
            # this fills data from the right
            if tsXmax > estXmax:
                tsXmax = estXmax
                tsXmin = tsXmax - tsZoom
            elif tsXmin < 0:
                tsXmin = 0
                tsXmax = tsZoom
            # if filling from the left is preferred uncomment the lines
            # below and comment out the block if/elif block above
            #if tsXmin < 0:
            #    tsXmax = estXmax
            #    tsXmin = tsXmax - tsZoom
            #elif tsXmax > estXmax:
            #    tsXmin = 0
            #    tsXmax = tsZoom

        uiEstAx.set_xlim(tsXmin, tsXmax)
        #print(appName + ': tsXmin: ' + str(tsXmin), flush=True)
        #print(appName + ': tsXmax: ' + str(tsXmax), flush=True)

        estYmax = -sys.float_info.max
        estYmin = sys.float_info.max
        for pair in estDataDict:
            tsStartpt, tsEndpt = tsSlice(tsEstDataDict[pair], tsXmin, tsXmax)

            if len(estDataDict[pair][tsStartpt:tsEndpt]) > 0:
                estLinesDict[pair].set_data(tsEstDataDict[pair][tsStartpt:tsEndpt], estDataDict[pair][tsStartpt:tsEndpt])
                estYmin = min(estYmin, min(estDataDict[pair][tsStartpt:tsEndpt]))
                estYmax = max(estYmax, max(estDataDict[pair][tsStartpt:tsEndpt]))

                if pair in plotBusDict and \
                   plotBusDict[pair] not in estLegendLabelList:
                    estLegendLineList.append(estLinesDict[pair])
                    estLegendLabelList.append(plotBusDict[pair])
        #print(appName + ': estYmin: ' + str(estYmin) + ', estYmax: ' + str(estYmax), flush=True)

        #if plotStatsFlag:
        #    plt.sca(uiEstAx)
        #    if len(estDataDict['Mean'][tsStartpt:tsEndpt]) > 0:
                # disable filling between lines because it's too much work
                # for big models and causes matplotlib to freeze
                #plt.fill_between(x=tsEstDataDict['Mean'][tsStartpt:tsEndpt], y1=estDataDict['Mean'][tsStartpt:tsEndpt], y2=estDataDict['Stdev Low'][tsStartpt:tsEndpt], color=stdevBlue)
                #plt.fill_between(x=tsEstDataDict['Mean'][tsStartpt:tsEndpt], y1=estDataDict['Mean'][tsStartpt:tsEndpt], y2=estDataDict['Stdev High'][tsStartpt:tsEndpt], color=stdevBlue)
                #plt.fill_between(x=tsEstDataDict['Stdev Low'][tsStartpt:tsEndpt], y1=estDataDict['Stdev Low'][tsStartpt:tsEndpt], y2=estDataDict['Min'][tsStartpt:tsEndpt], color=minmaxBlue)
                #plt.fill_between(x=tsEstDataDict['Stdev High'][tsStartpt:tsEndpt], y1=estDataDict['Stdev High'][tsStartpt:tsEndpt], y2=estDataDict['Max'][tsStartpt:tsEndpt], color=minmaxBlue)

        estDiffYmax = -sys.float_info.max
        estDiffYmin = sys.float_info.max
        if plotOverlayFlag:
            for pair in estDataDict:
                tsStartpt, tsEndpt = tsSlice(tsEstDataDict[pair],
                                             tsXmin, tsXmax)

                if len(estDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    diffEstDataFlag = True
                    diffEstLinesDict[pair+' Est'].set_data(tsEstDataDict[pair][tsStartpt:tsEndpt], estDataDict[pair][tsStartpt:tsEndpt])
                    estDiffYmin = min(estDiffYmin, min(estDataDict[pair][tsStartpt:tsEndpt]))
                    estDiffYmax = max(estDiffYmax, max(estDataDict[pair][tsStartpt:tsEndpt]))

        else:
            for pair in diffEstDataDict:
                tsStartpt, tsEndpt = tsSlice(tsDiffEstDataDict[pair],
                                             tsXmin, tsXmax)

                if len(diffEstDataDict[pair][tsStartpt:tsEndpt]) > 0:
                    diffEstDataFlag = True
                    diffEstLinesDict[pair].set_data(tsDiffEstDataDict[pair][tsStartpt:tsEndpt], diffEstDataDict[pair][tsStartpt:tsEndpt])
                    estDiffYmin = min(estDiffYmin, min(diffEstDataDict[pair][tsStartpt:tsEndpt]))
                    estDiffYmax = max(estDiffYmax, max(diffEstDataDict[pair][tsStartpt:tsEndpt]))

        #print(appName + ': estDiffYmin: ' + str(estDiffYmin) + ', estDiffYmax: ' + str(estDiffYmax), flush=True)

    # state-estimator voltage magnitude plot y-axis zoom and pan calculation
    #print(appName + ': state-estimator voltage value y-axis limits...', flush=True)
    newEstYmin, newEstYmax = yAxisLimits(estYmin, estYmax, uiEstZoomSldr.val, uiEstPanSldr.val)
    uiEstAx.set_ylim(newEstYmin, newEstYmax)
    uiEstAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiEstAx.grid(True)

    # voltage value difference plot y-axis zoom and pan calculation
    if not plotOverlayFlag and not diffEstDataFlag:
        print(appName + ': NOTE: no voltage value difference data to plot yet\n', flush=True)
    #print(appName + ': voltage value difference y-axis limits...', flush=True)

    # compare estimate with measurement min/max to get overall min/max
    diffYmin = min(estDiffYmin, measDiffYmin)
    diffYmax = max(estDiffYmax, measDiffYmax)

    newDiffYmin, newDiffYmax = yAxisLimits(diffYmin, diffYmax, uiDiffZoomSldr.val, uiDiffPanSldr.val)

    if not plotOverlayFlag and plotMagFlag:
        # always show 0% lower limit for magnitude % difference plots
        # when the upper limit drops below 1%, force it to 1%
        if newDiffYmax < 1.0:
            newDiffYmin, newDiffYmax = yAxisLimits(0.0, 1.0, uiDiffZoomSldr.val, uiDiffPanSldr.val)
        else:
            newDiffYmin, newDiffYmax = yAxisLimits(0.0, diffYmax, uiDiffZoomSldr.val, uiDiffPanSldr.val)

    uiDiffAx.set_ylim(newDiffYmin, newDiffYmax)

    uiDiffAx.xaxis.set_major_formatter(ticker.ScalarFormatter())
    uiDiffAx.yaxis.set_major_formatter(ticker.ScalarFormatter())
    uiDiffAx.grid(True)

    if plotStatsFlag:
        uiEstAx.legend()
        if not plotOverlayFlag:
            uiDiffAx.legend()

    elif len(plotBusDict) > 0:
        if plotLegendFlag or len(estLegendLineList)<=10:
            cols = math.ceil(len(estLegendLineList)/8)
            uiEstAx.legend(estLegendLineList, estLegendLabelList, ncol=cols)

            if not plotOverlayFlag:
                # bottom difference plot needs a legend because it has
                # double the lines with different line types
                cols = math.ceil((len(diffMeasLinesDict) + len(diffEstLinesDict))/8)
                uiDiffAx.legend(ncol=cols)

    # flush all the plot changes
    updatePlots()


def plotPauseCallback(event):
    global plotPausedFlag
    # toggle whether plot is paused
    plotPausedFlag = not plotPausedFlag

    # update the button icon
    uiPauseAx.images[0].set_data(playIcon if plotPausedFlag else pauseIcon)

    if not plotPausedFlag:
        for pair in measDataDict:
            # add all the data that came in since the pause button was hit
            measDataDict[pair].extend(measDataPausedDict[pair])
            # clear the "paused" data so we build from scratch with the next pause
            measDataPausedDict[pair].clear()
            # now do the same extend/clear for timestamp data
            tsMeasDataDict[pair].extend(tsMeasDataPausedDict[pair])
            tsMeasDataPausedDict[pair].clear()

        for pair in estDataDict:
            estDataDict[pair].extend(estDataPausedDict[pair])
            estDataPausedDict[pair].clear()
            tsEstDataDict[pair].extend(tsEstDataPausedDict[pair])
            tsEstDataPausedDict[pair].clear()

        if not plotOverlayFlag:
            for pair in diffMeasDataDict:
                diffMeasDataDict[pair].extend(diffMeasDataPausedDict[pair])
                diffMeasDataPausedDict[pair].clear()
                tsDiffMeasDataDict[pair].extend(tsDiffMeasDataPausedDict[pair])
                tsDiffMeasDataPausedDict[pair].clear()

            for pair in diffEstDataDict:
                diffEstDataDict[pair].extend(diffEstDataPausedDict[pair])
                diffEstDataPausedDict[pair].clear()
                tsDiffEstDataDict[pair].extend(tsDiffEstDataPausedDict[pair])
                tsDiffEstDataPausedDict[pair].clear()

    plotDataCallback(None)


def plotShowAllCallback(event):
    global plotShowAllFlag
    # toggle whether to show all timestamps
    plotShowAllFlag = not plotShowAllFlag

    # update the button icon
    uiShowAx.images[0].set_data(checkedIcon if plotShowAllFlag else uncheckedIcon)
    plotDataCallback(None)


def plotDataCallback(event):
    plotMeasurementData()
    plotEstimateData()


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
        # add all possible pairs, which is fine even if some don't exist
        estToBusDict[cnid+',A'] = cnname+',A'
        estToBusDict[cnid+',B'] = cnname+',B'
        estToBusDict[cnid+',C'] = cnname+',C'
        estToBusDict[cnid+',S1'] = cnname+',S1'
        estToBusDict[cnid+',S2'] = cnname+',S2'
    print(appName + ': start bus to estimate mrid query results...', flush=True)
    pprint.pprint(busToEstDict)
    print(appName + ': end bus to estimate mrid query results', flush=True)


def initPlot(configFlag):
    global plotFig
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
                if buspair in busToMeasDict:
                    plotBusDict[buspair] = buspair
            else:
                if buspair+',A' in busToMeasDict:
                    plotBusDict[buspair+',A'] = buspair+',A'
                if buspair+',B' in busToMeasDict:
                    plotBusDict[buspair+',B'] = buspair+',B'
                if buspair+',C' in busToMeasDict:
                    plotBusDict[buspair+',C'] = buspair+',C'
                if buspair+',S1' in busToMeasDict:
                    plotBusDict[buspair+',S1'] = buspair+',S1'
                if buspair+',S2' in busToMeasDict:
                    plotBusDict[buspair+',S2'] = buspair+',S2'
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
                        continue

                    buspair = buspair.upper()
                    if ',' in buspair:
                        if buspair in busToMeasDict:
                            plotBusDict[buspair] = buspair
                    else:
                        if buspair+',A' in busToMeasDict:
                            plotBusDict[buspair+',A'] = buspair+',A'
                        if buspair+',B' in busToMeasDict:
                            plotBusDict[buspair+',B'] = buspair+',B'
                        if buspair+',C' in busToMeasDict:
                            plotBusDict[buspair+',C'] = buspair+',C'
                        if buspair+',S1' in busToMeasDict:
                            plotBusDict[buspair+',S1'] = buspair+',S1'
                        if buspair+',S2' in busToMeasDict:
                            plotBusDict[buspair+',S2'] = buspair+',S2'
            #print(appName + ': ' + str(plotBusDict), flush=True)
        except:
            print(appName + ': ERROR: node/phase pair configuration file state-plotter-config.csv does not exist.\n', flush=True)
            exit()

    for pair in plotBusDict:
        # create empty lists for the per pair data for each plot so we can
        # just do append calls when data to plot arrives
        estDataDict[pair] = []
        estDataPausedDict[pair] = []
        measDataDict[pair] = []
        measDataPausedDict[pair] = []

        if not plotOverlayFlag:
            diffEstDataDict[pair+' Est'] = []
            diffEstDataPausedDict[pair+' Est'] = []
            if sensorSimulatorRunningFlag:
                diffMeasDataDict[pair+' Meas'] = []
                diffMeasDataPausedDict[pair+' Meas'] = []

        # create a lines dictionary entry per node/phase pair for each plot
        measLinesDict[pair], = uiMeasAx.plot([], [], label=plotBusDict[pair])
        color = measLinesDict[pair].get_color()

        if plotOverlayFlag:
            estLinesDict[pair], = uiEstAx.plot([], [], label=plotBusDict[pair], linestyle='dashed', color=color)

            diffMeasLinesDict[pair+' Actual'], = uiDiffAx.plot([], [], label=plotBusDict[pair]+' Actual', color=color)
            diffEstLinesDict[pair+' Est'], = uiDiffAx.plot([], [], label=plotBusDict[pair]+' Est.', linestyle='dashed', color=color)
        else:
            estLinesDict[pair], = uiEstAx.plot([], [], label=plotBusDict[pair], color=color)

            if sensorSimulatorRunningFlag:
                diffEstLinesDict[pair+' Est'], = uiDiffAx.plot([], [], label=plotBusDict[pair]+' Est.', linestyle='dashed', color=color)
                diffMeasLinesDict[pair+' Meas'], = uiDiffAx.plot([], [], label=plotBusDict[pair]+' Meas.', color=color)
            else:
                diffEstLinesDict[pair+' Est'], = uiDiffAx.plot([], [], label=plotBusDict[pair]+' Est.', color=color)


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
         be plotted, e.g. "-bus 150" will plot all phases present (A, B, C, s1,
         s2).  Plotting combinations of bus,phase pairs is done by repeating
         the -bus option, e.g., "-bus 150,A -bus 160,A". Using -bus on the
         command line results in state-plotter-config.csv bus,phase pairs
         being disregarded.
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
        -phase: plots only the specified phase (A, B, C, s1, s2) given as the
         argument that follows. Combinations of phases in the same plot are
         done by repeating the -phase option, e.g., "-phase A -phase B" to
         exclude C, s1, and s2. If there are bus,phase pairs specified in
         state-plotter-config.csv or with the -bus option, they will be
         excluded if -phase is used and the phase of the pair differs. E.g.,
         "-bus 160,A -phase C" will not plot the 160,A pair since the -phase
         option specifies only phase C.
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
            plotPhaseList.append(arg.upper())
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
        elif arg.startswith('-nomatch'):
            plotMatchesFlag = False
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

    # subscribe as early as possible to simulation or sensor measurements
    # to avoid getting any estimates without corresponding measurements for
    # a timestamp
    if useSensorsForEstimatesFlag:
        # subscribe to all simulation measurements for the bottom plot
        gapps.subscribe(simulation_output_topic(simID), simulationCallback)

    # query to get connectivity node,phase pairs
    queryBusToEst()

    # query to get bus to sensor mrid mapping
    queryBusToSim()

    # query to get the nominimal voltage mapping
    queryVnom()

    # matplotlib setup done before receiving any messages that reference it
    initPlot(plotConfigFlag)

    if plotConfigFlag or len(plotBusList)>0:
        # determine what to plot based on the state-plotter-config file
        # and finish plot initialization
        configPlot(plotBusList)

    # determine which flavor of callback for measurements and estimates
    measCallback = measurementNoConfigCallback
    senCallback = sensorNoConfigCallback
    estCallback = estimateNoConfigCallback
    if plotConfigFlag or len(plotBusList)>0:
        measCallback = measurementConfigCallback
        senCallback = sensorConfigCallback
        estCallback = estimateConfigCallback
    elif plotStatsFlag:
        measCallback = measurementStatsCallback
        senCallback = sensorStatsCallback
        estCallback = estimateStatsCallback

    # subscribe to either sensor or simulation measurements for the top plot
    if useSensorsForEstimatesFlag:
        gapps.subscribe(service_output_topic('gridappsd-sensor-simulator',
                                             simID), measCallback)
    else:
        gapps.subscribe(simulation_output_topic(simID), measCallback)

        if sensorSimulatorRunningFlag:
            gapps.subscribe(service_output_topic('gridappsd-sensor-simulator',
                                                 simID), senCallback)

    # subscribe to state-estimator output--with config file
    gapps.subscribe(service_output_topic('state-estimator', simID), estCallback)

    # interactive plot event loop allows both the ActiveMQ messages to be
    # received and plot GUI events
    plt.show()

    gapps.disconnect()


if __name__ == '__main__':
    _main()

