Importing Data
********************************

Importing data is highly reliant on the import format, there are currently two supported formats:

- Vector format for OD which contains
    - Top row with [ '' t1  t2  t3 .. ]
    - Rows for each trial, [ 'identifier'   data1   data2   data3 ]

- Titer format which is a list of data exported from Chromeleon HPLC software:
    - 2 blank rows
    - Row indicating titers: [ ''   Glucose Lactate Acetate Ethanol .. ]
    - Blank row
    - Row for each data point [ 'identifier'    GlucoseTiter    LactateTiter    AcetateTiter .. ]

Then data can be imported