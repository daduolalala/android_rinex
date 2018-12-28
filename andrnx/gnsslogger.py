#coding:utf-8


#!/usr/bin/env python3
"""
Module to process log files from Google's Android GNSS Logger app
"""
import datetime
import math
import re
import sys



# Flags to check wether the measurement is correct or not
# https://developer.android.com/reference/android/location/GnssMeasurement.html#getState()
STATE_CODE_LOCK = int(0x00000001)
STATE_BIT_SYNC = int(0x00000002)
STATE_TOW_DECODED = int(0x00000008)
STATE_GLO_TOD_DECODED = int(0x00000080)
STATE_GAL_E1BC_CODE_LOCK = int(0x00000400)

# AccumulatedDeltaRangeState
ADR_STATE_VALID = int(0x00000001)
ADR_STATE_CYCLE_SLIP = int(0x00000004)
ADR_STATE_RESET = int(0x00000002)
ADR_STATE_HALF_CYCLE_REPORTED = int(0x00000010)

# Define constants
SPEED_OF_LIGHT = 299792458.0 # [m/s]
GPS_WEEKSECS = 604800 # Number of seconds in a week
NS_TO_S = 1.0e-9
NS_TO_M = NS_TO_S * SPEED_OF_LIGHT  # Constant to transform from nanoseconds to meters

# Origin of the GPS time scale
GPSTIME = datetime.datetime(1980, 1, 6)

OBS_LIST = ['C', 'L', 'D', 'S']

EPOCH_STR = 'epoch'

HCCC = 0.0

# Constellation types
CONSTELLATION_GPS = 1
CONSTELLATION_SBAS = 2
CONSTELLATION_GLONASS = 3
CONSTELLATION_QZSS = 4
CONSTELLATION_BEIDOU = 5
CONSTELLATION_GALILEO = 6
CONSTELLATION_UNKNOWN = 0

CONSTELLATION_LETTER = {
        CONSTELLATION_GPS : 'G',
        CONSTELLATION_SBAS : 'S',
        CONSTELLATION_GLONASS : 'R',
        CONSTELLATION_QZSS : 'J',
        CONSTELLATION_BEIDOU : 'C',
        CONSTELLATION_GALILEO : 'E',
        CONSTELLATION_UNKNOWN : 'X'
}




class GnssLogHeader(object):
    """
    Class that manages the header from the log file.
    """



    def __init__(self, filename):
        """
        Initializes the header from a file handler to the file. Loads the
        parameters and field names present in the header part of the log
        """

        self.parameters = {}
        self.fields = {}

        with open(filename, 'r') as fh:

                for line in fh:

                        # Detect end of header
                        if not line.startswith('#'):
                                break

                        # Skip empty lines
                        if line.strip() == '#':
                                continue

                        fields = re.split('[: ,]', line.strip())

                        method_name = 'parse_{0}'.format(fields[1].lower())

                        # Call the method that processes the line
                        getattr(GnssLogHeader, method_name)(self, line)


    def get_fieldnames(self, line):
        """
        """

        fields = [f.strip() for f in line[2:].strip().split(',')] # Skip initial hash character

        key = fields[0]
        field_names = fields[1:]

        self.fields[key] = field_names

        return

    def parse_header(self, line):
        """
        Get parameters from header line, in this case do nothing
        """
        pass

    def parse_version(self, line):
        """
        Return a dictionary
        """

        fields = line.strip().split(' ')

        for field in fields[1:]:

            if field.endswith(':'):
                key = field[:-1]
                self.parameters[key] = ''

            else:

                self.parameters[key] += ' ' + field

        # Clean superfluous spaces
        self.parameters = { k:self.parameters[k].strip() for k in self.parameters }


    def parse_fix(self, line):

        self.get_fieldnames(line)

    def parse_raw(self, line):
        """
        """
        self.get_fieldnames(line)


    def parse_nav(self, line):
        """
        """
        self.get_fieldnames(line)

# ------------------------------------------------------------------------------

