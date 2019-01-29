# puf-scf-match
This is a temporary repo for holding code to match the PUF and SCF. 
Once an appropriate matching mechanism is determined, this code should be transplanted to `taxdata`.

This assumes the existence of an already-prepared dataset labeled `puf.csv`. 
For this to work, the matching must be done using the 2016 SCF and the PUF
aged to 2015. To obtain the relevant SCF data files, download and extract them from
 - https://www.federalreserve.gov/econres/files/scfp2016s.zip
 - https://www.federalreserve.gov/econres/files/scf2016s.zip

The aging of the PUF aligns the results with timing of the income
information in the SCF. The preparation of the SCF data is done in the State do file
`scf_prep.do`. In the transplant, we should consider how to conduct any aging to match variables.

On an additional note, the SCF has some unusual statistical issues involved
that may complicate the statistical analysis. In particular, the SCF uses
multiple imputation, such that each unit in the SCF has 5 observations. This
matching version ignores this complication.

To run this, first execute the code in `scf_prep.do`, and then run your preferred matching program.
