This modules provides Decliner for Latin. Given a lemma, the Decliner will provide each grammatically valid forms. 

## About

This work is based on the lexical and linguistic data built for and by the Collatinus Team ( https://github.com/biblissima/collatinus ). Therefore, this module inherits the license from the original project (GNU GPLv3). The objective of this module is to port part of Collatinus to CLTK.

The original data are the results of more than a decade of recension done by Philippe Verkerk and Yves Ouvrard. The converter and original modifications were provided by Thibault Clérice.

## How to ?

To update the resources, you need python3.4 or higher and run `python3 __convert.py` in the `lemmata/collatinus` directory. We keep original data to keep tracks of modifications. There might be some modification made to original collatinus data as the Python Decliner is much more dependent on well formatted data than the C++ Original Implementation.
