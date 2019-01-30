"""
This file conducts a matching between the PUF and the SCF using minimum
distance. In the event of ties (which should be very common due to the multiple
imputation in the SCF), we split the PUF record into several different records,
with the weight split based on the relative weights among the SCF matches.

In our case, we use age and two comparable income measures:
    Active income: wage/salary income, farm net income, sole proprietorship
                   net income, Sch E net income
    Passive income: taxable and nontaxable interest income, dividends,
                    Unemployment Insurance, Social Security, pensions and 
                    annuities
In this version, distance is defined as
    sqrt((age_scf - age_puf)^2 / Var(age_scf) +
         (actinc_scf - actinc_puf)^2 / Var(actinc_scf) +
         (passinc_scf - passinc_puf)^2 / Var(passinc_scf))
The variance is taken over the SCF measure because the distance is calculated
relative to each observation in the PUF.

The output of this program is a file containing pairings of units from the PUF
and from the SCF.
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
calc = Calculator(policy=pol, records=recs)
calc.advance_to_year(2015)
calc.calc_all()
recvars = ['e00200', 'e02100', 'e00900', 'e02000', 'e00400', 'e00300',
           'e00600', 'e02300', 'e01500', 'e02400', 'age_head', 's006', 'RECID']
PUF = calc.dataframe(recvars)

PUF['activeincome'] = (PUF['e00200'] + PUF['e00900'] + PUF['e02100'] +
                       PUF['e02000'])
PUF['passiveincome'] = (PUF['e00400'] + PUF['e00300'] + PUF['e00600'] +
                        PUF['e02300'] + PUF['e01500'] + PUF['e02400'])

def Variance(scf, varname):
    """
    Calculates the weighted variance for the SCF sub-dataset passed to it.
    """
    assert varname in ['age', 'activeincome', 'passiveincome']
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
    Aincb = np.array(scf['activeincome'])
    Pincb = np.array(scf['passiveincome'])
    ageb = np.array(scf['age'])
    puf_list = list()
    scf_list = list()
    wt_list = list()
    # Iterate over PUF observations
    for i in range(len(puf)):
        scf1 = copy.deepcopy(scf)
        # Grab weight and income for PUF unit
        awt = puf.loc[i, 's006']
        Ainca = puf.loc[i, 'activeincome']
        Pinca = puf.loc[i, 'passiveincome']
        agea = puf.loc[i, 'age_head']
        # Calculate distance
        v_age = Variance(scf, 'age')
        v_ainc = Variance(scf, 'activeincome')
        v_pinc = Variance(scf, 'passiveincome')
        scf1['dist'] = np.sqrt((ageb - agea)**2 / v_age +
                               ((Aincb - Ainca)**2 / v_ainc) +
                               ((Pincb - Pinca)**2 / v_pinc))
        # Grab matched observations
        scf_matched = scf1[scf1['dist'] == min(scf1['dist'])].reset_index()
        mwgts = np.array(scf_matched['wgt'])
        # Iterate over matched observations
        for j in range(len(scf_matched)):
            # Save each matching
            puf_list.append(puf.loc[i, 'RECID'])
            scf_list.append(scf_matched.loc[j, 'Y1'])
            wt_list.append(awt * mwgts[j] / sum(mwgts))
    # Save results to a DataFrame
    match1 = pd.DataFrame({'pufseq': puf_list, 'scf_seq': scf_list,
                           'wgt': wt_list})
    return match1

# Call the Match function for each age group and save the matchings
match_res = Match(PUF, SCF)
match_res.to_csv(os.path.join(CUR_PATH, 'match_1D_results.csv'), index=False)

