This documentation describes the record format for the divisional files on 
/pub/data/cirs/climdiv that have the filenames:

climdiv-cddcdv-vx.y.z-YYYYMMDD
climdiv-hddcdv-vx.y.z-YYYYMMDD
climdiv-pcpndv-vx.y.z-YYYYMMDD
climdiv-pdsidv-vx.y.z-YYYYMMDD
climdiv-phdidv-vx.y.z-YYYYMMDD
climdiv-pmdidv-vx.y.z-YYYYMMDD
climdiv-sp01dv-vx.y.z-YYYYMMDD
climdiv-sp02dv-vx.y.z-YYYYMMDD
climdiv-sp03dv-vx.y.z-YYYYMMDD
climdiv-sp06dv-vx.y.z-YYYYMMDD
climdiv-sp09dv-vx.y.z-YYYYMMDD
climdiv-sp12dv-vx.y.z-YYYYMMDD
climdiv-sp24dv-vx.y.z-YYYYMMDD
climdiv-tmaxdv-vx.y.z-YYYYMMDD
climdiv-tmindv-vx.y.z-YYYYMMDD
climdiv-tmpcdv-vx.y.z-YYYYMMDD
climdiv-zndxdv-vx.y.z-YYYYMMDD

For a map of all CONUS divisions, please see the following link:
http://www.ncdc.noaa.gov/monitoring-references/maps/images/us-climate-divisions-names.jpg

For maps of divisions in Alaska, see the following links:
http://www1.ncdc.noaa.gov/pub/data/cmb/images/us/2015/feb/alaska-clim-divs.png
http://www1.ncdc.noaa.gov/pub/data/cmb/images/us/2015/feb/alaska-clim-divs-with-cities.png


                                    nClimDiv
                                   DIVISIONAL
                        TEMPERATURE-PRECIPITATION-DROUGHT

                                   JUNE 2014

The major parameters in this file are sequential climatic division monthly 
maximum, minimum and average temperature (deg. F. to 10ths, national 
temperature to 100ths), precipitation (inches to 100ths), Standardized 
Precipitation Index (SPI), and Palmer Drought Indices (PDSI, PHDI, PMDI, 
and ZNDX). Period of record is 1895 through latest month available, updated 
monthly.

Values from the most recent two calendar years will be updated on a monthly 
basis.  Period of record updates will occur when the underlying data set 
undergoes a version change.

METHODOLOGY:

Divisional values in nClimDiv were derived from area-weighted averages of 
grid-point estimates interpolated from station data.  A nominal grid resolution
of 5 km was used to ensure that all divisions had sufficient spatial sampling 
(only four small divisions had less than 100 points) and because the impact of 
elevation on precipitation is minimal below 5 km.  Station data were gridded 
via climatologically aided interpolation to minimize biases from topographic 
and network variability.

The Global Historical Climatology Network (GHCN)  Daily dataset is the source 
of station data for nClimDiv.  GHCN-Daily contains several major observing 
networks in North America, five of which are used here.  The primary network 
is the National Weather Service (NWS) Cooperative Observing (COOP) program, 
which consists of stations operated by volunteers as well as by agencies such 
as the Federal Aviation Administration.  To improve coverage in western states 
and along international borders, nClimDiv also includes the National 
Interagency Fire Center (NIFC) Remote Automatic Weather Station (RAWS) network, 
the USDA Snow Telemetry (SNOTEL) network, the Environment Canada (EC) 
network (south of 52�N), and part of Mexicos Servicio Meteorologico Nacional 
(SMN) network (north of 24�N).  Note that nClimDiv does not incorporate 
precipitation data from RAWS because that networks tipping-bucket gauges are 
unheated, leading to suspect cold-weather data.

All GHCN-Daily stations are routinely processed through a suite of logical, 
serial, and spatial quality assurance reviews to identify erroneous 
observations.  For nClimDiv, all such data were set to missing before 
computing monthly values, which in turn were subjected to additional serial 
and spatial checks to eliminate residual outliers. Stations having at least 
10 years of valid monthly data since 1950 were used in nClimDiv.

For temperature, bias adjustments were computed to account for historical 
changes in observation time, station location, temperature instrumentation, 
and siting conditions.  Changes in observation time are only problematic for 
the COOP network whereas changes in station location and instrumentation occur 
in almost all surface networks.   As in the U.S. Historical Climatology Network
version 2.5, the method of Karl et al. (1986) was applied to remove the 
observation time bias from the COOP network, and the pairwise method of Menne 
and Williams (2009) was used to address changes in station location and 
instrumentation in all networks.  Because the pairwise method also largely 
accounts for local, unrepresentative trends that arise from changes in siting 
conditions, nClimDiv contains no separate adjustment in that regard.

