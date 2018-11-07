#!/usr/bin/env python3
"""
Module to convert GNSS logger data to RINEX 3 data
"""
import datetime

# ------------------------------------------------------------------------------

def split_array(arr, n):
    """
    Split an input array into multiple sub-arrays of maximum length n

    :return: Array of arrays with maximum length n

    >>> split_array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], 13)
    [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], [14]]
    """

    return [arr[i:i+n] for i in range(0, len(arr), n)]

# -----------------------------------------------------------------------------

def __write_rnx3_header__(ver=3.03, typ="O"):
    """
    Write the first header line of the Rinex file
    """

    TAIL = "RINEX VERSION / TYPE"

    PAD = ' '

    res = "{0:9.2f}{1:11s}{2:1s}{1:19s}{3:1s}{1:19s}{4}\n".format(ver, PAD, typ, 'M', TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_runby__(pgm="Rokubun", agency="not-available"):
    """
    Write the runby header line of the Rinex file
    """

    TAIL = "PGM / RUN BY / DATE"

    datestr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    res = "{0:20s}{1:20s}{2:20s}{3}\n".format(pgm, agency, datestr, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_markername__(markername="UNKN"):
    """
    Write the runby header line of the Rinex file
    """

    TAIL = "MARKER NAME"

    res = "{0:60s}{1}\n".format(markername, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_markertype__(markertype="SMARTPHONE"):
    """
    """

    TAIL = "MARKER TYPE"

    res = "{0:60s}{1}\n".format(markertype, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_obsagency__(observer="unknown", agency="unknown"):
    """
    """

    TAIL = "OBSERVER / AGENCY"

    res = "{0:20s}{1:40s}{2}\n".format(observer, agency, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_rectype__(rec="unknown", typ="unknown", version="unkown"):
    """
    """

    TAIL = "REC # / TYPE / VERS"

    res = "{0:20s}{1:20s}{2:20s}{3}\n".format(rec, typ, version, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_anttype__(antenna="unknown", typ="unknown"):
    """
    """

    TAIL = "ANT # / TYPE"

    res = "{0:20s}{1:40s}{2}\n".format(antenna, typ, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_obslist__(obslist):
    """
    """

    TAIL = "SYS / # / OBS TYPES"

    res = ""

    for satsys in obslist:

        olist = obslist[satsys]

        lines = split_array(olist, 13)

        for i in range(len(lines)):

            l = satsys + "  {0:3d}".format(len(olist)) if i == 0 else "      "

            for obs in lines[i]:
                l += " {0:3s}".format(obs)

            res += "{0:60s}{1}\n".format(l, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_antpos__(pos=[0.0, 0.0, 0.0]):
    """
    """

    PAD = ' '
    TAIL = "APPROX POSITION XYZ"

    res = "{0:14.4f}{1:14.4f}{2:14.4f}".format(*pos) + \
          "{0:18s}{1}\n".format(PAD, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_anthen__(hen=[0.0, 0.0, 0.0]):
    """
    """

    PAD = ' '
    TAIL = "ANTENNA: DELTA H/E/N"

    res = "{0:14.4f}{1:14.4f}{2:14.4f}".format(*hen) + \
          "{0:18s}{1}\n".format(PAD, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_firstobs__(epoch):
    """
    """

    TAIL = "TIME OF FIRST OBS"

    res = epoch.strftime("  %Y    %m    %d    %H    %M    %S.") + \
                    '{0:06d}0'.format(int(epoch.microsecond))

    res = "{0:60s}{1}\n".format(res, TAIL)
    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_lastobs__(epoch):
    """
    """

    if epoch is None:
        return ""

    TAIL = "TIME OF LAST OBS"

    res = epoch.strftime("  %Y    %m    %d    %H    %M    %S.") + \
                    '{0:06d}0'.format(int(epoch.microsecond))

    res = "{0:60s}{1}\n".format(res, TAIL)

    return res

# -----------------------------------------------------------------------------

def __write_rnx3_header_end__():
    """
    """

    PAD = ' '
    TAIL = "END OF HEADER"

    res = "{0:60s}{1}\n".format(PAD, TAIL)
    return res

# ------------------------------------------------------------------------------

def write_header(obslist, firstepoch, ver=3.03, typ="O", pgm="Rokubun", markername="UNKN",
                 markertype="SMARTPHONE", observer="unknown", agency="unknown",
                 rec="unknown", rec_type="unknown", rec_version="unkown",
                 antenna="unknown", ant_type="unknown",
                 pos=[0.0, 0.0, 0.0], hen=[0.0, 0.0, 0.0], lastepoch=None):
    """
    """

    res  = __write_rnx3_header__(ver, typ)
    res += __write_rnx3_header_runby__(pgm, agency)
    res += __write_rnx3_header_markername__(markername)
    res += __write_rnx3_header_markertype__(markertype)
    res += __write_rnx3_header_obsagency__(observer, agency)
    res += __write_rnx3_header_rectype__(rec, rec_type, rec_version)
    res += __write_rnx3_header_anttype__(antenna, ant_type)
    res += __write_rnx3_header_antpos__(pos)
    res += __write_rnx3_header_anthen__(hen)
    res += __write_rnx3_header_obslist__(obslist)
    res += __write_rnx3_header_firstobs__(firstepoch)
    res += __write_rnx3_header_lastobs__(lastepoch)
    res += __write_rnx3_header_end__()

    return res

# ------------------------------------------------------------------------------

def write_obs(mdict, obslist, flag=0):
    """
    """
    # Print epoch
    epoch = mdict['epoch']
    res = epoch.strftime("> %Y %m %d %H %M %S.") + '{0:06d}0'.format(int(epoch.microsecond))

    # Epoch flag
    res += " {0:2d}".format(flag)

    # Num sats
    res += " {0:2d}".format(len(mdict)-1)

    res += '\n'

    # For each satellite, print obs
    for sat in mdict:
        if sat == 'epoch':
            continue

        res += sat

        obstypes = obslist[sat[0]]

        for o in obstypes:

            try:
                meas = mdict[sat][o]
            except KeyError:
                meas = 0.0

            if meas > 40e6:
                meas = 0.0

            res += '{0:14.3f}00'.format(meas)

        res += '\n'

    return res

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import doctest
    doctest.testmod(raise_on_error=True)
