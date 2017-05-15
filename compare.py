#!/usr/bin/env python3

debug = True

'''
This script compares two lists of CPS employees scraped from the employee
search tool, and outputs these lists:
    - new employees
    - dearly departed employees
    - employees with changed information.
Employees are identified by their email rather than their name.
'''

import argparse

# parse args
parser = argparse.ArgumentParser(description='Script to describe changes in CPS employees')
parser.add_argument('before', help='first employee list', type=str)
parser.add_argument('after', help='second employee list', type=str)
args = parser.parse_args()

### the realness begins

import pandas as pd

names = ["lname", "fname", "job", "location", "phone", "email", "type"]
# read in before and after lists
before = pd.read_csv(args.before, names=names)
after = pd.read_csv(args.after, names=names)

# clean up emails
# lower case is best case
before['email'] = before['email'].str.lower()
after['email'] = after['email'].str.lower()
# NaN --> ''
after = after.fillna('')
before = before.fillna('')

# sort lists
before.sort_values('email', inplace=True)
after.sort_values('email', inplace=True)

# create output frames
cnames = names + ['prevLocation']
changedLocation = pd.DataFrame(columns=cnames)
newEmployees = pd.DataFrame(columns=names)
departedEmployees = pd.DataFrame(columns=names)

# march through lists
na = after.shape[0]
nb = before.shape[0]

aa = 0 # index for after employees
bb = 0 # index for before employees
while (aa < na and bb < nb): # loop over after employees
    aEmail = after.iloc[aa]['email']
    bEmail = before.iloc[bb]['email']
    aLocation = after.iloc[aa]['location']
    bLocation = before.iloc[bb]['location']

    #if (after.iloc[aa]['email'] == before.iloc[bb]['email']): # employee match
    if (aEmail == bEmail): # employee match
        if (aLocation != bLocation): # change of location
            if (debug):
                print("{} moved from {} to {}!".format(aEmail, bLocation, aLocation))
            # append to changed location list
            changedLocation = changedLocation.append(after.iloc[aa])
            pos = changedLocation.last_valid_index()
            changedLocation.set_value(pos, 'prevLocation', bLocation)
        aa += 1
        bb += 1
    else: # mismatch
        #if (debug):
            #print("{} @ {} is not {} @ {}".format(aEmail, aLocation, bEmail, bLocation))
        if (aEmail < bEmail): # new employee
            if (debug):
                print("{} is a brand new hire at {}!".format(aEmail, aLocation))
            newEmployees = newEmployees.append(after.iloc[aa])
            aa += 1
        else: # departed employee
            if (debug):
                print("{} has left {} and CPS!".format(bEmail, bLocation))
            departedEmployees = departedEmployees.append(before.iloc[bb])
            bb += 1

# cleanup: if there are extra before employees at the end of the list,
# they get appended to the departed list

# diff lists

# march through diff

    # if in both, check other records for difference
        # do just location first
    # else if in A but not B (strcmp: A < B), new employee
    # else if in B but not A (strcmp: B < A), departed employee

# spit out lists
before.to_csv('before_sort.csv', header=False, index=False)
after.to_csv('after_sort.csv', header=False, index=False)

changedLocation.to_csv('changedLocation.csv', index=False)
newEmployees.to_csv('newEmployees.csv', index=False)
departedEmployees.to_csv('departedEmployees.csv', index=False)
