from data.preprocessing.categorize_motions import (
    Category,
    Motion,
    calculate_category_score,
    categorize_motion,
    normalize_motion,
    normalize_text,
)


class TestNormalizeText:
    def test_czech_diacritics(self):
        result = normalize_text("ěščřžýáíéúůňťď")
        assert result == "escrzyaieuuntd"

    def test_uppercase_text(self):
        result = normalize_text("HELLO WORLD")
        assert result == "hello world"

    def test_mixed_case_text(self):
        result = normalize_text("HeLLo WoRLd")
        assert result == "hello world"

    def test_multiple_diacritics_same_word(self):
        result = normalize_text("příliš")
        assert result == "prilis"

    def test_empty_string(self):
        result = normalize_text("")
        assert result == ""

    def test_text_with_punctuation(self):
        result = normalize_text("Hello, world!")
        assert result == "hello, world!"

    def test_text_with_numbers(self):
        result = normalize_text("Test123")
        assert result == "test123"


class TestNormalizeMotion:
    def test_standard_motion_text(self):
        result = normalize_motion("We should legalize all drugs")
        assert result.text == "We should legalize all drugs"
        assert result.normalized_words == ["we", "should", "legalize", "all", "drugs"]

    def test_motion_with_czech_diacritics(self):
        result = normalize_motion("Měli bychom zvýšit daně")
        assert result.text == "Měli bychom zvýšit daně"
        assert result.normalized_words == ["meli", "bychom", "zvysit", "dane"]

    def test_motion_with_extra_whitespace(self):
        result = normalize_motion("We  should   legalize")
        assert result.normalized_words == ["we", "should", "legalize"]

    def test_motion_with_leading_trailing_whitespace(self):
        result = normalize_motion("  We should legalize  ")
        assert result.normalized_words == ["we", "should", "legalize"]

    def test_single_word_motion(self):
        result = normalize_motion("Taxation")
        assert result.normalized_words == ["taxation"]

    def test_empty_string_motion(self):
        result = normalize_motion("")
        assert result.normalized_words == []

    def test_motion_with_punctuation(self):
        result = normalize_motion("Should we legalize drugs?")
        assert result.normalized_words == ["should", "we", "legalize", "drugs"]


class TestCalculateCategoryScore:
    def test_single_keyword_match(self):
        motion = Motion(
            text="We should increase taxes",
            normalized_words=["we", "should", "increase", "taxes"],
        )
        category = Category(name="Economics", keywords={"taxes", "economy"})

        result = calculate_category_score(motion, category)

        assert result.score == 1
        assert result.category == category

    def test_multiple_keyword_matches(self):
        motion = Motion(
            text="We should increase taxes for economy",
            normalized_words=["we", "should", "increase", "taxes", "for", "economy"],
        )
        category = Category(name="Economics", keywords={"taxes", "economy", "market"})

        result = calculate_category_score(motion, category)

        assert result.score == 2

    def test_no_keyword_matches(self):
        motion = Motion(
            text="We should protect environment",
            normalized_words=["we", "should", "protect", "environment"],
        )
        category = Category(name="Economics", keywords={"taxes", "economy"})

        result = calculate_category_score(motion, category)

        assert result.score == 0

    def test_duplicate_keyword_in_motion(self):
        motion = Motion(
            text="taxes taxes taxes", normalized_words=["taxes", "taxes", "taxes"]
        )
        category = Category(name="Economics", keywords={"taxes"})

        result = calculate_category_score(motion, category)

        assert result.score == 1

    def test_partial_word_no_match(self):
        motion = Motion(
            text="taxation is important",
            normalized_words=["taxation", "is", "important"],
        )
        category = Category(name="Economics", keywords={"tax"})

        result = calculate_category_score(motion, category)

        assert result.score == 0

    def test_case_insensitive_matching(self):
        motion = Motion(
            text="TAXES are high", normalized_words=["taxes", "are", "high"]
        )
        category = Category(name="Economics", keywords={"taxes"})

        result = calculate_category_score(motion, category)

        assert result.score == 1

    def test_diacritic_insensitive_matching(self):
        motion = Motion(
            text="Daně jsou vysoké", normalized_words=["dane", "jsou", "vysoke"]
        )
        category = Category(name="Economics", keywords={"dane"})

        result = calculate_category_score(motion, category)

        assert result.score == 1


