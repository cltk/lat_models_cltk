# Quick script to produce complete collatinus transformation
# Data come from https://github.com/biblissima/collatinus/tree/master/bin/data
# See README.md at lemmata/collatinus/README.md
#
# This file needs to be run in collatinus working dir with python 3.4 or higher
#

import json
import re
from copy import deepcopy
import unicodedata



def normalize_unicode(lines):
    """ Transform lines into diacritics bytes free unicode
    """
    return unicodedata.normalize('NFKD', lines).encode('ASCII', 'ignore').decode()


#############################################################
# Convert morphos.la
# Each line of Morphos.la represents a declension name
#############################################################
search = re.compile(r'[^-]')
morphos = {}

with open("src/morphos.la") as f:
    for line in f.readlines():
        line = line.strip()
        if line.startswith("!") or len(line) < 2:
            pass
        else:
            # Person
            # If we have a person, we know it's a verb
            line = line\
                .replace("1ère", "v1-------")\
                .replace("2ème", "v2-------")\
                .replace("3ème", "v3-------")

            # Number
            line = line\
                .replace("singulier", "--s------")\
                .replace("pluriel",   "--p------")

            # Tense
            line = line\
                .replace("présent",         "---p-----")\
                .replace("imparfait",       "---i-----")\
                .replace("parfait",         "---r-----")\
                .replace("PQP",             "---l-----")\
                .replace("futur antérieur", "---t-----")\
                .replace("futur",           "---f-----")

            # Mood
            line = line\
                .replace("indicatif",       "----i----")\
                .replace("subjonctif",      "----s----")\
                .replace("infinitif",       "v---n----")\
                .replace("impératif",       "----m----")\
                .replace("gérondif",        "----g----")\
                .replace("adjectif verbal", "----g----")\
                .replace("participe",       "g---p----")\
                .replace("supin en -um",    "----u----")\
                .replace("supin en -u",     "----u----")

            # Voice
            line = line\
                .replace("actif",  "-----a---")\
                .replace("passif", "-----p---")

            # Gender
            line = line\
                .replace("masculin", "------m--")\
                .replace("féminin",  "------f--")\
                .replace("neutre",   "------n--")

            # Case
            line = line\
                .replace("nominatif", "-------n-")\
                .replace("génitif",   "-------g-")\
                .replace("accusatif", "-------a-")\
                .replace("datif",     "-------d-")\
                .replace("ablatif",   "-------b-")\
                .replace("vocatif",   "-------v-")\
                .replace("locatif",   "-------l-")

            # Degree
            line = line\
                .replace("comparatif", "a-------c")\
                .replace("superlatif", "a-------s")\
                .replace("positif",    "a-------p")

            line = line.replace("461:", "416:--------")

            # Then we merge the tags
            new_tag = "---------"
            index, tags = line.split(":")
            tags = tags.split()

            for tag in tags:
                for x in search.finditer(tag):
                    i = x.start()
                    new_tag = new_tag[:i] + tag[i] + new_tag[i+1:]

            morphos[index] = new_tag

assert morphos["190"] == "--sppamv-"
assert morphos["121"] == "v1spia---"

#############################################################
# Convert modeles.la
# Line starting with $ are variable that can be reused
# Set of line starting with model are models
# R:int:int,int (Root number, Character to remove to get canonical form, number of character to add to get the root)
#  -> eg. : for uita, R:1:1,0 would get root 1, 1 character to remove, 0 to add -> uit
#  -> eg. : for epulae, R:1:2,0 would get root 1, 2 character to remove, 0 to add : epul
#############################################################


def parse_range(des_number):
    """ Range

    :return: Int reprenting element of the range
    """
    ids = []
    for des_group in des_number.split(","):  # When we have ";", we should parse it normally
        if "-" in des_group:
            start, end = tuple([int(x) for x in des_group.split("-")])
            ids += list(range(start, end + 1))
        else:
            ids += [int(des_group)]
    return ids


