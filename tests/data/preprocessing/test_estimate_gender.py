from data.preprocessing.estimate_gender import (
    Gender,
    GenderGuessMethod,
    guess_gender,
    guess_gender_from_firstname,
    guess_gender_from_lastname,
    parse_name,
)


class TestParseName:
    def test_standard_czech_format(self):
        result = parse_name("Novák Jakub")
        assert result.last_name == "Novák"
        assert result.first_name == "Jakub"
        assert result.full_name == "Novák Jakub"

    def test_multiple_first_names(self):
        result = parse_name("Novák Jakub Karel")
        assert result.last_name == "Novák"
        assert result.first_name == "Jakub Karel"
        assert result.full_name == "Novák Jakub Karel"

    def test_single_name_only(self):
        result = parse_name("Novák")
        assert result.last_name == "Novák"
        assert result.first_name == ""
        assert result.full_name == "Novák"

    def test_empty_string(self):
        result = parse_name("")
        assert result.last_name == ""
        assert result.first_name == ""
        assert result.full_name == ""

    def test_extra_whitespace(self):
        result = parse_name("  Novák   Jakub  ")
        assert result.last_name == "Novák"
        assert result.first_name == "Jakub"


class TestGuessGenderFromLastname:
    def test_female_suffix_ova(self):
        result = guess_gender_from_lastname("Nováková")
        assert result == Gender.FEMALE

    def test_female_suffix_a_with_accent(self):
        result = guess_gender_from_lastname("Malá")
        assert result == Gender.FEMALE

    def test_male_surname(self):
        result = guess_gender_from_lastname("Novák")
        assert result is None

    def test_ends_with_a_no_accent(self):
        result = guess_gender_from_lastname("Borga")
        assert result is None

    def test_case_insensitivity(self):
        result = guess_gender_from_lastname("NOVÁKOVÁ")
        assert result == Gender.FEMALE

    def test_empty_string(self):
        result = guess_gender_from_lastname("")
        assert result is None


class TestGuessGenderFromFirstname:
    def test_male_name_in_list(self):
        male_names = {"jakub"}
        female_names = set()
        result = guess_gender_from_firstname("jakub", male_names, female_names)
        assert result == Gender.MALE

    def test_female_name_in_list(self):
        male_names = set()
        female_names = {"anna"}
        result = guess_gender_from_firstname("anna", male_names, female_names)
        assert result == Gender.FEMALE

    def test_name_not_in_either_list(self):
        male_names = set()
        female_names = set()
        result = guess_gender_from_firstname("xyz", male_names, female_names)
        assert result == Gender.INCONCLUSIVE

    def test_case_insensitivity(self):
        male_names = {"jakub"}
        female_names = set()
        result = guess_gender_from_firstname("JAKUB", male_names, female_names)
        assert result == Gender.MALE

    def test_name_with_extra_spaces(self):
        male_names = set()
        female_names = {"anna"}
        result = guess_gender_from_firstname("  anna  ", male_names, female_names)
        assert result == Gender.FEMALE

    def test_empty_string(self):
        male_names = {"jakub"}
        female_names = {"anna"}
        result = guess_gender_from_firstname("", male_names, female_names)
        assert result == Gender.INCONCLUSIVE

    def test_name_in_both_lists(self):
        male_names = {"andrea"}
        female_names = {"andrea"}
        result = guess_gender_from_firstname("andrea", male_names, female_names)
        assert result == Gender.INCONCLUSIVE


class TestGuessGender:
    def test_female_by_lastname_suffix(self):
        male_names = set()
        female_names = set()
        result = guess_gender("Nováková Anna", male_names, female_names)
        assert result.gender == Gender.FEMALE
        assert result.method_used == GenderGuessMethod.LASTNAME_SUFFIX
        assert result.debater_name.last_name == "Nováková"
        assert result.debater_name.first_name == "Anna"

    def test_male_by_firstname_match(self):
        male_names = {"jakub"}
        female_names = set()
        result = guess_gender("Novák Jakub", male_names, female_names)
        assert result.gender == Gender.MALE
        assert result.method_used == GenderGuessMethod.FIRSTNAME_MATCH

    def test_female_by_firstname_match(self):
        male_names = set()
        female_names = {"anna"}
        result = guess_gender("Smith Anna", male_names, female_names)
        assert result.gender == Gender.FEMALE
        assert result.method_used == GenderGuessMethod.FIRSTNAME_MATCH

    def test_inconclusive_no_matches(self):
        male_names = set()
        female_names = set()
        result = guess_gender("Smith Unknown", male_names, female_names)
        assert result.gender == Gender.INCONCLUSIVE
        assert result.method_used == GenderGuessMethod.INCONCLUSIVE

    def test_lastname_takes_precedence(self):
        male_names = {"jakub"}
        female_names = set()
        result = guess_gender("Nováková Jakub", male_names, female_names)
        assert result.gender == Gender.FEMALE
        assert result.method_used == GenderGuessMethod.LASTNAME_SUFFIX

    def test_single_name_with_female_suffix(self):
        male_names = set()
        female_names = set()
        result = guess_gender("Nováková", male_names, female_names)
        assert result.gender == Gender.FEMALE
        assert result.method_used == GenderGuessMethod.LASTNAME_SUFFIX