class TestCategorizeMotion:
    def test_single_category_strong_match(self):
        motion_text = "We should increase taxes for the economy"
        categories = [
            Category(name="Economics", keywords={"taxes", "economy", "market"}),
            Category(name="Law", keywords={"court", "justice"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.motion_text == motion_text
        assert result.top_category_1 is not None
        assert result.top_category_1.category.name == "Economics"
        assert result.top_category_1.score == 2
        assert result.top_category_2 is None
        assert result.top_category_3 is None

    def test_multiple_categories_matching(self):
        motion_text = "We should reform courts and taxes"
        categories = [
            Category(name="Economics", keywords={"taxes", "economy"}),
            Category(name="Law", keywords={"courts", "justice"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is not None
        assert result.top_category_2 is not None
        assert result.top_category_1.score == 1
        assert result.top_category_2.score == 1

    def test_three_plus_categories(self):
        motion_text = "We should reform courts, increase taxes, protect environment and improve education"
        categories = [
            Category(name="Economics", keywords={"taxes"}),
            Category(name="Law", keywords={"courts"}),
            Category(name="Environment", keywords={"environment"}),
            Category(name="Education", keywords={"education"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is not None
        assert result.top_category_2 is not None
        assert result.top_category_3 is not None
        # All 4 categories match, but only top 3 are returned

    def test_fewer_than_three_categories(self):
        motion_text = "We should increase taxes"
        categories = [
            Category(name="Economics", keywords={"taxes"}),
            Category(name="Law", keywords={"court"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is not None
        assert result.top_category_1.category.name == "Economics"
        assert result.top_category_2 is None
        assert result.top_category_3 is None

    def test_no_categories_match(self):
        motion_text = "We should do something"
        categories = [
            Category(name="Economics", keywords={"taxes", "economy"}),
            Category(name="Law", keywords={"court", "justice"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is None
        assert result.top_category_2 is None
        assert result.top_category_3 is None

    def test_exactly_one_category(self):
        motion_text = "We should increase taxes"
        categories = [
            Category(name="Economics", keywords={"taxes"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is not None
        assert result.top_category_1.category.name == "Economics"
        assert result.top_category_2 is None
        assert result.top_category_3 is None

    def test_exactly_two_categories(self):
        motion_text = "We should increase taxes and reform courts"
        categories = [
            Category(name="Economics", keywords={"taxes"}),
            Category(name="Law", keywords={"courts"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is not None
        assert result.top_category_2 is not None
        assert result.top_category_3 is None

    def test_dominant_category_with_weak_matches(self):
        motion_text = "We should reform taxes, economy, market and maybe courts"
        categories = [
            Category(name="Economics", keywords={"taxes", "economy", "market"}),
            Category(name="Law", keywords={"courts"}),
        ]

        result = categorize_motion(motion_text, categories)
        print("Dominant category with weak matches:")
        print(result)

        assert result.top_category_1 is not None
        assert result.top_category_1.category.name == "Economics"
        assert result.top_category_1.score == 3
        assert result.top_category_2 is not None
        assert result.top_category_2.category.name == "Law"
        assert result.top_category_2.score == 1

    def test_empty_motion_text(self):
        motion_text = ""
        categories = [
            Category(name="Economics", keywords={"taxes"}),
        ]

        result = categorize_motion(motion_text, categories)

        assert result.top_category_1 is None
        assert result.top_category_2 is None
        assert result.top_category_3 is None
