"""
This file conducts a matching between the PUF and the SCF using minimum
distance. In the event of ties (which should be very common due to the multiple
imputation in the SCF), we split the PUF record into several different records,
with the weight split based on the relative weights among the SCF matches.

In our case, we use age and the comparable income measure:
    Wage/salary income
    Farm net income
    Sch C income (sole proprietorship)
    Sch E income
    Taxable and nontaxable interest income
    Dividends
    Unemployment Insurance
    Social Security
    Pensions and annuities
In this version, distance is defined as
    sqrt((age_scf - age_puf)^2 / Var(age_scf) +
         (inc_scf - inc_puf)^2 / Var(inc_scf))
The variance is taken over the SCF measure because the distance is calculated
relative to each observation in the PUF.

The output of this program is a file containing pairings of units from the PUF
and from the SCF.

This program is nearly identical to match_1A.py. The distinction is that in the
case of n SCF observations matched to a PUF observation, this
randomly selects one to match instead of producing n matches.
"""
import os
import numpy as np
import pandas as pd
import copy
import taxcalc
from taxcalc import *

# Read in the SCF data
CUR_PATH = os.path.abspath(os.path.dirname(__file__))
SCF = pd.read_csv(os.path.join(CUR_PATH, 'scf.csv'))

# Get the PUF data aged to 2015
recs = Records('puf.csv')
pol = Policy()
calc = Calculator(policy=pol, records=recs, verbose=False)
calc.advance_to_year(2015)
calc.calc_all()
recvars = ['e00200', 'e02100', 'e00900', 'e02000', 'e00400', 'e00300',
           'e00600', 'e02300', 'e01500', 'e02400', 'age_head', 's006', 'RECID']
PUF = calc.dataframe(recvars)

PUF['compincome'] = (PUF['e00200'] + PUF['e02100'] + PUF['e00900'] +
                     PUF['e02000'] + PUF['e00400'] + PUF['e00300'] +
                     PUF['e00600'] + PUF['e02300'] + PUF['e01500'] +
                     PUF['e02400'])

def Variance(scf, varname):
    """
    Calculates the weighted variance for the SCF sub-dataset passed to it.
    """
    assert varname in ['age', 'compincome']
    var = np.array(scf[varname])
    wgt = np.array(scf['wgt'])
    avg = np.average(var, weights=wgt)
    varian = np.average((var - avg)**2, weights=wgt)
    return varian
    

def Match(puf, scf):
    """
    This function takes in a PUF dataset and a SCF dataset and matches the
    results. It returns a dataset of pairings of PUF and SCF records and the
    weight accorded to each.
    """
    incb = np.array(scf['compincome'])
    ageb = np.array(scf['age'])
    puf_list = list()
    scf_list = list()
    wt_list = list()
    # Calculate distance
    v_age = Variance(scf, 'age')
    v_inc = Variance(scf, 'compincome')
    # Iterate over PUF observations
    for i in range(len(puf)):
        scf1 = copy.deepcopy(scf)
        # Grab weight and income for PUF unit
        inca = puf.loc[i, 'compincome']
        agea = puf.loc[i, 'age_head']
        scf1['dist'] = np.sqrt((ageb - agea)**2 / v_age +
                               ((incb - inca)**2 / v_inc))
        # Grab matched observations
        scf_matched = scf1[scf1['dist'] == min(scf1['dist'])]
        # Randomly select 1 SCF match
        scf_matched2 = scf_matched.sample(n=1, weights='wgt').reset_index()
        # Save each matching
        puf_list.append(puf.loc[i, 'RECID'])
        scf_list.append(scf_matched2.loc[0, 'Y1'])
        wt_list.append(puf.loc[i, 's006'])
    # Save results to a DataFrame
    match1 = pd.DataFrame({'pufseq': puf_list, 'scf_seq': scf_list,
                           'wgt': wt_list})
    return match1

# Call the Match function for each age group and save the matchings
match_res = Match(PUF, SCF).round(2)
match_res.to_csv(os.path.join(CUR_PATH, 'match_2C_results.csv'), index=False)

print('Matching complete')
print('Length of PUF: ' + str(len(PUF)))
print('Length of SCF: ' + str(len(SCF)))
print('Length of Match: ' + str(len(match_res)))
