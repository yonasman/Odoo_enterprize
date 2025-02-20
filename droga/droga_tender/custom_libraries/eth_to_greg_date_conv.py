from calendar import month
from datetime import date, datetime


class converter:
    @staticmethod
    def eth_to_greg_convert(dd,mm,yyyy):
        if(mm+8>12):
            month_converted=(mm+8)-12 
            month_to_compare=(mm+8)-12
        else:
            month_converted=mm+8
            month_to_compare=mm+8

        if mm+8>12:
            year_converted=yyyy+8
        else:
            year_converted=yyyy+7

        if year_converted>2000:
            year_converted-=2000

        day_converted=0
        if (mm in [1,2] and yyyy%4==0):
            day_converted=dd+11
        elif(mm in [3,4] and yyyy%4==0) or (mm in [1,2] and yyyy%4!=0):
            day_converted=dd+10
        elif(mm in [5,7] and yyyy%4==0) or (mm in [3,4,7] and yyyy%4!=0) or (yyyy%4==0 and mm==6 and dd>21) or (yyyy%4!=0 and mm==6 and dd<21):
            day_converted=dd+9
        elif(mm in [8,9] and yyyy%4==0) or (mm in [5,8,9] and yyyy%4!=0) or (yyyy%4==0 and mm==6 and dd<21):
            day_converted=dd+8
        elif (mm in [10,11]) or (yyyy%4!=0 and mm==6 and dd<21):
            day_converted=dd+7
        elif mm==12:
            day_converted=dd+6
        elif mm==13:
            day_converted=dd+5

        if(month_converted in [1,3,5,7,8,10,12] and day_converted>31):
            month_converted=month_converted+1
            day_converted=day_converted-31
        elif(month_converted in [4,6,9,11] and day_converted>30):
            month_converted=month_converted+1
            day_converted=day_converted-30
        elif(month_converted ==2 and day_converted>29 and year_converted%4==0):
            month_converted=month_converted+1
            day_converted=day_converted-29
        elif(month_converted ==2 and day_converted>28 and year_converted%4!=0):
            month_converted=month_converted+1
            day_converted=day_converted-28

        if(month_to_compare!=month_converted and month_to_compare==12):
            year_converted=year_converted+1

        if(month_converted>12):
            month_converted=month_converted-12

        return datetime(year_converted,month_converted,day_converted)

