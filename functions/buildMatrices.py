# This script reads dictionary files created with  main_createDictionaries.py
# and generates the matrices need to run the spectral abscissa optimization
#
#   INPUT PARAMETERS:
#       -h : cell discretization step size
#
#   OUTPUT:
#       file containing road lengths (sigma)
#       file containing system size (n)
#       file containing constant a_h
#       file containing matrix K
#       file containing matrix M
#       file containing matrix C






import numpy as np
import pickle
import sys
import scipy.linalg as la
import networkx as nx
import pylab


dictionaries_file_path  = 'python_files/dictionary_'             # Dictionaries files
matrices_file_path = 'python_files/pyoutMatrices_'




def getBlock(i,j, A, sigma):            # Returns block (i,j) where i,j \in \until{nr}
    if i<0 or i>len(sigma) or j<0 or j>len(sigma):
        print('Indices out of bounds in getBlock')
    rs = int(np.sum(sigma[:i]))     # start row
    rf = int(np.sum(sigma[:i+1]))   # final row
    cs = int(np.sum(sigma[:j]))     # start row
    cf = int(np.sum(sigma[:j+1]))   # final row
    return np.copy(A[rs:rf, cs:cf])

def setBlock(i,j, A_ij, A, sigma):      # Returns block (i,j) where i,j \in \until{nr}
    if i<0 or i>len(sigma) or j<0 or j>len(sigma):
        print('Indices out of bounds in setBlock')
    A = np.copy(A)
    rs = int(np.sum(sigma[:i]))     # start row
    rf = int(np.sum(sigma[:i+1]))   # final row
    cs = int(np.sum(sigma[:j]))     # start row
    cf = int(np.sum(sigma[:j+1]))   # final row
    A[rs:rf,cs:cf] = A_ij
    return A


def getArgument(argName, listOfArguments):
    i=0
    for l in listOfArguments:
        if l==str('-'+argName):
            return listOfArguments[i+1]
            break
        i+=1
    return None