def convert_models(lines):
    models = {}
    __model = {
        "R": {},
        "abs": [],  # Unused desinence if inherits
        "des": {},  # Dict of desinences
        "suf": [],  # Dict of Suffixes
        "sufd": []  # Possible endings
    }
    __R = re.compile("^R:(?P<root>\d+):(?P<remove>\w+)[,:]?(?P<add>\w+)?", flags=re.UNICODE)
    __des = re.compile("^des[\+]?:(?P<range>[\d\-,]+):(?P<root>\d+):([\w\-,;]+)$", flags=re.UNICODE)
    last_model = None
    variable_replacement = {}

    for lineno, line in enumerate(lines):
        line = line.strip()
        # If we get a variable
        if line.startswith("$"):
            # We split the line on =
            var, rep = tuple(line.split("="))
            # We create a replacement variable
            variable_replacement[var] = rep
        elif len(line) > 0 and not line.startswith("!"):
            if line.startswith("modele:"):
                last_model = line[7:]
                models[last_model] = deepcopy(__model)
            elif line.startswith("pere:"):
                # Inherits from parent
                models[last_model].update(
                    deepcopy(models[line[5:]])
                )
            elif line.startswith("R:"):
                # Still do not know how to deal with "K"
                root, remove, chars = __R.match(line).groups()
                if chars == "0":
                    chars = ""
                models[last_model]["R"][root] = [remove, chars]
            elif line.startswith("des"):
                # We have new endings
                # des:range:root_number:list_of_des
                # First we apply desinence variables replacement
                if "$" in line:
                    for var, rep in variable_replacement.items():
                        # First we replace +$
                        line = re.sub(
                            "(\w+)(\+?\{})".format(var),
                            lambda x: (
                                ";".join([x.group(1) + r for r in rep.split(";")])
                            ),
                            line, flags=re.UNICODE
                        )
                        line = line.replace(var, rep)
                        if "$" not in line:
                            break
                try:
                    des_number, root, des = __des.match(line).groups()
                except AttributeError as E:
                    print(line)
                    raise E

                ids = parse_range(des_number)
                for i, d in zip(ids, des.split(";")):
                    if line.startswith("des+") and int(i) in models[last_model]["des"]:
                        models[last_model]["des"][int(i)].append((root, d.replace("-", "").split(",")))
                    else:
                        models[last_model]["des"][int(i)] = [(root, d.replace("-", "").split(","))]
            elif line.startswith("abs:"):
                models[last_model]["abs"] = parse_range(line[4:])  # Add the one we should not find as desi
            elif line.startswith("suf:"):
                rng, suf = tuple(line[4:].split(":"))
                models[last_model]["suf"].append([suf, list(parse_range(rng))])  # Suffixes are alternative ending
            elif line.startswith("sufd:"):
                models[last_model]["sufd"] += line[5:].split(",")  # Sufd are suffix always present
            else:
                print(line.split(":")[0])
    return models


with open("./src/modeles.la") as f:
    lines = normalize_unicode(f.read()).split("\n")
    norm_models = convert_models(lines)


assert norm_models["fortis"]["des"][13] == [("4", [''])],\
    "Root 4, Empty string (originally '-') expected, found %s %s" % norm_models["fortis"]["des"][13][0]
assert norm_models["fortis"]["des"][51] == [("1", ["iorem"])],\
    "Root 4, iorem expected, found %s %s" % norm_models["fortis"]["des"][50][0]
assert norm_models["dico"]["des"][181] == [("0", ["e"]), ("0", [""])],\
    "[(0, e), (0, ''), found %s %s " % tuple([str(x) for x in norm_models["dico"]["des"][181]])
assert norm_models["edo"]["des"][122] == [("0", ["is"]), ("3", ["es"])],\
    "[(0, is), (3, es), found %s %s " % tuple([str(x) for x in norm_models["edo"]["des"][122]])

############################################
#
#   Get the lemma converter
#
# lemma=lemma|model|genitive/infectum|perfectu|morpho indications
#
############################################

def parseLemma(lines):
    """

    :param lines:
    :param normalize:
    :return:
    """

    lemmas = {}
    regexp = re.compile("^(?P<lemma>\w+){1}(?P<quantity>\=\w+)?\|(?P<model>\w+)?\|[-]*(?P<geninf>[\w,]+)?[-]*\|[-]*(?P<perf>[\w,]+)?[-]*\|(?P<lexicon>.*)?", flags=re.UNICODE)

    for lineno, line in enumerate(lines):
        if not line.startswith("!") and "|" in line:
            if line.count("|") != 4:
                # We need to clean up the mess
                # Some line lacks a |
                # I assume this means we need to add as many before the dictionary
                should_have = 4
                missing = should_have - line.count("|")
                last_one = line.rfind("|")
                line = line[:last_one] + "|" * missing + line[last_one:]
            result = regexp.match(line)
            if not result:
                print(line)
            else:
                result = result.groupdict(default=None)
                # we always normalize the key
                lemmas[normalize_unicode(result["lemma"])] = result
    return lemmas

with open("./src/lemmes.la") as f:
    lines = normalize_unicode(f.read()).split("\n")
    lemmas = parseLemma(lines)


assert lemmas["volumen"]["geninf"] == "volumin"
assert lemmas["volumen"]["lemma"] == "volumen"
assert lemmas["volumen"]["model"] == "corpus"

with open("./collected.json", "w") as f:
    json.dump(
        {
            "pos": morphos,
            "models": norm_models,
            "lemmas": lemmas
        },
        f
    )