class GnssLog(object):
    """
    """

    CONVERTER = {
        'AccumulatedDeltaRangeState' : int,
        'ConstellationType' : int,
        'MultipathIndicator' : int,
        'State' : int,
        'Svid' : int
    }


    def __init__(self, filename):
        """
        """

        # Criteria by which the different data batches are delimited
        self.BATCH_DELIMITER = 'TimeNanos'

        self.filename = filename

        self.header = GnssLogHeader(self.filename)


    def __field_conversion__(self, fname, valuestr):
        """
        Convert the field, by default will be float, unless it exists in
        the CONVERTER structure. If an exeception occurs, the field will be
        left as is.
        """
        try:
            if fname in GnssLog.CONVERTER:
                return GnssLog.CONVERTER[fname](valuestr)
        except ValueError:
                return ''

        try:
                return float(valuestr)
        except ValueError:
                return valuestr



    def __parse_line__(self, line):
        """
        """

        line_fields = line.strip().split(',')

        field_names = self.header.fields[line_fields[0]]

        fields = { field_names[i] :  \
                   self.__field_conversion__(field_names[i], line_fields[i + 1]) \
                                        for i in range(len(line_fields) - 1)}

        return fields


    def raw_batches(self):
        """
        Generator function use to yield a batch
        """

        batch = []

        with open(self.filename, 'r') as fh:

            for line in fh:

                if not line.startswith('Raw'):
                        continue

                line_fields = self.__parse_line__(line)


                if len(line_fields) != 29:
                    continue

                if len(batch) > 0 and line_fields[self.BATCH_DELIMITER] != batch[0][self.BATCH_DELIMITER]:
                        yield batch
                        batch = []

                # if line_fields['ConstellationType'] != 1:
                #     continue

                batch.append(line_fields)

            # Yield last batch
            yield batch

    def fix_batches(self):
        """
        Generator function used to yield a position batch
        """

        with open(self.filename, 'r') as fh:

            for line in fh:

                if not line.startswith('Fix'):
                        continue

                yield self.__parse_line__(line)

# ------------------------------------------------------------------------------


def get_frequency(measurement):

    v = measurement['CarrierFrequencyHz']

    # 如果为空,则返回 GPS_L1 的频率
    # return 1575420000 if v == '' else v

    ctype = CONSTELLATION_GPS if measurement['ConstellationType'] == '' else measurement['ConstellationType']

    if v != '':
        return v

    if ctype == 1: # gps
        return 1575450000

    elif ctype == 2: # sbas
        return 1575420000

    elif ctype == 3:# glo
        return 1602000000

    elif ctype == 4: # qzss
        return 1575420000

    elif ctype == 5: # bds
        return 1561098000

    elif ctype == 6: # gal
        return 1575420000
    else:
        tTxSeconds = 0


# ------------------------------------------------------------------------------

def get_obscode(measurement):

    ctype = CONSTELLATION_GPS if measurement['ConstellationType'] == '' else measurement['ConstellationType']

    frequency = get_frequency(measurement)

    ifreq = 0 if frequency == '' else round(frequency / 10.23e6)

    if ctype == CONSTELLATION_GPS:  # gps 1C 2C 5X
        if ifreq == 154:
            return '1C'
        elif ifreq == 115:
            return '5X'
        else:
            raise ValueError("Cannot get Rinex frequency band: sys={0},freq={1}\n".format(ctype, frequency))

    elif ctype == CONSTELLATION_SBAS: # SBAS
        return '1C'

    elif ctype == CONSTELLATION_GLONASS: # GLONASS
        return '1C'

    elif ctype == CONSTELLATION_QZSS: # QZSS
        if ifreq == 154:
            return '1C'
        elif ifreq == 115:
            return '5X'
        else:
            raise ValueError("Cannot get Rinex frequency band: sys={0},freq={1}\n".format(ctype, frequency))

    elif ctype == CONSTELLATION_BEIDOU:  # bds 1I 7I 6I
        if ifreq == 153:
            return '1I'
        elif ifreq == 118:
            return '7I'
        elif ifreq == 123:
            return '6I'
        else:
            raise ValueError("Cannot get Rinex frequency band: sys={0},freq={1}\n".format(ctype, frequency))

    elif ctype == CONSTELLATION_GALILEO: # gal 1C 5I
        if ifreq == 154:
            return '1C'
        elif ifreq == 115:
            return '5X'
        else:
            raise ValueError("Cannot get Rinex frequency band: sys={0},freq={1}\n".format(ctype, frequency))

    else:
        raise ValueError("Cannot get Rinex frequency band: sys={0}\n".format(ctype))

