from llmod import extract_all
import re
import pandas as pd
import os


dfmod = extract_all(r"C:\Users\InkyPhantom\Desktop\Projects\cv sorter files\P11 24824 Software Development Associate (1).pdf")

print(dfmod)