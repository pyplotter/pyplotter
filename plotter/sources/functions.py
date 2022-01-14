# This Python file uses the following encoding: utf-8
from math import log10
from typing import Union, Tuple


def _parse_number(number: float,
                  precision: int,
                  inverse: bool=False,
                  unified: bool=False) -> Union[str, Tuple[str, str]]:
    if number!=0:
        power_ten = int(log10(abs(number))//3*3)
    else:
        power_ten = 0

    if power_ten>=-24 and power_ten<=18 :

        prefix = {-24 : 'y',
                  -21 : 'z',
                  -18 : 'a',
                  -15 : 'p',
                  -12 : 'p',
                   -9 : 'n',
                   -6 : 'µ',
                   -3 : 'm',
                    0 : '',
                    3 : 'k',
                    6 : 'M',
                    9 : 'G',
                   12 : 'T',
                   15 : 'p',
                   18 : 'E'}

        if inverse:
            if unified:
                return '{} {}'.format(round(number*10.**-power_ten, precision), prefix[-power_ten])
            else:
                return str(round(number*10.**-power_ten, precision)), prefix[-power_ten]
        else:
            if unified:
                return '{} {}'.format(round(number*10.**-power_ten, precision), prefix[power_ten])
            else:
                return str(round(number*10.**-power_ten, precision)), prefix[power_ten]
    else:
        return str(round(number, precision)), ''