# ------------------------------------------------------------------------------

def get_obslist(batches):
    """
    Obtain the observable list (array of RINEX 3.0 observable codes), particularized
    per each constellation, e.g.

    obs = {
        'G' : [C1C, L1C, D1C, S1C, C5X],
        'E' : [C1C, L1C, D1C, C5X],
        'R' : [C1P, C2P]
        'C' : [C1I, L1I, D1I, S1I],
    }
    """

    obslist = {}

    for batch in batches:

        for measurement in batch:

                obscode = get_obscode(measurement)

                constellation = CONSTELLATION_LETTER[measurement['ConstellationType']]

                if constellation not in obslist:
                        obslist[constellation] = []

                arr = obslist[constellation]

                if obscode not in arr:
                        obslist[constellation].append(obscode)


    # Sort observable list for all constellations
    for c in obslist:
        arr = sorted(obslist[c])
        obslist[c] = [ m + o for o in arr for m in OBS_LIST  ]

    return obslist

# ------------------------------------------------------------------------------

def check_lli(state):
    # todo:加入半周反转的判断

    # if (state & ADR_STATE_VALID) == 0:
    #     raise ValueError("State [ 0x{0:2x} {0:8b} ] not ADR_STATE_VALID [ 0x{1:2x} {1:8b} ] not valid".format(state,ADR_STATE_VALID))

    if (state & ADR_STATE_CYCLE_SLIP) != 0:
        raise ValueError("State [ 0x{0:2x} {0:8b} ] has ADR_STATE_CYCLE_SLIP [ 0x{1:2x} {1:8b} ] not valid".format(state, ADR_STATE_CYCLE_SLIP))

    if (state & ADR_STATE_RESET) != 0:
        raise ValueError("State [ 0x{0:2x} {0:8b} ] has ADR_STATE_RESET [ 0x{1:2x} {1:8b} ] not valid".format(state,ADR_STATE_RESET))


def check_state(ctype, obscode, state):
    """
    Checks if measurement is valid or not based on the Sync bits
    """

    if ctype == CONSTELLATION_GPS or ctype == CONSTELLATION_QZSS:
        if (state & STATE_CODE_LOCK) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_CODE_LOCK [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_CODE_LOCK))
        if (state & STATE_TOW_DECODED) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_TOW_DECODED [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_TOW_DECODED))

    elif ctype == CONSTELLATION_SBAS: # SBAS
        if (state & STATE_CODE_LOCK) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_CODE_LOCK [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_CODE_LOCK))

    elif ctype == CONSTELLATION_GLONASS: # GLONASS
        if (state & STATE_CODE_LOCK) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_CODE_LOCK [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_CODE_LOCK))
        if (state & STATE_GLO_TOD_DECODED) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_GLO_TOD_DECODED [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_TOW_DECODED))

    elif ctype == CONSTELLATION_BEIDOU:  # bds 1I 7I 6I
        if (state & STATE_CODE_LOCK) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_CODE_LOCK [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_CODE_LOCK))
        if (state & STATE_TOW_DECODED) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_TOW_DECODED [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_TOW_DECODED))

    elif ctype == CONSTELLATION_GALILEO:
        if (obscode == '1C', state & STATE_GAL_E1BC_CODE_LOCK) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_GAL_E1BC_CODE_LOCK [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_CODE_LOCK))
        if (state & STATE_TOW_DECODED) == 0:
            raise ValueError("State [ 0x{0:2x} {0:8b} ] not STATE_TOW_DECODED [ 0x{1:2x} {1:8b} ] not valid".format(state,STATE_TOW_DECODED))
    else:
        pass


