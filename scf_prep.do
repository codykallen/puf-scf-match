clear all
/*
This first section reads in the raw, underlying survey response results and
prepares useful measures that we want to include in the main results.
*/
set maxvar 6000
use "p16i6.dta", clear
// Measure of comparable income
gen compincome = X5702 + X5704 + X5714 + X5706 + X5708 + X5710 + 5716 + X5722
// Active and passive income measures
gen activeincome = X5702 + X5704 + X5714
gen passiveincome = X5706 + X5708 + X5710 + X5716 + X5722
// Save the results to add to main dataset
keep Y1 compincome activeincome passiveincome
save "compincome.dta", replace

/*
This section reads in the official prepared results, merges in our calculated
results from the raw responses, and saves the data as a CSV.
*/
use "rscfp2016.dta", clear
merge 1:1 Y1 using "compincome.dta"
drop _merge

keep Y1 compincome activeincome passiveincome age wgt
export delimited using "scf.csv", replace
clear
exit
