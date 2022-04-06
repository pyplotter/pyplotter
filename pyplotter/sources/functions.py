# This Python file uses the following encoding: utf-8
from math import log10
from typing import Union, Tuple


def _parse_number(number: float,
                  precision: int,
                  inverse: bool=False,
                  unified: bool=False) -> Union[str, Tuple[str, str]]:
    """
    Return a number parsed form human reading with SI prefix
    Example:
        parse_number(1.23456789e-7, 3) -> ('123.457', 'n')
        parse_number(1.23456789e-7, 3) -> ('123.5', 'n')
        parse_number(1.6978e-7, 3, True) -> ('169.78', 'G')

    Args:
        number:
            Number to be parsed
        precision:
            Precision to round the number after the decimal
        inverse:
            If True, returns the inverse of the SI prefix.
            Defaults to False.
        unified:
        If True, return an unique string such as
            parse_number(1.23456789e-7, 3) -> ('123.457 n')
            parse_number(1.23456789e-7, 3) -> ('123.5 n')
            parse_number(1.6978e-7, 3, True) -> ('169.78 G')
    """

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
