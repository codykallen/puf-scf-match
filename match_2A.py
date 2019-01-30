"""
This file conducts a matching between the PUF and the SCF using minimum
distance, with distance defined using the Euclidean norm. In the event of ties
(which should be very common due to the multiple imputation in the SCF), we
split the PUF record into several different records, with the weight split
based on the relative weights among the SCF matches.

In our case, the measure of interest is the comparable income measure:
    Wage/salary income
    Farm net income
    Sch C income (sole proprietorship)
    Sch E income
    Taxable and nontaxable interest income
    Dividends
    Unemployment Insurance
    Social Security
    Pensions and annuities

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
           'e00600', 'e02300', 'e01500', 'e02400', 's006', 'RECID']
PUF = calc.dataframe(recvars)

PUF['compincome'] = (PUF['e00200'] + PUF['e02100'] + PUF['e00900'] +
                     PUF['e02000'] + PUF['e00400'] + PUF['e00300'] +
                     PUF['e00600'] + PUF['e02300'] + PUF['e01500'] +
                     PUF['e02400'])

def Match(puf, scf):
    """
    This function takes in a PUF dataset and a SCF dataset and matches the
    results. It returns a dataset of pairings of PUF and SCF records and the
    weight accorded to each.
    """
    incb = np.array(scf['compincome'])
    puf_list = list()
    scf_list = list()
    wt_list = list()
    # Iterate over PUF observations
    for i in range(len(puf)):
        scf1 = copy.deepcopy(scf)
        # Grab income for PUF unit
        inca = puf.loc[i, 'compincome']
        # Calculate distance
        scf1['dist'] = np.abs(incb - inca)
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

# Call the Match function and save the matchings
match_res = Match(PUF, SCF).round(2)
match_res.to_csv(os.path.join(CUR_PATH, 'match_2A_results.csv'), index=False)

print('Matching complete')
print('Length of PUF: ' + str(len(PUF)))
print('Length of SCF: ' + str(len(SCF)))
print('Length of Match: ' + str(len(match_res)))