################       MAIN SCRIPT      ##############
def main():
    if getArgument('h',sys.argv):
        h = float(getArgument('h',sys.argv))
    else:
        h=80
    print('Running script that generates matrices A, K, M, with  h='+str(h)+'  ...')
    f = open(dictionaries_file_path +'lights', 'rb')
    lights = pickle.load(f)
    f.close()
    f = open(dictionaries_file_path +'phases', 'rb')
    phases = pickle.load(f)
    f.close()
    f = open(dictionaries_file_path +'roads', 'rb')
    roads = pickle.load(f)
    f.close()




    ## Compute road sizes sigma
    print('* Working on vector of road lengths sigma...', end="", flush=True)
    sigma = []
    gamma = []
    for l in roads:
        lane_length = max(1,int( round( float(l['len'])/h  ,0 ) ))
        sigma.append(lane_length)
        gamma.append(float(l['speed']))
    f = open(matrices_file_path +'sigma', 'wb')
    pickle.dump(sigma, f)
    f.close()
    print('[DONE]')
    n = np.sum(sigma)  # Adjacency matrix dimension
    f = open(matrices_file_path + 'n', 'wb')
    pickle.dump(n, f)
    f.close()
    print('* System size n= ' + str(n))




    ## Compute vector a_h
    print('* Working on vector a_h...', end="", flush=True)
    i = 0
    A = np.zeros((n,n))
    for l in roads:
        sigma_i = sigma[i]
        gamma_i = gamma[i]
        Di = np.identity( sigma_i-1 )
        Di = np.concatenate((np.zeros((1, sigma_i-1)), Di), axis=0)
        Di = np.concatenate((Di, np.zeros((sigma_i, 1))),   axis=1)
        Di = Di - np.identity(sigma_i)
        Di = gamma_i/h*Di
        if l['signalized']=='Y':
            Di[-1,-1] = 0
        else:
            Di[-1, -1] = -1     # If lane is not signalized then outflow is constant
        A = setBlock(i, i, Di, A, sigma)
        i += 1

    # Add nonsignalized intersections
    j = 0
    for ph in phases:
        if ph['signalized']=='N':
            o = ph['origin']  # id of origin road
            for d in ph['dest']:
                orig_size = sigma[o]  # (The list of roads is sorted by id by construction)
                dest_size = sigma[d]
                A_ij = np.zeros((dest_size, orig_size))
                A_ij[0, -1] = 1/len(ph['dest'])
                A = setBlock(d, o, A_ij, A, sigma)
        j += 1

    ah = A.flatten('F')
    f = open(matrices_file_path +'ah', 'wb')
    pickle.dump(ah, f)
    f.close()
    print('[DONE]')







    ## Construct matrix K
    print('* Working on matrix K...', end="", flush=True)
    m = 0       # Number of phases
    for tl in lights:
        m += len(tl['phases'])


    i = 0       # index of columns in K
    # K = np.zeros((n**2,m))
    K = np.empty((n ** 2, m))
    M = np.zeros((len(lights), m))
    d_roads = []                        # List containing the sorted sequence of roads associated with d
    for tl in lights:
        intersection_phases = [phases[i] for i in tl['phases']]     # list containing the phases associated with tl
        for ph in intersection_phases:
            o_r = ph['origin']          # id of origin road
            o_size = sigma[o_r]         # size of origin road
            destinations = ph['dest']       # id of destination roads for current phase
            A_i = np.zeros((n, n))
            for d_r in destinations:
                d_size = sigma[d_r]
                A_ii = np.zeros((o_size, o_size))
                A_ii[-1,-1] = -1
                A_i = setBlock(o_r, o_r, A_ii, A_i, sigma)
                A_ij = np.zeros((d_size, o_size))
                A_ij[0, -1] = 1/len(destinations)
                A_i = setBlock(d_r, o_r, A_ij, A_i, sigma)
            a_i = A_i.flatten('F').reshape(n**2,1)
            K[:,i] = a_i.T
            d_roads.append(o_r)
            i+=1
    f = open(matrices_file_path + 'K', 'wb')
    pickle.dump(K, f, protocol=4)
    f.close()
    print('[DONE]')
    f = open(matrices_file_path +'d_roads', 'wb')
    pickle.dump(d_roads, f, protocol=4)
    f.close()
    print('* List of ordered roads associated with d: '+str(d_roads))





    ## Construct matrix M
    print('* Working on constraint matrix M...', end="", flush=True)
    j = 0
    for tl in lights:
        m = np.ones((1, len(tl['phases'])))       # Durations of edges of the same intersection must sum up to T
        if j == 0:
            M = m
        else:
            Z = np.zeros((M.shape[0], m.shape[1]))
            M = np.concatenate((M, Z), axis=1)
            z = np.zeros((1, M.shape[1] - m.shape[1]))
            m = np.concatenate((z, m), axis=1)
            M = np.concatenate((M, m), axis=0)
        j += 1
    f = open(matrices_file_path +'M', 'wb')
    pickle.dump(M, f)
    f.close()
    print('[DONE]')






    # Compute matrix C
    print('* Working on observations matrix C...', end="", flush=True)
    i = 0
    empty = True
    for ss in sigma:
        if roads[i]['signalized']=='Y':
            II = np.identity(ss)
            c = II[-1,:]
            c = c.reshape(1,ss)
            if empty:
                C = c
                empty = False
            else:
                Z = np.zeros((C.shape[0], sigma[i]))
                C = np.concatenate((C, Z), axis=1)
                z = np.zeros((1, C.shape[1] - c.shape[1]))
                c = np.concatenate((z, c), axis=1)
                C = np.concatenate((C, c), axis=0)
        else:
            if empty:
                C = np.zeros((1, sigma[i]))
                empty = False
            else:
                Z = np.zeros((C.shape[0], sigma[i]))
                C = np.concatenate((C, Z), axis=1)

        i += 1

    f = open(matrices_file_path +'C', 'wb')
    pickle.dump(C, f)
    f.close()
    print('[DONE]')

    print('--------------------------------')
    print('*** Success!!!  Matrices created.\n')

    # l = M.shape[0]
    # r = np.ones(l)
    # d = la.pinv(M)@r
    d=np.ones(M.shape[1])
    a = K@d + ah
    A = a.reshape(n,n).T
    G = nx.from_numpy_matrix(np.array(A))
    nx.draw(G, with_labels=True)
    pylab.ion()
    pylab.show()
    # pylab.pause(0.001)
    # input("Press [enter] to continue.")
    # pylab.draw()
    # pylab.pause(0.001)
    # input("Press [enter] to continue.")





if __name__ == "__main__":
    main()