"""
This file conducts a matching between the PUF and the SCF similar to that
done is taxdata. In other words, we compute a particular measure and align the
items.
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
This version conducts the income matching nested within age groups. This adds
an additional level of accuracy relative to match0A.py.

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
# Group by age
age1 = np.array(SCF['age'])
group_age1 = np.zeros(len(age1))
group_age1 = np.where(age1 >= 35, 1, group_age1)
group_age1 = np.where(age1 >= 45, 2, group_age1)
group_age1 = np.where(age1 >= 55, 3, group_age1)
group_age1 = np.where(age1 >= 65, 4, group_age1)
group_age1 = np.where(age1 >= 75, 5, group_age1)
SCF['age_group'] = group_age1

# Get the PUF data aged to 2015
recs = Records('puf.csv')
pol = Policy()
calc = Calculator(policy=pol, records=recs, verbose=False)
calc.advance_to_year(2015)
calc.calc_all()
recvars = ['e00200', 'e02100', 'e00900', 'e02000', 'e00400', 'e00300',
           'e00600', 'e02300', 'e01500', 'e02400', 'age_head', 's006', 'RECID']
PUF = calc.dataframe(recvars)

# Calculate income measure for PUF
PUF['compincome'] = (PUF['e00200'] + PUF['e02100'] + PUF['e00900'] +
                     PUF['e02000'] + PUF['e00400'] + PUF['e00300'] +
                     PUF['e00600'] + PUF['e02300'] + PUF['e01500'] +
                     PUF['e02400'])
# Group by age
age2 = np.array(PUF['age_head'])
group_age2 = np.zeros(len(age2))
group_age2 = np.where(age2 >= 35, 1, group_age2)
group_age2 = np.where(age2 >= 45, 2, group_age2)
group_age2 = np.where(age2 >= 55, 3, group_age2)
group_age2 = np.where(age2 >= 65, 4, group_age2)
group_age2 = np.where(age2 >= 75, 5, group_age2)
PUF['age_group'] = group_age2




def Match(puf, scf):
    """
    This function takes in a PUF dataset and a SCF dataset and matches the
    results. It returns a dataset of pairings of PUF and SCF records and the
    weight accorded to each.
    """
    puf = copy.deepcopy(puf)
    scf = copy.deepcopy(scf)
    # Ensure datasets have same total weight
    wt_factor = sum(puf['s006']) / sum(scf['wgt'])
    scf['wgt2'] = scf['wgt'] * wt_factor
    # Sort by income
    puf = puf.sort_values('compincome', kind='mergesort').reset_index()
    scf = scf.sort_values('compincome', kind='mergesort').reset_index()
    # Preparation for matching
    puf_list = list()
    scf_list = list()
    wt_list = list()
    j = 0
    count = len(scf) - 1
    bwt = scf.loc[0, 'wgt2']
    epsilon = 0.001
    # Iterate over PUF observations
    for i in range(len(puf)):
        # Grab weight for PUF unit
        awt = puf.loc[i, 's006']
        # Run until PUF record weight used up
        while awt > epsilon:
            # Append the matched records
            pufseq = puf.loc[i, 'RECID']
            scfseq = scf.loc[j, 'Y1']
            puf_list.append(pufseq)
            scf_list.append(scfseq)
            # Use lesser weight for matched record
            cwt = min(awt, bwt)
            wt_list.append(cwt)
            # Update remaining weights for records
            awt = max(0, awt - cwt)
            bwt = max(0, bwt - cwt)
            # If SCF weight used up
            if bwt <= epsilon:
                # If SCf records not all used up
                if j < count:
                    j += 1
                    bwt = scf.loc[j, 'wgt2']
    # Save results to a DataFrame
    match1 = pd.DataFrame({'pufseq': puf_list, 'scf_seq': scf_list,
                           'wgt': wt_list})
    return match1

# Call the Match function for each age group and save the matchings
match_res0 = Match(PUF[PUF['age_group'] == 0], SCF[SCF['age_group'] == 0])
match_res1 = Match(PUF[PUF['age_group'] == 1], SCF[SCF['age_group'] == 1])
match_res2 = Match(PUF[PUF['age_group'] == 2], SCF[SCF['age_group'] == 2])
match_res3 = Match(PUF[PUF['age_group'] == 3], SCF[SCF['age_group'] == 3])
match_res4 = Match(PUF[PUF['age_group'] == 4], SCF[SCF['age_group'] == 4])
match_res5 = Match(PUF[PUF['age_group'] == 5], SCF[SCF['age_group'] == 5])
match_res = pd.concat([match_res0, match_res1, match_res2, match_res3,
                       match_res4, match_res5], axis=0)
match_res.to_csv(os.path.join(CUR_PATH, 'match_0B_results.csv'), index=False)

print('Matching complete')
print('Length of PUF: ' + str(len(PUF)))
print('Length of SCF: ' + str(len(SCF)))
print('Length of Match: ' + str(len(match_res)))