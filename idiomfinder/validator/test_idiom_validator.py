from pytest import fixture

from idiomfinder.validator import IdiomValidator


@fixture
def idiom_validator():
    return IdiomValidator()


def test_empty_str_should_return_false(idiom_validator):
    assert not idiom_validator.is_valid(None)
    assert not idiom_validator.is_valid('')


def test_non_idiom_should_return_false(idiom_validator):
    assert not idiom_validator.is_valid("blah")
    assert not idiom_validator.is_valid("不是成语")


def test_idioms_should_return_true(idiom_validator):
    assert idiom_validator.is_valid("一心一意")
    assert idiom_validator.is_valid("南辕北辙")
    assert idiom_validator.is_valid("指鹿为马")
