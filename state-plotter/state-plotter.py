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
vLinesDict = {}
angDataDict = {}
angDataDictPaused = {}
angLinesDict = {}
tsInit = 0
pausedFlag = False
showFlag = False
firstPassFlag = True
plotNumber = 0


def measurementConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']
    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    global tsInit, PausedFlag

    for item in estVolt:
        pair = item['ConnectivityNode'] + ',' + item['phase']

        if pair in nodePhasePairDict:
            matchCount += 1
            v = item['v']
            angle = item['angle']

            print(sys.argv[0] + ': node,phase pair: ' + pair)
            print(sys.argv[0] + ': timestamp: ' + str(ts))
            print(sys.argv[0] + ': v: ' + str(v))
            print(sys.argv[0] + ': angle: ' + str(angle) + '\n')

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
                vDataDictPaused[pair].append(v)
                angDataDictPaused[pair].append(angle)
            else:
                vDataDict[pair].append(v)
                angDataDict[pair].append(angle)

            # no reason to keep checking more pairs if we've found all we
            # are looking for
            if matchCount == len(nodePhasePairDict):
                break

    # update plot with the new data
    plotData(None)


def measurementNoConfigCallback(header, message):
    msgdict = message['message']
    ts = msgdict['timestamp']
    estVolt = msgdict['Estimate']['SvEstVoltages']
    matchCount = 0
    global tsInit, pausedFlag, firstPassFlag, plotNumber

    for item in estVolt:
        pair = item['ConnectivityNode'] + ',' + item['phase']
        v = item['v']
        angle = item['angle']

        print(sys.argv[0] + ': node,phase pair: ' + pair)
        print(sys.argv[0] + ': timestamp: ' + str(ts))
        print(sys.argv[0] + ': v: ' + str(v))
        print(sys.argv[0] + ': angle: ' + str(angle) + '\n')

        if firstPassFlag:
            vDataDict[pair] = []
            vDataDictPaused[pair] = []
            angDataDict[pair] = []
            angDataDictPaused[pair] = []
            # create a lines dictionary entry per node/phase pair for each plot
            vLinesDict[pair], = vAx.plot([], [], label=pair)
            angLinesDict[pair], = angAx.plot([], [], label=pair)

        matchCount += 1

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
            vDataDictPaused[pair].append(v)
            angDataDictPaused[pair].append(angle)
        else:
            vDataDict[pair].append(v)
            angDataDict[pair].append(angle)

        # no reason to keep checking more pairs if we've found all we
        # are looking for
        if plotNumber>0 and matchCount==plotNumber:
            break

    # only do the dictionary initializtion code on the first call
    firstPassFlag = False

    # update plot with the new data
    plotData(None)


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
        # determine how many points are being plotted to give the properly
        # sized slice of the full lists of data, which impacts y-axis scaling
        tsZoom = int(tsZoomSldr.val)
        points = int(tsZoom/3.0) + 1
        if points > len(tsData):
            points = len(tsData)

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
        #print(sys.argv[0] + ': xmin: ' + str(xmin))
        #print(sys.argv[0] + ': xmax: ' + str(xmax))

        if xmin > 0:
            startpt = int(xmin/3.0)
        else:
            startpt = 0
        endpt = int(xmax/3.0) + 1
        #print(sys.argv[0] + ': startpt: ' + str(startpt))
        #print(sys.argv[0] + ': endpt: ' + str(endpt) + '\n')

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
    #print(sys.argv[0] + ': calculated newvYmin: ' + str(newvYmin))
    #print(sys.argv[0] + ': calculated newvYmax: ' + str(newvYmax))

    if newvYmin < vYmin:
        newvYmin = vYmin
        newvYmax = newvYmin + vHeight
    elif newvYmax > vYmax:
        newvYmax = vYmax
        newvYmin = newvYmax - vHeight
    #print(sys.argv[0] + ': final newvYmin: ' + str(newvYmin))
    #print(sys.argv[0] + ': final newvYmax: ' + str(newvYmax) + '\n')

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
    #print(sys.argv[0] + ': calculated newangYmin: ' + str(newangYmin))
    #print(sys.argv[0] + ': calculated newangYmax: ' + str(newangYmax))

    if newangYmin < angYmin:
        newangYmin = angYmin
        newangYmax = newangYmin + angHeight
    elif newangYmax > angYmax:
        newangYmax = angYmax
        newangYmin = newangYmax - angHeight
    #print(sys.argv[0] + ': final newangYmin: ' + str(newangYmin))
    #print(sys.argv[0] + ': final newangYmax: ' + str(newangYmax) + '\n')

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
    print(cnPairDict)

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
                 
                pair = line.split(',')
                if len(pair)==2 and pair[0].upper() in cnPairDict:
                    nodePhasePairDict[cnPairDict[pair[0].upper()] + ',' + pair[1]] = line
    except:
        print(sys.argv[0] + ': Node/Phase pair configuration file state-plotter-config.csv does not exist.\n')
        exit()

    #print(sys.argv[0] + ': ' + str(nodePhasePairDict))


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
    tsZoomSldr = Slider(tsZoomAx, 'show all           zoom', 1, 100, valinit=30, valfmt='%d', valstep=1.0)
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
        print('Usage: ' + sys.argv[0] + ' sim_id sim_req\n')
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

    if plotConfigFlag:
        # GridAPPS-D query to get connectivity node,phase pairs to determine
        # what to plot based on the state-plotter-config file
        queryConnectivityPairs()

        # subscribe to state-estimator measurement output
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.'+
                        sys.argv[1], measurementConfigCallback)
    else:
        # subscribe to state-estimator measurement output
        gapps.subscribe('/topic/goss.gridappsd.state-estimator.out.'+
                        sys.argv[1], measurementNoConfigCallback)

    # matplotlib setup
    initPlot(plotConfigFlag, plotLegendFlag)

    # interactive plot event loop allows both the ActiveMQ messages to be
    # received and plot GUI events
    plt.show()

    gapps.disconnect()


if __name__ == '__main__':
    _main()