For additional information on how nClimDiv is constructed, please see:
http://journals.ametsoc.org/doi/abs/10.1175/JAMC-D-13-0248.1

Monthly heating and cooling degree day values are available for the period
1895 to present.  The divisional degree day values are derived from  the
adjusted temperatures using a statistical algorithm.  The heating and cooling
degree day values available at this site are used for operational monitoring
purposes and may be different from the heating and cooling degree day values
published in official degree day publications.  Population weights utilize 
the 1981-2010 Census data.

Historical drought data have been added to this file for the period 1895 to
present.  The file is updated monthly.  All drought data are calibrated using 
the period 1931-1990 (cf. Karl, 1986; Journal of Climate and Applied 
Meteorology, Vol. 25, No. 1, January 1986).  Drought data include: 

1.  Palmer Drought Severity Index (PDSI)

 This is the monthly value (index) that is generated indicating the severity
 of a wet or dry spell.  This index is based on the principles of a balance
 between moisture supply and demand.  Man-made changes were not considered in
 this calculation.  The index generally ranges from -6 to +6, with negative
 values denoting dry spells and positive values indicating wet spells.  There
 are a few values in the magnitude of +7 or -7.  PDSI values 0 to -.5 =
 normal; -0.5 to -1.0 = incipient drought; -1.0 to -2.0 = mild drought; -2.0
 to -3.0 = moderate drought; -3.0 to -4.0 = severe drought; and greater than -
 4.0 = extreme drought.  Similar adjectives are attached to positive values of
 wet spells.  This is a meteorological drought index used to assess the
 severity of dry or wet spells of weather.

2.  Palmer Hydrological Drought Index (PHDI)

 This is the monthly value (index) generated monthly that indicates the
 severity of a wet or dry spell.  This index is based on the principles of a
 balance between moisture supply and demand.  Man-made changes such as
 increased irrigation, new reservoirs, and added industrial water use were not
 included in the computation of this index.  The index generally ranges from -
 6 to +6, with negative values denoting dry spells, and positive values
 indicating wet spells.  There are a few values in the magnitude of +7 or -7. 
 PHDI values 0 to -0.5 = normal; -0.5 to -1.0 = incipient drought; -1.0 to -
 2.0 = mild drought; -2.0 to -3.0 = moderate drought; -3.0 to -4.0 = severe
 drought; and greater than -4.0 = extreme drought.  Similar adjectives are
 attached to positive values of wet spells.  This is a hydrological drought
 index used to assess long-term moisture supply.

3.  Palmer "Z" Index (ZNDX)

 This is the generated monthly Z values, and they can be expressed as the
 "Moisture Anomaly Index."  Each monthly Z value is a measure of the departure
 from normal of the moisture climate for that month.  This index can respond
 to a month of above-normal precipitation, even during periods of drought. 
 Table 1 contains expected values of the Z index and other drought parameters. 
 See Historical Climatology Series 3-6 through 3-9 for a detailed description
 of the drought indices.

4.  Modified Palmer Drought Severity Index (PMDI)

 This is a modification of the Palmer Drought Severity Index.  The
 modification was made by the National Weather Service Climate Analysis Center
 for operational meteorological purposes.  The Palmer drought program
 calculates three intermediate parallel index values each month.  Only one
 value is selected as the PDSI drought index for the month.  This selection is
 made internally by the program on the basis of probabilities.  If the
 probability that a drought is over is 100%, then one index is used.  If the
 probability that a wet spell is over is 100%, then another index is used.  If
 the probability is between 0% and 100%, the third index is assigned to the
 PDSI.  The modification (PMDI) incorporates a weighted average of the wet and
 dry index terms, using the probability as the weighting factor.  (Thomas R.
 Heddinghause and Paul Sabol, 1991; "A Review of the Palmer Drought Severity
 Index and Where Do We Go From Here?," Proceedings of the Seventh Conference
 on Applied Climatology, pp. 242-246, American Meteorological Society, Boston,
 MA).  The PMDI and PDSI will have the same value during an established
 drought or wet spell (i.e., when the probability is 100%), but they will have
 different values during transition periods.

5.  Standardized Precipitation Index (SPxx)

This is a transformation of the probability of observing a given amount of 
precipitation in xx months.  A zero index value reflects the median of the 
distribution of precipitation, a -3 indicates a very extreme dry spell, and a 
+3 indicates a very extreme wet spell.  The more the index value departs from 
zero, the drier or wetter an event lasting xx months is when compared to the 
long-term climatology of the location.  The index allows for comparison of 
precipitation observations at different locations with markedly different 
climates; an index value at one location expresses the same relative departure 
from median conditions at one location as at another location.  It is 
calculated for different time scales since it is possible to experience dry 
conditions over one time scale while simultaneously experiencing wet conditions 
over a different time scale. 


               Table 1    Classes for Wet and Dry Periods