# ------------------------------------------------------------------------------

def get_satname(measurement):
    """
    Obtain the satellite name from a GNSS Logger measurement

    >>> get_satname({'ConstellationType': 1, 'Svid': 5})
    'G05'
    >>> get_satname({'ConstellationType': 6, 'Svid': 11})
    'E11'
    >>> get_satname({'ConstellationType': 3, 'Svid': 24})
    'R24'
    >>> get_satname({'ConstellationType': 5, 'Svid': 1})
    'C1'
    """

    ctype = measurement['ConstellationType']
    c = CONSTELLATION_LETTER[ctype]
    svid = measurement['Svid']

    satname = '{0}{1:02d}'.format(c, svid)

    # Make sure that we report GLONASS OSN (PRN) instead of FCN
    # https://developer.android.com/reference/android/location/GnssStatus.html#getSvid(int)
    if svid > 50 and ctype == CONSTELLATION_GLONASS:
        raise ValueError("-- WARNING: Skipping measurement for GLONASS sat "
                         "without OSN [ {0} ]".format(satname))

    return satname

# ------------------------------------------------------------------------------

def process(measurement, fullbiasnanos=None, integerize=False, pseudorange_bias=0.0):
    """
    Process a log measurement. This method computes the pseudorange, carrier-phase (in cycles)
    Doppler (cycles/s) as well as CN/0

    :param measurement: GNSS Logger measurement line to process
    :param fullbiasnanos: Full Bias Nanos, used to either fix it to a certain
                          value (if value is provided) or update it with the
                          data if None (default value)
    :param integerize: Boolean to control whether to integerize the measurements
                       to the nearest "integerized" time stamp (in this case
                       to the nearest second)
    :param pseudorange_bias: Add an externally computed bias to the pseudorange.
                             Default is 0.0
    """


    try:
        satname = get_satname(measurement)
    except ValueError as e:
        sys.stderr.write("{0}\n".format(e))
        return None

    obscode = get_obscode(measurement)

    # 检测是否发生周跳
    lockflag = 0
    try:
        check_lli(measurement['AccumulatedDeltaRangeState'])
    except ValueError as e:
        sys.stderr.write("-- WARNING: {0} for satellite [ {1} ]\n".format(e, satname))
        lockflag = 1

    # Skip this measurement if no synched
    trackflag = 0
    try:
        check_state(measurement['ConstellationType'], obscode, measurement['State'])
    except ValueError as e:
        sys.stderr.write("-- WARNING: {0} for satellite [ {1} ]\n".format(e, satname))
        trackflag = 1

    global  HCCC
    new_hccc = measurement['HardwareClockDiscontinuityCount']
    if  new_hccc != HCCC:
        sys.stderr.write("-- WARNING: HardwareClockDiscontinuityCount: [{0}] => [{1}] for satellite [{2}]\n".format(HCCC, new_hccc,satname))
        HCCC = new_hccc

    # Set the fullbiasnanos if not set or if we need to update the full bias
    # nanos at each epoch
    fullbiasnanos = measurement['FullBiasNanos'] if fullbiasnanos is None else fullbiasnanos

    # Obtain time nanos and bias nanos. Skip if None

    try:
        timenanos = float(measurement['TimeNanos'])
    except ValueError:
        raise ValueError("-- WARNING: Invalid value of TimeNanos or satellite  [ {0} ]\n".format(satname))

    try:
        biasnanos = measurement['BiasNanos']
    except ValueError:
        biasnanos = 0.0

    # Compute the GPS week number as well as the time within the week of
    # the reception time (i.e. clock epoch)
    gpsweek = math.floor(-fullbiasnanos * NS_TO_S / GPS_WEEKSECS)
    local_est_GPS_time = timenanos - (fullbiasnanos + biasnanos)
    gpssow = local_est_GPS_time * NS_TO_S - gpsweek * GPS_WEEKSECS

    # Fractional part of the integer seconds
    frac = gpssow - int(gpssow+0.5) if integerize else 0.0

    # Convert the epoch to Python's buiit-in datetime class
    epoch = GPSTIME + datetime.timedelta(weeks=gpsweek, seconds=gpssow-frac)

    try:
        timeoffsetnanos = measurement['TimeOffsetNanos']
    except ValueError:
        timeoffsetnanos = 0.0

    # Compute the reception and transmission times
    tRxSeconds = gpssow + timeoffsetnanos * NS_TO_S

    ctype = measurement['ConstellationType']
    tTxSeconds = 0

    if ctype == 1:# gps
        tTxSeconds = float(measurement['ReceivedSvTimeNanos']) * NS_TO_S

    elif ctype == 2:
        tTxSeconds = float(measurement['ReceivedSvTimeNanos']) * NS_TO_S

    elif ctype == 3:# glo
        tTxSeconds = float(measurement['ReceivedSvTimeNanos']) * NS_TO_S
        txint = round(tRxSeconds/86400)*86400
        tTxSeconds = round(tRxSeconds/86400)*86400 - 10800 + tTxSeconds + 18

    elif ctype == 4: # qzss
        tTxSeconds = float(measurement['ReceivedSvTimeNanos']) * NS_TO_S

    elif ctype == 5: # bds
        tTxSeconds = measurement['ReceivedSvTimeNanos'] * NS_TO_S + 14

    elif ctype == 6: # gal
        tTxSeconds = float(measurement['ReceivedSvTimeNanos']) * NS_TO_S
    else:
        tTxSeconds = 0

    #tTxSeconds = measurement['ReceivedSvTimeNanos'] * NS_TO_S

    # Compute the travel time, which will be eventually the pseudorange
    tau = tRxSeconds - tTxSeconds

    # Check the week rollover, for measurements near the week transition
    if tau < 0:
        tau += GPS_WEEKSECS

    # Compute the range as the difference between the received time and
    # the transmitted time
    range = tau * SPEED_OF_LIGHT - pseudorange_bias

    # Check if the range needs to be modified with the range rate in
    # order to make it consistent with the timestamp
    if integerize:
        range -= frac * measurement['PseudorangeRateMetersPerSecond']

    wavelength = SPEED_OF_LIGHT / get_frequency(measurement)

    # Process the accumulated delta range (i.e. carrier phase). This
    # needs to be translated from meters to cycles (i.e. RINEX format
    # specification)
    cphase = - measurement['AccumulatedDeltaRangeMeters'] / wavelength

    doppler = - measurement['PseudorangeRateMetersPerSecond'] / wavelength

    cn0 = measurement['Cn0DbHz']

    # # 有周跳相位置零
    # if lockflag:
    #     cphase = 0.0

    # 跟踪状态异常,伪距置零
    if trackflag:
        range = 0.0

    return { EPOCH_STR : epoch,
             satname : { 'C' + obscode : range,
                         'L' + obscode : cphase,
                         'D' + obscode : doppler,
                         'S' + obscode : cn0,
                         'TRACK': trackflag,
                         'LLI': lockflag
                         }
             }

def merge(measdict):
# ------------------------------------------------------------------------------

    """
    Merge a list of processed batches, which are dictonaries with an epoch
    and an internal dictionary with the satellite measurements

    """

    res = None

    for m in measdict:

        # Skip emtpy measurements
        if m is None:
            continue

        # Initialize
        if res is None:
            res = m
            continue

        exp_epoch = res[EPOCH_STR]
        got_epoch = m[EPOCH_STR]

        if got_epoch != exp_epoch:
            sys.stderr.write("Wrong measurement when merging batches. Expected "
                             "[ {0} ], got [ {1} ]. Will be skipped\n".format(exp_epoch, got_epoch))
            continue

        # Lambda method to get the satellites from the batch
        satsin = lambda x : [k for k in x.keys() if k is not EPOCH_STR]

        exp_sats = satsin(res)
        got_sats = satsin(m)

        # Loop over all the got satellites and merge them
        for sat in got_sats:

            if sat in exp_sats:
                res[sat].update(m[sat])
            else:
                res[sat] = m[sat]

    return res

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import doctest
    doctest.testmod(raise_on_error=True)
