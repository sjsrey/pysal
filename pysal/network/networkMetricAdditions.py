# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 16:38:53 2016

@author: eheldero
"""

import numpy as np
import operator

#use graph edges
def buildMatrices(ntw):
    """
    Used to build square adjacency and distance matrices from pysal Network objects
    """
    gr = ntw.graphedges
    gl = ntw.graph_lengths
    
    li = []
    for l in gr:
        li.append(l[0])
        li.append(l[1])
        
    uNodes = set(li)
    
    #clean node list
    cNodes = {}
    for i, c in enumerate(uNodes):
        cNodes[c] = i
    
    cgr = []
    for i, edge in enumerate(gr):
        e1 = cNodes[edge[0]]
        e2 = cNodes[edge[1]]
        cgr.append([e1,e2])
    
    adj = np.zeros((len(cNodes),len(cNodes)))
    dst = np.zeros((len(cNodes),len(cNodes)))
    
    for i, e in enumerate(cgr):
        adj[e[0],e[1]] = 1
    
        dst[e[0],e[1]] = gl[tuple(gr[i])]
    
    adjD,dstD = addDiag(adj,dst)
    
    return adjD, dstD
"""    
adj, dst = buildMatrices(ntw)

Due to a pre-existing bug in the pysal network module
this may throw an error if the line shapefile has closed loops
that are unconnected to other parts of the shapefile
"""
##testing
adj = [[0,1,1,1,0],[1,0,1,0,0],[1,1,0,1,1],[1,0,1,0,0],[0,0,1,0,0]]
dst = [[0,5,3,6,0],[5,0,2,0,0],[3,2,0,4,3.5],[6,0,4,0,0],[0,0,3.5,0,0]]

# adj = binary adjacency matrix
# dst = distance adj matrix

def addDiag(adj, dst):
    """
    Used internally to add diagonals to matrices
    """
    adjD = adj
    dstD = dst
    for i, li in enumerate(adj):
        for j in range(i,len(li),1):
            adjD[j][i] = adj[i][j]
            dstD[j][i] = dst[i][j]
    return adjD,dstD

def evcounts(mat):
    """
    Used to generate edge and node counts
    """
    ne = 0.
    for line in adj:
        ne = ne + sum(line)
    nn = len(adj)
    return ne, nn

def nodeDeg(adj):
    """
    Degree centrality of each node in the network
    """
    nl = range(len(adj))
    nd = {}
    for i,n in enumerate(nl):
        tl = adj[i]
        nd[n] = sum(tl)
    return nd

def betaIndex(adj):
    """
    Beta index from the adjacency matrix
    """
    ne, nn = evcounts(adj)
    bi = ne/nn
    return bi

def alphaIndex(adj):
    """
    Alpha index from the adjacency matrix
    """
    ne, nn = evcounts(adj)
    ai = (ne-nn+1)/(2*nn-5)
    return ai

def gammaIndex(adj):
    """
    Gamma index from the adjacency matrix
    """
    ne, nn = evcounts(adj)
    gi = ne/(3*nn-6)
    return gi

def etaIndex(adj, dst):
    """
    Eta index from the distance matrix
    """
    ne, nn = evcounts(adj)
    td = 0
    for line in dst:
        td = td + sum(line)
    ei = td/ne
    return ei

def piIndex(netDiam, dst):
    """
    Pi index from the distance matrix
    """
    td = 0
    for line in dst:
        td = td + sum(line)
    pInd = td/netDiam[2]
    return pInd

def dstToDict(dst):
    """
    Used internally to convert internode distances to format for 
    Dijkstra's algorithm implementation
    """
    finalDict = {}
    for j,list in enumerate(dst):
        tDict = {}
        for i,val in enumerate(list):
            if val != 0:
                tDict[i] = val
        finalDict[j] = tDict
    return finalDict

def diam(distDicts):
    """
    Network diameter from Dijkstra's algorithm
    returns tuple of (start node, end node, diameter)
    """
    md = 0
    for k in distDicts:
        mt = max(distDicts[k].iteritems(), key = operator.itemgetter(1))
        if mt[1] > md:
            md = mt[1]
            end = mt[0]
            start = k
    return start, end, md
    
def closeCent(distDicts):
    """
    Three different closeness centrality metrics for each node
    Output is list of format: 
    [[node n, harmonic centrality n, closeness centrality n, Dangalchev centrality n],[...]]
    """
    allCent = []
    for k in distDicts:
        tempHarmonic = 0.
        tempCent = 0.
        tempDangalchev = 0.
        for j in distDicts[k]:
            if j != k:
                tempHarmonic = tempHarmonic + 1/distDicts[k][j]
                tempCent = tempCent + distDicts[k][j]
                tempDangalchev = tempDangalchev + 1/2**distDicts[k][j]
        baseCent = 1/tempCent
        tl = [k,tempHarmonic,baseCent,tempDangalchev]
        allCent.append(tl)
    return allCent
    

def shortDist(adj,dst):
    """
    Implementation of Dijkstra's algorithm for shortest distance between
    all paired nodes
    """
    nodes = range(len(adj))
    dstDicts = {}
    distances = dstToDict(dst)
    for i,n in enumerate(nodes):
        
        unvisited = {node: None for node in nodes}
        visited = {}
        
        current = n
        currentDistance = 0
        unvisited[current] = currentDistance
        
        while unvisited:
            for neighbor, distance in distances[current].items():
                if neighbor not in unvisited: continue
                newDistance = currentDistance+distance
                if unvisited[neighbor] is None or unvisited[neighbor] > newDistance:
                    unvisited[neighbor] = newDistance
            visited[current] = currentDistance
            try:
                del unvisited[current]
            except:
                pass
                #print 'error:',i,n,current, unvisited
            if not unvisited: break
            candidates = [node for node in unvisited.items() if node[1]]
            #print candidates
            try:
                current, currentDistance = sorted(candidates, key = lambda x: x[1])[0]
            except:
                pass
                #print 'error',i,n,candidates, unvisited
        
        dstDicts[n] = visited
    
    return dstDicts