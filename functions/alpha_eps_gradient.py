import numpy as np
import scipy.optimize as opt
import scipy.linalg as la
import pylab            # Thiis imports matplotlib.pyplot and numpy!!
import pickle
import sys
import networkx as nx

import scipy.io as sio

dictionaries_file_path          = 'python_files/dictionary_'             # Dictionaries files
matrices_file_path              = 'python_files/pyoutMatrices_'
durations_files_name            = 'python_files/pyoutOptimization_'
inflows_outflows_file_name      = 'python_files/inflowsOutflows_'

# Global variables
np.set_printoptions(formatter={'float': '{: 0.4f}'.format})
f = open(matrices_file_path+'n', 'rb')
n = pickle.load(f)
f.close()
I = np.identity(n)




def getActiveConstraints(M, d, r):          # Returns active constraints
    active = []
    l = M.shape[0]
    for row in range(l):
        if np.absolute(M[row,:]@d-r[row])<1e-3:
            active.append(row)
    return active


def getActiveM(M, active_constraints):      # Returns active matrix M
    i=0
    m=M.shape[1]
    for row in active_constraints:
        if i==0:
            Ma = M[row,:].reshape(1,m)
        else:
            Ma = np.concatenate((Ma, M[row,:].reshape(1,m)), axis=0)
        i+=1
    return Ma


def traceGramian( s, A, B, C, eps_inv ):

    W = la.solve_continuous_lyapunov( (A-s*I) , -B@B.transpose() )
    ff = np.trace(C @ W @ C.T ) - eps_inv
    return ff


def checkConstraint(d, M, r):
    return la.norm(M@d-r)


def getArgument(argName, listOfArguments):
    i=0
    for l in listOfArguments:
        if l==str('-'+argName):
            return listOfArguments[i+1]
            break
        i+=1
    return None






