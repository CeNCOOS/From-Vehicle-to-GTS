# From-Vehicle-to-GTS
How to go from a vehicle to posting data on the GTS

This repository is designed to help guide a beginner from a vehicles data stream to pushing data to a file that can be picked up by the GTS (Global Telecommunications System).
This example was set up around Met-Ocean observations from autonomous surface vessels Report Sequence 3 15 011 from the FM 94 BUFR 
The ECMF table of codes is the base for all the codes and a very large and confusing document.

1) The first step is to register with ocean-ops.org.
2) You will need a WMO ID for your vehicle.  You need some defining permanent feature of the vehicle that can be associated with the WMO ID.  Generally this is the serial number of the vehicle.
3) There are currently set types of vehicles and if you have a different type you will need to contact Ocean-Ops to have them define your vehicle type.  Uncrewed Surface Vehicles (USV) are on their list to add, but currently they are listed by manufacturer.
4) Request a WMO ID and enter the appropriate data requested by the form.  Note during the summer this may take some time as most of the staff may be on vacation.
5) Obtain your datastream from your vehicle.  This may, as in the example used here, require decoding the data.
6) Write the data to a csv file with a header
Python will be used in this example. To generate the BUFR file this example requires the following:
    eccodes
    click
    csv2bufr (the above are required by this code)

7) Create bufr template JSON file  A table of some of the codes located https://confluence.ecmwf.int/display/ECC/WMO%3D37+element+table
    Note: template could not have the following in it for this example:
   <ul>
    <li> 1) {eccodes_key": "#1#observingPlatformManufacturerModel", "value":"const:1001824"} as this is not in the current version of eccodes</li>
    <li>2) {eccodes_key": "#1#observingPlatformManufacturerSerialNumber","value":"const:EMP301"} this won't work both because above isn't there but also because the serial number is assumed to be a integer</li>
    <li>3) {eccodes_key": "#1#stationType","value":"const:9"} this has to be "surfaceStationType" as "stationType" is not defined for this report sequence</li>
    <li>4) {eccodes_key": "#1#uniqueIdentifierForProfile","value":"data:uuid"} would not code for some reason, but since id is defined in the metadata as a uuid we will go with that.</li>
   </ul>
9) Run csv2bufr, example command looks like:
      csv2bufr data transform input.csv --bufr-template bufr_template.json --output-dir output_directory
      Where those are double dashes before the command options
10) Validate the bufr file if this is the first time creating,
    a) German option: https://kunden.dwd.de/bufrviewer/  This one seemed to give the most complete output
    b) ECMWF option: https://codes.ecmwf.int/bufr/validator  This one didn't seem to output everything encoded
    c) AWS option: http://aws-bufr-webapp.s3-website-ap-southeast-2.amazonaws.com/ This didn't seem to work for me.
11) Take the .bufr4 file and place it in a web accessible folder where your regional node can pick it up and post it to the GTS (How this will works is in progress)

Note: This is all a work in progress. We have not yet submitted data to the GTS yet.
