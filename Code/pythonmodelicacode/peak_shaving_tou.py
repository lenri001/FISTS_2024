def peak_shaving_tou(dblInp):
    import pandas as pd
    import os
    [net_load, SOC, time] = dblInp
    
    def label_from_timestamp(df):
        # -*- coding: utf-8 -*-

        #  python-holidays
        #  ---------------
        #  A fast, efficient Python library for generating country, province and state
        #  specific sets of holidays on the fly. It aims to make determining whether a
        #  specific date is a holiday as fast and flexible as possible.
        #
        #  Author:  ryanss <ryanssdev@icloud.com> (c) 2014-2017
        #           dr-prodigy <maurizio.montel@gmail.com> (c) 2017-2020
        #  Website: https://github.com/dr-prodigy/python-holidays
        #  License: MIT (see LICENSE file)

        from datetime import date, datetime, timedelta
        from dateutil.easter import easter, EASTER_ORTHODOX
        from dateutil.parser import parse
        from dateutil.relativedelta import relativedelta as rd
        from dateutil.relativedelta import MO, TU, WE, TH, FR, SA, SU
        import inspect
        import six
        import sys
        import warnings
        import pandas as pd
        import holidays

        __version__ = '0.9.12'

        MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
        WEEKEND = (SAT, SUN)

        JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, \
            NOV, DEC = range(1, 13)


        class HolidayBase(dict):
            PROVINCES = []

            def __init__(self, years=[], expand=True, observed=True,
                         prov=None, state=None):
                self.observed = observed
                self.expand = expand
                if isinstance(years, int):
                    years = [years, ]
                self.years = set(years)
                if not getattr(self, 'prov', False):
                    self.prov = prov
                self.state = state
                for year in list(self.years):
                    self._populate(year)

            def __setattr__(self, key, value):
                if key == 'observed' and len(self) > 0:
                    dict.__setattr__(self, key, value)
                    if value is True:
                        # Add (Observed) dates
                        years = list(self.years)
                        self.years = set()
                        self.clear()
                        for year in years:
                            self._populate(year)
                    else:
                        # Remove (Observed) dates
                        for k, v in list(self.items()):
                            if v.find("Observed") >= 0:
                                del self[k]
                else:
                    return dict.__setattr__(self, key, value)

            def __keytransform__(self, key):
                if isinstance(key, datetime):
                    key = key.date()
                elif isinstance(key, date):
                    key = key
                elif isinstance(key, int) or isinstance(key, float):
                    key = datetime.utcfromtimestamp(key).date()
                elif isinstance(key, six.string_types):
                    try:
                        key = parse(key).date()
                    except (ValueError, OverflowError):
                        raise ValueError("Cannot parse date from string '%s'" % key)
                else:
                    raise TypeError("Cannot convert type '%s' to date." % type(key))

                if self.expand and key.year not in self.years:
                    self.years.add(key.year)
                    self._populate(key.year)
                return key

            def __contains__(self, key):
                return dict.__contains__(self, self.__keytransform__(key))

            def __getitem__(self, key):
                if isinstance(key, slice):
                    if not key.start or not key.stop:
                        raise ValueError("Both start and stop must be given.")

                    start = self.__keytransform__(key.start)
                    stop = self.__keytransform__(key.stop)

                    if key.step is None:
                        step = 1
                    elif isinstance(key.step, timedelta):
                        step = key.step.days
                    elif isinstance(key.step, int):
                        step = key.step
                    else:
                        raise TypeError(
                            "Cannot convert type '%s' to int." % type(key.step)
                        )

                    if step == 0:
                        raise ValueError('Step value must not be zero.')

                    date_diff = stop - start
                    if date_diff.days < 0 <= step or date_diff.days >= 0 > step:
                        step *= -1

                    days_in_range = []
                    for delta_days in range(0, date_diff.days, step):
                        day = start + timedelta(days=delta_days)
                        try:
                            dict.__getitem__(
                                self,
                                day
                            )
                            days_in_range.append(day)
                        except (KeyError):
                            pass
                    return days_in_range
                return dict.__getitem__(self, self.__keytransform__(key))

            def __setitem__(self, key, value):
                if key in self:
                    if self.get(key).find(value) < 0 \
                            and value.find(self.get(key)) < 0:
                        value = "%s, %s" % (value, self.get(key))
                    else:
                        value = self.get(key)
                return dict.__setitem__(self, self.__keytransform__(key), value)

            def update(self, *args):
                args = list(args)
                for arg in args:
                    if isinstance(arg, dict):
                        for key, value in list(arg.items()):
                            self[key] = value
                    elif isinstance(arg, list):
                        for item in arg:
                            self[item] = "Holiday"
                    else:
                        self[arg] = "Holiday"

            def append(self, *args):
                return self.update(*args)

            def get(self, key, default=None):
                return dict.get(self, self.__keytransform__(key), default)

            def get_list(self, key):
                return [h for h in self.get(key, "").split(", ") if h]

            def pop(self, key, default=None):
                if default is None:
                    return dict.pop(self, self.__keytransform__(key))
                return dict.pop(self, self.__keytransform__(key), default)

            def __eq__(self, other):
                return dict.__eq__(self, other) and self.__dict__ == other.__dict__

            def __ne__(self, other):
                return dict.__ne__(self, other) or self.__dict__ != other.__dict__

            def __add__(self, other):
                if isinstance(other, int) and other == 0:
                    # Required to sum() list of holidays
                    # sum([h1, h2]) is equivalent to (0 + h1 + h2)
                    return self
                elif not isinstance(other, HolidayBase):
                    raise TypeError()
                HolidaySum = createHolidaySum(self, other)
                country = (getattr(self, 'country', None) or
                           getattr(other, 'country', None))
                if self.country and other.country and self.country != other.country:
                    c1 = self.country
                    if not isinstance(c1, list):
                        c1 = [c1]
                    c2 = other.country
                    if not isinstance(c2, list):
                        c2 = [c2]
                    country = c1 + c2
                prov = getattr(self, 'prov', None) or getattr(other, 'prov', None)
                if self.prov and other.prov and self.prov != other.prov:
                    p1 = self.prov if isinstance(self.prov, list) else [self.prov]
                    p2 = other.prov if isinstance(other.prov, list) else [other.prov]
                    prov = p1 + p2
                return HolidaySum(years=(self.years | other.years),
                                  expand=(self.expand or other.expand),
                                  observed=(self.observed or other.observed),
                                  country=country, prov=prov)

            def __radd__(self, other):
                return self.__add__(other)

            def _populate(self, year):
                pass


        def createHolidaySum(h1, h2):
            class HolidaySum(HolidayBase):

                def __init__(self, country, **kwargs):
                    self.country = country
                    self.holidays = []
                    if getattr(h1, 'holidays', False):
                        for h in h1.holidays:
                            self.holidays.append(h)
                    else:
                        self.holidays.append(h1)
                    if getattr(h2, 'holidays', False):
                        for h in h2.holidays:
                            self.holidays.append(h)
                    else:
                        self.holidays.append(h2)
                    HolidayBase.__init__(self, **kwargs)

                def _populate(self, year):
                    for h in self.holidays[::-1]:
                        h._populate(year)
                        self.update(h)

            return HolidaySum


        def list_supported_countries():
            """List all supported countries incl. their abbreviation."""
            return [name for name, obj in
                    inspect.getmembers(sys.modules[__name__], inspect.isclass)
                    if obj.__module__ is __name__]


        def CountryHoliday(country, years=[], prov=None, state=None, expand=True,
                           observed=True):
            try:
                country_holiday = globals()[country](years=years,
                                                     prov=prov,
                                                     state=state,
                                                     expand=expand,
                                                     observed=observed)
            except (KeyError):
                raise KeyError("Country %s not available" % country)
            return country_holiday

        class UsElectricHolidays(holidays.HolidayBase):

            def _populate(self, year):
                 # New Year's Day
                if year > 1870:
                    name = "New Year's Day"
                    self[date(year, JAN, 1)] = name
                    if self.observed and date(year, JAN, 1).weekday() == SUN:
                        self[date(year, JAN, 1) + rd(days=+1)] = name + \
                            " (Observed)"

                # Washington's Birthday
                name = "Washington's Birthday"
                if year > 1970:
                    self[date(year, FEB, 1) + rd(weekday=MO(+3))] = name
                elif year >= 1879:
                    self[date(year, FEB, 22)] = name

                # Memorial Day
                if year > 1970:
                    self[date(year, MAY, 31) + rd(weekday=MO(-1))] = "Memorial Day"
                elif year >= 1888:
                    self[date(year, MAY, 30)] = "Memorial Day"

                # Independence Day
                if year > 1870:
                    name = "Independence Day"
                    self[date(year, JUL, 4)] = name
                    if self.observed and date(year, JUL, 4).weekday() == SUN:
                        self[date(year, JUL, 4) + rd(days=+1)] = name + " (Observed)"

                # Labor Day
                if year >= 1894:
                    self[date(year, SEP, 1) + rd(weekday=MO)] = "Labor Day"

                # Veterans Day
                if year > 1953:
                    name = "Veterans Day"
                else:
                    name = "Armistice Day"
                if 1978 > year > 1970:
                    self[date(year, OCT, 1) + rd(weekday=MO(+4))] = name
                elif year >= 1938:
                    self[date(year, NOV, 11)] = name
                    if self.observed \
                            and date(year, NOV, 11).weekday() == SUN:
                        self[date(year, NOV, 11) + rd(days=+1)] = name + \
                            " (Observed)"

                # Thanksgiving
                if year > 1870:
                    self[date(year, NOV, 1) + rd(weekday=TH(+4))] = "Thanksgiving"

                # Christmas Day
                if year > 1870:
                    name = "Christmas Day"
                    self[date(year, DEC, 25)] = "Christmas Day"
                    if self.observed \
                            and date(year, DEC, 25).weekday() == SUN:
                        self[date(year, DEC, 25) + rd(days=+1)] = name + \
                            " (Observed)"

        us_holidays = UsElectricHolidays()

        def label_weekends(df, timestamp_name):
            # Make the index the date
            df.index = df[timestamp_name]

            # Creates column for day of the week: 0 = Monday to 6 = Sunday
            df['DayWeek'] = df[timestamp_name].dt.dayofweek 
            # .apply run a function through every line of code without usong a for loop
            # lambda is a temporay function 
            # If x >= 5 set true (boolean statement) since it is the weekend # 5 is Saturday and 6 is Sunday
            # Returns boolean staement where weekend is true 
            df['Is_Weekend'] = df['DayWeek'].apply(lambda x: True if x >= 5 else False )
            # Creates an array for all the US Holidays in California
            # us_holidays = holidays.CountryHoliday('US')
            # Uses apply and lambda again to check if there is a holiday 
            # X in holiday returns a boolean satement 
            # .apply runs this function thorugh the entire Date column 
            # Returns a new boolean column where holidays is true 
            df['Is_Holiday'] = df[timestamp_name].apply(lambda x: True if x in us_holidays else False )
            # Creates a month column 
            df['month'] = df[timestamp_name].dt.month
            # Creates a new column of Boolean satements of where summer is true
            # 6 is June and 9 is September
            df['is_summer'] = df[timestamp_name].dt.month.between(6,9)

            # This function determines the four catogories of Summer Weekend, Winter Weekend, Summer Weekday, Winter Weekday
            # The function takes in 4 columns in the dataframme
            # THhe .apply() function passes in one variable at a time from each column
            def peak_fun(vec):
                Date = vec[0] # First Column Date, .apply() Passes in a timestamp not a vector
                Is_Weekend = vec[1] # Second Column Is Weekend, .apply() Passes in a bool not a vector
                Is_Holiday = vec[2] # Third Column Is Holiday, .apply() Passes in a bool not a vector
                Is_Summer = vec[3] # Fourth Column Is Summer, .apply() Passes in a bool not a vector
                if Is_Weekend or Is_Holiday:
                    if Is_Summer:
                        return 'Summer_Weekend'       
                    else:
                        return 'Winter_Weekend'
                else:
                    if Is_Summer:
                        return 'Summer_Weekday'
                    else:
                        return 'Winter_Weekday'

            # Pass in the 4 columns and use the .apply() function
            df['fun'] = df[[timestamp_name, 'Is_Weekend', 'Is_Holiday', 'is_summer']].apply(peak_fun, axis = 1)
            return df 
        # Edison TOU Pricing New

        # Summer Weekday Time
        su_wdy_sofpk = False
        su_wdy_ofpk = ['0:00','8:00','23:00','0:00']
        su_wdy_mdpk = ['8:00', '12:00', '18:00', '23:00']
        su_wdy_onpk = ['12:00', '18:00']

        # Summer Weekend Time
        su_wkd_sofpk = False
        su_wkd_ofpk = ['0:00','21:00','21:00','0:00']
        su_wkd_mdpk = False
        su_wkd_onpk = False

        # Winter Weekday Time
        wt_wdy_sofpk = False
        wt_wdy_ofpk = ['0:00','8:00','21:00','0:00']
        wt_wdy_mdpk = ['8:00', '17:00']
        wt_wdy_onpk = ['17:00', '21:00']

        # Winter Weekend Time
        wt_wkd_sofpk = False
        wt_wkd_ofpk = ['0:00','21:00','21:00','0:00']
        wt_wkd_mdpk = False
        wt_wkd_onpk = False

        def summer_weekday(su_wdy_sofpk, su_wdy_ofpk, su_wdy_mdpk, su_wdy_onpk, df):

            if su_wdy_sofpk != False:
                len_su_wdy_sofpk = int(len(su_wdy_sofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wdy_sofpk,1):
                    selection = df[df['fun'] == 'Summer_Weekday'].between_time(su_wdy_sofpk[begin],su_wdy_sofpk[end], inclusive='left')
                    selection["Peak"] = "Super Off-Peak"
                    ww = df["fun"] == "Summer_Weekday"
                    df.loc[df[ww].between_time(su_wdy_sofpk[begin], su_wdy_sofpk[end], inclusive='left').index, "Peak"] = "Super Off-Peak"
                    begin += 2
                    end += 2

            if su_wdy_ofpk != False:
                len_su_wdy_ofpk = int(len(su_wdy_ofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wdy_ofpk,1):
                    selection = df[df['fun'] == 'Summer_Weekday'].between_time(su_wdy_ofpk[begin],su_wdy_ofpk[end], inclusive='left')
                    selection["Peak"] = "Off-Peak"
                    ww = df["fun"] == "Summer_Weekday"
                    df.loc[df[ww].between_time(su_wdy_ofpk[begin], su_wdy_ofpk[end], inclusive='left').index, "Peak"] = "Off-Peak"
                    begin += 2
                    end += 2

            if su_wdy_mdpk != False:
                len_su_wdy_mdpk = int(len(su_wdy_mdpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wdy_mdpk,1):
                    selection = df[df['fun'] == 'Summer_Weekday'].between_time(su_wdy_mdpk[begin],su_wdy_mdpk[end], inclusive='left')
                    selection["Peak"] = "Mid-Peak"
                    ww = df["fun"] == "Summer_Weekday"
                    df.loc[df[ww].between_time(su_wdy_mdpk[begin], su_wdy_mdpk[end], inclusive='left').index, "Peak"] = "Mid-Peak"
                    begin += 2
                    end += 2

            if su_wdy_onpk != False:
                len_su_wdy_onpk = int(len(su_wdy_onpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wdy_onpk,1):
                    selection = df[df['fun'] == 'Summer_Weekday'].between_time(su_wdy_onpk[begin],su_wdy_onpk[end], inclusive='left')
                    selection["Peak"] = "On-Peak"
                    ww = df["fun"] == "Summer_Weekday"
                    df.loc[df[ww].between_time(su_wdy_onpk[begin], su_wdy_onpk[end], inclusive='left').index, "Peak"] = "On-Peak"
                    begin += 2
                    end += 2
            return df

        def summer_weekend(su_wkd_sofpk, su_wkd_ofpk, su_wkd_mdpk, su_wkd_onpk, df):

            if su_wkd_sofpk != False:
                len_su_wkd_sofpk = int(len(su_wkd_sofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wkd_sofpk,1):
                    selection = df[df['fun'] == 'Summer_Weekend'].between_time(su_wkd_sofpk[begin],su_wkd_sofpk[end], inclusive='left')
                    selection["Peak"] = "Super Off-Peak"
                    ww = df["fun"] == "Summer_Weekend"
                    df.loc[df[ww].between_time(su_wkd_sofpk[begin], su_wkd_sofpk[end], inclusive='left').index, "Peak"] = "Super Off-Peak"
                    begin += 2
                    end += 2

            if su_wkd_ofpk != False:
                len_su_wkd_ofpk = int(len(su_wkd_ofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wkd_ofpk,1):
                    selection = df[df['fun'] == 'Summer_Weekend'].between_time(su_wkd_ofpk[begin],su_wkd_ofpk[end], inclusive='left')
                    selection["Peak"] = "Off-Peak"
                    ww = df["fun"] == "Summer_Weekend"
                    df.loc[df[ww].between_time(su_wkd_ofpk[begin], su_wkd_ofpk[end], inclusive='left').index, "Peak"] = "Off-Peak"
                    begin += 2
                    end += 2

            if su_wkd_mdpk != False:
                len_su_wkd_mdpk = int(len(su_wkd_mdpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wkd_mdpk,1):
                    selection = df[df['fun'] == 'Summer_Weekend'].between_time(su_wkd_mdpk[begin],su_wkd_mdpk[end], inclusive='left')
                    selection["Peak"] = "Mid-Peak"
                    ww = df["fun"] == "Summer_Weekend"
                    df.loc[df[ww].between_time(su_wkd_mdpk[begin], su_wkd_mdpk[end], inclusive='left').index, "Peak"] = "Mid-Peak"
                    begin += 2
                    end += 2

            if su_wkd_onpk != False:
                len_su_wkd_onpk = int(len(su_wkd_onpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_su_wkd_onpk,1):
                    selection = df[df['fun'] == 'Summer_Weekend'].between_time(su_wkd_onpk[begin],su_wkd_onpk[end], inclusive='left')
                    selection["Peak"] = "On-Peak"
                    ww = df["fun"] == "Summer_Weekend"
                    df.loc[df[ww].between_time(su_wkd_onpk[begin], su_wkd_onpk[end], inclusive='left').index, "Peak"] = "On-Peak"
                    begin += 2
                    end += 2
            return df

        def winter_weekday(wt_wdy_sofpk, wt_wdy_ofpk, wt_wdy_mdpk, wt_wdy_onpk, df):

            if wt_wdy_sofpk != False:
                len_wt_wdy_sofpk = int(len(wt_wdy_sofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wdy_sofpk,1):
                    selection = df[df['fun'] == 'Winter_Weekday'].between_time(wt_wdy_sofpk[begin],wt_wdy_sofpk[end], inclusive='left')
                    selection["Peak"] = "Super Off-Peak"
                    ww = df["fun"] == "Winter_Weekday"
                    df.loc[df[ww].between_time(wt_wdy_sofpk[begin], wt_wdy_sofpk[end], inclusive='left').index, "Peak"] = "Super Off-Peak"
                    begin += 2
                    end += 2

            if wt_wdy_ofpk != False:
                len_wt_wdy_ofpk = int(len(wt_wdy_ofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wdy_ofpk,1):
                    selection = df[df['fun'] == 'Winter_Weekday'].between_time(wt_wdy_ofpk[begin],wt_wdy_ofpk[end], inclusive='left')
                    selection["Peak"] = "Off-Peak"
                    ww = df["fun"] == "Winter_Weekday"
                    df.loc[df[ww].between_time(wt_wdy_ofpk[begin], wt_wdy_ofpk[end], inclusive='left').index, "Peak"] = "Off-Peak"
                    begin += 2
                    end += 2

            if wt_wdy_mdpk != False:
                len_wt_wdy_mdpk = int(len(wt_wdy_mdpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wdy_mdpk,1):
                    selection = df[df['fun'] == 'Winter_Weekday'].between_time(wt_wdy_mdpk[begin],wt_wdy_mdpk[end], inclusive='left')
                    selection["Peak"] = "Mid-Peak"
                    ww = df["fun"] == "Winter_Weekday"
                    df.loc[df[ww].between_time(wt_wdy_mdpk[begin], wt_wdy_mdpk[end], inclusive='left').index, "Peak"] = "Mid-Peak"
                    begin += 2
                    end += 2

            if wt_wdy_onpk != False:
                len_wt_wdy_onpk = int(len(wt_wdy_onpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wdy_onpk,1):
                    selection = df[df['fun'] == 'Winter_Weekday'].between_time(wt_wdy_onpk[begin],wt_wdy_onpk[end], inclusive='left')
                    selection["Peak"] = "On-Peak"
                    ww = df["fun"] == "Winter_Weekday"
                    df.loc[df[ww].between_time(wt_wdy_onpk[begin], wt_wdy_onpk[end], inclusive='left').index, "Peak"] = "On-Peak"
                    begin += 2
                    end += 2
            return df

        def winter_weekend(wt_wkd_sofpk, wt_wkd_ofpk, wt_wkd_mdpk, wt_wkd_onpk, df):

            if wt_wkd_sofpk != False:
                len_wt_wkd_sofpk = int(len(wt_wkd_sofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wkd_sofpk,1):
                    selection = df[df['fun'] == 'Winter_Weekend'].between_time(wt_wkd_sofpk[begin],wt_wkd_sofpk[end], inclusive='left')
                    selection["Peak"] = "Super Off-Peak"
                    ww = df["fun"] == "Winter_Weekend"
                    df.loc[df[ww].between_time(wt_wkd_sofpk[begin], wt_wkd_sofpk[end], inclusive='left').index, "Peak"] = "Super Off-Peak"
                    begin += 2
                    end += 2

            if wt_wkd_ofpk != False:
                len_wt_wkd_ofpk = int(len(wt_wkd_ofpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wkd_ofpk,1):
                    selection = df[df['fun'] == 'Winter_Weekend'].between_time(wt_wkd_ofpk[begin],wt_wkd_ofpk[end], inclusive='left')
                    selection["Peak"] = "Off-Peak"
                    ww = df["fun"] == "Winter_Weekend"
                    df.loc[df[ww].between_time(wt_wkd_ofpk[begin], wt_wkd_ofpk[end], inclusive='left').index, "Peak"] = "Off-Peak"
                    begin += 2
                    end += 2

            if wt_wkd_mdpk != False:
                len_wt_wkd_mdpk = int(len(wt_wkd_mdpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wkd_mdpk,1):
                    selection = df[df['fun'] == 'Winter_Weekend'].between_time(wt_wkd_mdpk[begin],wt_wkd_mdpk[end], inclusive='left')
                    selection["Peak"] = "Mid-Peak"
                    ww = df["fun"] == "Winter_Weekend"
                    df.loc[df[ww].between_time(wt_wkd_mdpk[begin], wt_wkd_mdpk[end], inclusive='left').index, "Peak"] = "Mid-Peak"
                    begin += 2
                    end += 2

            if wt_wkd_onpk != False:
                len_wt_wkd_onpk = int(len(wt_wkd_onpk)/2)
                begin = 0
                end = 1
                for i in range(0,len_wt_wkd_onpk,1):
                    selection = df[df['fun'] == 'Winter_Weekend'].between_time(wt_wkd_onpk[begin],wt_wkd_onpk[end], inclusive='left')
                    selection["Peak"] = "On-Peak"
                    ww = df["fun"] == "Winter_Weekend"
                    df.loc[df[ww].between_time(wt_wkd_onpk[begin], wt_wkd_onpk[end], inclusive='left').index, "Peak"] = "On-Peak"
                    begin += 2
                    end += 2
            return df

        def label_peaks(df):
            winter_weekend(wt_wkd_sofpk, wt_wkd_ofpk, wt_wkd_mdpk, wt_wkd_onpk, df)
            winter_weekday(wt_wdy_sofpk, wt_wdy_ofpk, wt_wdy_mdpk, wt_wdy_onpk, df)
            summer_weekday(su_wdy_sofpk, su_wdy_ofpk, su_wdy_mdpk, su_wdy_onpk, df)
            summer_weekend(su_wkd_sofpk, su_wkd_ofpk, su_wkd_mdpk, su_wkd_onpk, df)

        df = label_weekends(df, 'time')
        label_peaks(df)
        df = df.reset_index(drop = True)
        return [df.Peak[0], df.month[0]]


    epoch_timeshift = 1646092800
    
    time += epoch_timeshift

#    print(pd.DataFrame({'time' : [pd.Timestamp(time, unit = 's')]}))
    
    
    peak, month = label_from_timestamp(pd.DataFrame({'time' : [pd.Timestamp(time, unit = 's')]}))
    peak_tou = "df.feather"  
    if os.path.exists(peak_tou):
        df = pd.read_feather(peak_tou)
        [on_peak, mid_peak, off_peak, super_off_peak, last_month] = df.iloc[0].tolist()
    else: 
        df = pd.DataFrame({'On-Peak': [0], 'Mid-Peak': [0], 'Off-Peak': [0], 'Super Off-Peak': [0], 'Month': [0]})
        [on_peak, mid_peak, off_peak, super_off_peak, last_month] = df.iloc[0].tolist()
    if (peak == "On-Peak"):
        if month > last_month:
            on_peak = 0
        if ((net_load <= -15000) and (SOC > 0.20) and (net_load >= -100000)):
            ivt_ctrl = -1 * abs(net_load + 15000)
        elif ((net_load <= -100000) and (SOC > 0.20)):
            ivt_ctrl = -100000
        elif ((net_load >= 0) and (SOC < 0.90) and (net_load < 100000)):
            ivt_ctrl = (net_load);
        elif ((SOC < 0.90) and (net_load >= 100000)):
            ivt_ctrl = 100000
        else:
            ivt_ctrl = 0
        
    elif (peak == "Mid-Peak"):
        if month > last_month:
            mid_peak = 0
        if mid_peak <= net_load:
            mid_peak = net_load
            if ((net_load <= -15000) and (SOC > 0.20) and (net_load >= -100000)):
                ivt_ctrl = -1 * abs(net_load + 15000)
            elif ((net_load <= -100000) and (SOC > 0.20)):
                ivt_ctrl = -100000
            elif ((net_load >= 0) and (SOC < 0.90) and (net_load < 100000)):
                ivt_ctrl = (net_load);
            elif ((SOC < 0.90) and (net_load >= 100000)):
                ivt_ctrl = 100000
            else:
                ivt_ctrl = 0
        else:
            ivt_ctrl = 0
        
    elif (peak == "Off-Peak"):
        if month > last_month:
            off_peak = 0
        if off_peak <= net_load:
            off_peak = net_load
            if ((net_load <= -15000) and (SOC > 0.20) and (net_load >= -100000)):
                ivt_ctrl = -1 * abs(net_load + 15000)
            elif ((net_load <= -100000) and (SOC > 0.20)):
                ivt_ctrl = -100000
            elif ((net_load >= 0) and (SOC < 0.90) and (net_load < 100000)):
                ivt_ctrl = (net_load);
            elif ((SOC < 0.90) and (net_load >= 100000)):
                ivt_ctrl = 100000
            else:
                ivt_ctrl = 0
        else:
            ivt_ctrl = 0
        
    elif (peak == "Super Off-Peak"):
        if month > last_month:
            super_off_peak = 0
        if super_off_peak <= net_load:
            super_off_peak = net_load
            if ((net_load <= -15000) and (SOC > 0.20) and (net_load >= -100000)):
                ivt_ctrl = -1 * abs(net_load + 15000)
            elif ((net_load <= -100000) and (SOC > 0.20)):
                ivt_ctrl = -100000
            elif ((net_load >= 0) and (SOC < 0.90) and (net_load < 100000)):
                ivt_ctrl = (net_load);
            elif ((SOC < 0.90) and (net_load >= 100000)):
                ivt_ctrl = 100000
            else:
                ivt_ctrl = 0
        else:
            ivt_ctrl = 0
    df.iloc[0] = [on_peak, mid_peak, off_peak, super_off_peak, month]
    df.to_feather('peak_tou.feather')
            
    return int(ivt_ctrl)