#######################   MAIN   ########################
def main():
    if getArgument('eps_inv',sys.argv):
        eps_inv  = float(getArgument('eps_inv',sys.argv))
    else:
        eps_inv = 1
    if getArgument('max_iter',sys.argv):
        max_iter  = float(getArgument('max_iter',sys.argv))
    else:
        max_iter = 5
    if getArgument('gamma', sys.argv):
        gam = float(getArgument('gamma', sys.argv))
    else:
        gam = .1
    print('\n Running gradient-descent algorithm with:')
    print('* 1/epsilon = '+str(eps_inv))
    print('* Maximum no. of iterations = ' + str(max_iter))
    print('* Gamma (descent stepsize) = ' + str(gam))

    f = open(inflows_outflows_file_name+'inflows', 'rb')
    x0 = pickle.load(f)
    f.close()
    f = open(inflows_outflows_file_name+'outflows', 'rb')
    outflows = np.diag(pickle.load(f)) + np.diag(1e-1*np.random.rand(n)) # The second term takes care of errors in the imported sumo network
    f.close()


    B = np.dot(x0.reshape(n,1),x0.reshape(1,n))
    f = open(matrices_file_path+'C', 'rb')
    C = pickle.load(f)
    f.close()
    f = open(matrices_file_path+'M', 'rb')
    M0 = pickle.load(f)
    f.close()
    f = open(matrices_file_path+'K', 'rb')
    K = pickle.load(f)
    f.close()
    f = open(matrices_file_path+'ah', 'rb')
    ah = pickle.load(f)
    f.close()
    ah = ah - outflows.flatten('F')

    l = M0.shape[0]
    m = M0.shape[1]


    # Equality constraints
    r0 = np.ones(l)
    # Inequality constraints
    II = np.identity(m)
    M = np.concatenate((M0, II), axis=0)
    M = np.concatenate((M, II), axis=0)
    rz = np.zeros(m)
    r = np.concatenate((r0,rz))
    ro = np.ones(m)
    r = np.concatenate((r,ro))



    # Construct feasible d
    d = la.pinv(M0)@r0
    f = open(durations_files_name+'dFeasible', 'wb')
    pickle.dump(d, f)
    f.close()
    a = K@d + ah
    A = a.reshape(n,n).T




    i = 0
    mem_J = []
    iterations = []
    mem_alpha_eps = []
    flag = True
    alpha_eps = 1
    lb_alpha_epsilon = 1e-3
    ub_alpha_epsilon = 1e3
    while i<max_iter and flag==True:# and alpha_eps>0: # np.absolute(deltaJ) > 1e-2 and i<1000:

        # Determine alpha_epsilon
        alphaA = np.max(np.real(la.eigvals(A)))
        if alphaA > 0:
            print('Oops! alpha(A)>0  (i='+str(i)+'), alphaA='+str(alphaA))
        if traceGramian( alphaA+lb_alpha_epsilon, A, B, C, 0 )<0:
            print('Oops! Tr( W(alpha(A)) ) < 0!! Try with larger  lower bound on initialization!')
        if traceGramian( ub_alpha_epsilon, A, B, C, eps_inv )>0:
            print('Oops! Tr( W(+infty) )-eps_inv > 0!! Try with larger initialization upper bound or larger epsilon_inv')
        x = opt.brentq(traceGramian, alphaA + lb_alpha_epsilon, ub_alpha_epsilon, xtol=1e-5, args=(A, B, C, eps_inv), full_output = True)
        alpha_eps = x[0]
        mem_alpha_eps.append(alpha_eps)
        if alpha_eps < np.max(np.real(la.eigvals(A))) or x[1].converged==False:
            print('Oops! alpha_eps(A) < alpha(A)')
            sys.exit('alpha_eps(A) < alpha(A)     OR         fsolve did non find a solution')



        # Determine Gradient
        Q = la.solve_continuous_lyapunov( (A-alpha_eps*I).transpose()  , -C.transpose()@C )
        P = la.solve_continuous_lyapunov( (A-alpha_eps*I)              , -B@B.transpose() )
        tr = np.trace(Q@P)
        Delta_A  = (Q@P)/tr
        gradA = Delta_A


        # Gradient projection
        delta_A = Delta_A.flatten('F')
        delta_d = K.T @ delta_A
        active_constraints = getActiveConstraints(M, d, r)
        Ma = getActiveM(M, active_constraints)
        m = Ma.shape[1]
        Proj = np.identity(m) - Ma.T @ la.pinv(Ma @ Ma.T) @ Ma  # Projection matrix
        theta = Proj @ delta_d
        d = d - gam * theta



        # Check constraints still holds
        if np.absolute(checkConstraint(d, M0, r0)) > 1e-4:
            print('Oops! Constraint is not satisfied')

        # Update A
        a = K@d + ah
        A = a.reshape(n,n).T

        # Check optimality
        if np.absolute(la.norm(theta))<1e-2: # Then necessary KKT are satisfied
            lamb = la.pinv(Ma.T)@theta
            flag=False # Terminate
            print('Lambda= ',lamb)
            print('(All lambda should be non-negative)\n')




        W = la.solve_continuous_lyapunov( A  , -B@B.transpose() )
        curJ = np.trace(C @ W @ C.transpose())
        mem_J.append(curJ)
        if (i > 1):
            deltaJ = mem_J[-1] - mem_J[-2]
        iterations.append(i)
        print('iteration='+str(i)+',   alphaA='+str(round(alphaA,3))+',   alpha_eps='+str(round(alpha_eps,3))+',   Trace(W)='+str(round(curJ,3)) )
        i += 1

    f = open(durations_files_name + 'dOptimal', 'wb')
    pickle.dump(d, f)
    f.close()


    pylab.figure()
    pylab.plot(iterations, mem_alpha_eps, '-o')
    pylab.title('alpha_epsilon vs iterations')

    pylab.figure()
    pylab.plot(iterations, mem_J, '-o')
    pylab.title('Trace of weighted Gramian vs iterations')

    print('--------------------------------')
    print('* First iteration:')
    print('     Trace(W(A)) = '+str(mem_J[0]))
    print('     Alpha_epsilon =', mem_alpha_eps[0])

    print('* Final iteration:')
    print('   Final value of Trace( W(A) ) = '+str(mem_J[-1]))
    print('   Alpha_epsilon = ',mem_alpha_eps[-1])

    print('* Optimal value of d = ' + str(d))
    print('--------------------------------')
    print('* NOTE:      if alpha_epsilon>0 then increase 1/epsilon (performance is not obtainable)')
    print('             if alpha_epsilon<0 then decrease 1/epsilon (better can be obtained)')

    print('--------------------------------')
    print('*** Success!!!  Optimization terminated and optimal durations saved.\n')


    pylab.ion()
    pylab.show()
    # pylab.draw()
    # pylab.pause(0.001)
    # input("Press [enter] to continue.")



if __name__ == "__main__":
    main()