Approximate 
Cumulative                                                           
Frequency               Range                                     Range
    %                   PHDI                  Category              Z         

  > 96                > 4.00                Extreme wetness      > 3.50

    90-95               3.00,  3.99         Severe wetness         2.50,  3.49

    73-89               1.50,  2.99         Mild to moderate       1.00,  2.49
                                                    wetness

    28-72              -1.49,  1.49         Near normal           -1.24,  0.99

    11-27              -1.50, -2.99         Mild to moderate      -1.25, -1.99
                                                    drought

     5-10              -3.00, -3.99         Severe drought        -2.00, -2.74

  <  4                <-4.00                Extreme drought      <-2.75


STATE CODE TABLE: 
                             Range of values of 01-91.

                             01 Alabama                 28 New Jersey
                             02 Arizona                 29 New Mexico
                             03 Arkansas                30 New York
                             04 California              31 North Carolina
                             05 Colorado                32 North Dakota
                             06 Connecticut             33 Ohio
                             07 Delaware                34 Oklahoma
                             08 Florida                 35 Oregon
                             09 Georgia                 36 Pennsylvania
                             10 Idaho                   37 Rhode Island
                             11 Illinois                38 South Carolina
                             12 Indiana                 39 South Dakota
                             13 Iowa                    40 Tennessee
                             14 Kansas                  41 Texas
                             15 Kentucky                42 Utah
                             16 Louisiana               43 Vermont
                             17 Maine                   44 Virginia
                             18 Maryland                45 Washington
                             19 Massachusetts           46 West Virginia
                             20 Michigan                47 Wisconsin
                             21 Minnesota               48 Wyoming
                             22 Mississippi             50 Alaska
                             23 Missouri   
                             24 Montana   
                             25 Nebraska 
                             26 Nevada  
                             27 New Hampshire


FILE FORMAT:


Element          Record
Name             Position    Element Description

STATE-CODE          1-2      STATE-CODE as indicated in State Code Table as
                             described in FILE 1.  Range of values is 01-91.

DIVISION-NUMBER     3-4      DIVISION NUMBER - Assigned by NCDC.  Range of
                             values 01-10.

ELEMENT CODE        5-6      01 = Precipitation
                             02 = Average Temperature
                             05 = PDSI
                             06 = PHDI
                             07 = ZNDX
                             08 = PMDI
                             25 = Heating Degree Days
                             26 = Cooling Degree Days
                             27 = Maximum Temperature
                             28 = Minimum Temperature
			     71 = 1-month Standardized Precipitation Index
			     72 = 2-month Standardized Precipitation Index
                             73 = 3-month Standardized Precipitation Index
                             74 = 6-month Standardized Precipitation Index
                             75 = 9-month Standardized Precipitation Index
                             76 = 12-month Standardized Precipitation Index
                             77 = 24-month Standardized Precipitation Index

YEAR                7-10     This is the year of record.  Range is 1895 to
                             current year processed.

(all data values are right justified):

JAN-VALUE          11-17     Palmer Drought Index format (f7.2)
                             Range of values -20.00 to 20.00. Decimal point
                             retains a position in 7-character field.
                             Missing values in the latest year are indicated
                             by -99.99.

                             Monthly Divisional Temperature format (f7.2)
                             Range of values -50.00 to 140.00 degrees Fahrenheit.
                             Decimals retain a position in the 7-character
                             field.  Missing values in the latest year are
                             indicated by -99.90.

                             Monthly Divisional Precipitation format (f7.2)
                             Range of values 00.00 to 99.99.  Decimal point
                             retains a position in the 7-character field.
                             Missing values in the latest year are indicated
                             by -9.99.

                             Monthly Divisional Degree Day format (f7.0)
                             Range of values 0000. to 9999.  Decimal point
                             retains a position in the 7-character field.
                             Missing values in the latest year are indicated
                             by -9999..

                             Standardized Precipitation Index format (f7.2).
                             Range of values -4.00 to 4.00.  Decimal
                             point retains a position in 7-character field.
                             Missing values in the latest year are indicated
                             by -99.99.

FEB-VALUE          18-24     

MAR-VALUE          25-31    

APR-VALUE          32-38   

MAY-VALUE          39-45  

JUNE-VALUE         46-52     

JULY-VALUE         53-59     

AUG-VALUE          60-66     

SEPT-VALUE         67-73     

OCT-VALUE          74-80     

NOV-VALUE          81-87     

DEC-VALUE          88-94     
