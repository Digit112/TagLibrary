import pytest

from TagLibrary import TagLibrary, TagIntegrityError, TagIdentificationError
from TagExpression import *

#### Test integrity validation ####

def test_self_reference_error():
	lib = TagLibrary(None)
	tag = lib.create("tagggg")
	tag.canonical = tag
	
	with pytest.raises(RuntimeError):
		lib.validate_integrity()

def test_tag_validation():
	lib = TagLibrary(None)
	
	with pytest.raises(ValueError):
		tag = lib.create("tag,")
	lib.validate_integrity()
	
	with pytest.raises(ValueError):
		tag = lib.create("tag)")
	lib.validate_integrity()
	
	with pytest.raises(ValueError):
		tag = lib.create("tag(")
	lib.validate_integrity()
	
	with pytest.raises(ValueError):
		tag = lib.create("tag\n!")
	lib.validate_integrity()

def test_basic_integrity_errors():
	lib = TagLibrary(None)
	
	tag = lib.create("tagggg")
	
	tag.tag_id = None
	with pytest.raises(RuntimeError):
		lib.validate_integrity()
	tag.tag_id = 1
	
	tag.antecedents = None
	with pytest.raises(RuntimeError):
		lib.validate_integrity()
	tag.antecedents = []
	
	tag.implicants = None
	with pytest.raises(RuntimeError):
		lib.validate_integrity()
	tag.implicants = []
	
	tag.consequents = None
	with pytest.raises(RuntimeError):
		lib.validate_integrity()
	tag.consequents = []

def test_dupe_errors():
	lib = TagLibrary(None)
	tag1 = lib.create("tagggg")
	tag2 = lib.create("tagggggggg")
	tag3 = lib.create("tagggggggggggggg")
	
	tag1.alias(tag2)
	tag2.imply(tag3)
	
	canon = tag1.get_canon()
	lib.validate_integrity()
	
	ant = canon.antecedents
	imp = tag3.implicants
	con = tag2.consequents
	
	assert len(ant) > 0
	assert len(imp) > 0
	assert len(con) > 0
	
	with pytest.raises(RuntimeError):
		canon.antecedents += ant
		lib.validate_integrity()
	
	with pytest.raises(RuntimeError):
		tag3.implicants += imp
		lib.validate_integrity()
	
	with pytest.raises(RuntimeError):
		tag2.consequents += con
		lib.validate_integrity()

#### Test integrity violations caught ####

def test_cant_make_dupe():
	lib = TagLibrary(None)
	tag = lib.create("tagggg")
	
	with pytest.raises(TagIntegrityError):
		tag = lib.create("tagggg")
	
	lib.validate_integrity()

def test_cant_get_nothing():
	lib = TagLibrary(None)
	
	with pytest.raises(TagIdentificationError):
		tag = lib.get("huh?")
	
	lib.validate_integrity()

# Note this doesn't prevent circular implication chains...
def test_cant_imply_alias():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	sphere.alias(ball)
	lib.validate_integrity()
	
	with pytest.raises(TagIntegrityError):
		sphere.imply(ball)
	
	with pytest.raises(TagIntegrityError):
		sphere.imply(sphere)
	
	lib.validate_integrity()

#### Test functionality ####

def test_iter():
	lib = TagLibrary(None)
	
	# Add a variety of tags to test iteration
	all_tags = [
		lib.create("tag"),
		lib.create("tah"),
		lib.create("tai"),
		lib.create("tbg"),
		lib.create("tbh"),
		lib.create("tcg"),
		lib.create("sag"),
		lib.create("sah"),
		lib.create("sbg")
	]
	
	ret_tags = list(lib)
	for tag in all_tags:
		assert tag in ret_tags
	
	for tag in ret_tags:
		assert tag in all_tags

def test_add_recall():
	lib = TagLibrary(None)
	tag1 = lib.create("my tag")
	assert tag1 is not None
	
	tag2 = lib.get("my tag")
	assert tag2 is not None
	
	assert tag1 is tag2
	lib.validate_integrity()

def test_alias():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	ball.alias(sphere)
	
	assert ball.get_canon() is sphere.get_canon()
	lib.validate_integrity()

def test_multi_alias():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	spheroid = lib.create("spheroid")
	
	ball.alias(sphere)
	sphere.alias(spheroid)
	
	assert ball.get_canon() is sphere.get_canon()
	assert sphere.get_canon() is spheroid.get_canon()
	assert ball.get_canon() is spheroid.get_canon()
	lib.validate_integrity()

def test_implication_migration():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	basketball = lib.create("basketball")
	basket_ball = lib.create("basket ball")
	
	basketball.alias(basket_ball)
	basketball.imply(ball)
	lib.validate_integrity()
	
	assert basket_ball.get_canon() is basketball.get_canon()
	
	assert basketball.does_directly_imply(ball)
	assert basket_ball.does_directly_imply(ball)
	
	ball.alias(sphere)
	lib.validate_integrity()
	
	assert basketball.does_directly_imply(sphere)
	assert basket_ball.does_directly_imply(sphere)
	lib.validate_integrity()

def test_implication_migration_reversed_aliasing():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	basketball = lib.create("basketball")
	basket_ball = lib.create("basket ball")
	
	basket_ball.alias(basketball)
	basketball.imply(ball)
	lib.validate_integrity()
	
	assert basket_ball.get_canon() is basketball.get_canon()
	
	assert basketball.does_directly_imply(ball)
	assert basket_ball.does_directly_imply(ball)
	
	sphere.alias(ball)
	lib.validate_integrity()
	
	assert ball.get_canon() is sphere.get_canon()
	
	assert basketball.does_directly_imply(sphere)
	assert basket_ball.does_directly_imply(sphere)
	lib.validate_integrity()

def test_implication_migration_reversed_implication():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	basketball = lib.create("basketball")
	basket_ball = lib.create("basket ball")
	
	ball.alias(sphere)
	basketball.imply(ball)
	lib.validate_integrity()
	
	assert ball.get_canon() is sphere.get_canon()
	
	assert basketball.does_directly_imply(ball)
	assert basketball.does_directly_imply(sphere)
	
	basketball.alias(basket_ball)
	lib.validate_integrity()
	
	assert basket_ball.get_canon() is basketball.get_canon()
	
	assert basket_ball.does_directly_imply(ball)
	assert basket_ball.does_directly_imply(sphere)
	lib.validate_integrity()

def test_implication_migration_reversed_implication_reversed_aliases():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	basketball = lib.create("basketball")
	basket_ball = lib.create("basket ball")
	
	sphere.alias(ball)
	basketball.imply(ball)
	lib.validate_integrity()
	
	assert ball.get_canon() is sphere.get_canon()
	
	assert basketball.does_directly_imply(ball)
	assert basketball.does_directly_imply(sphere)
	
	basket_ball.alias(basketball)
	lib.validate_integrity()
	
	assert basket_ball.get_canon() is basketball.get_canon()
	
	assert basket_ball.does_directly_imply(ball)
	assert basket_ball.does_directly_imply(sphere)
	lib.validate_integrity()

def test_consequent_migration_no_dupes():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	basketball = lib.create("basketball")
	basket_ball = lib.create("basket ball")
	
	basketball.imply(ball)
	basket_ball.imply(sphere)
	lib.validate_integrity()
	
	assert basketball.does_directly_imply(ball)
	assert basket_ball.does_directly_imply(sphere)
	
	ball.alias(sphere)
	lib.validate_integrity()
	
	assert ball.get_canon() is sphere.get_canon()
	assert basketball.does_directly_imply(sphere)
	assert basket_ball.does_directly_imply(ball)
	
	basketball.alias(basket_ball)
	lib.validate_integrity()
	
	assert basketball.does_directly_imply(ball)
	assert basket_ball.does_directly_imply(sphere)
	assert basketball.does_directly_imply(sphere)
	assert basket_ball.does_directly_imply(ball)

#### Test tagify errors ####

def test_infinite_tagify():
	lib = TagLibrary(None)
	
	expr = TagExpression("NOT tag")
	
	assert type(expr.root) is TagNegation
	expr.root.right = expr.root # Create infinite regress.
	
	with pytest.raises(RuntimeError):
		lib.tagify(expr)

def test_unknown_tags():
	lib = TagLibrary(None)
	
	expr = TagExpression("uh AND oh")
	
	with pytest.raises(TagIdentificationError):
		lib.tagify(expr)

#### Test tagify ####

def test_tagify_single_tag():
	lib = TagLibrary(None)
	tag = lib.create("tag")
	expr = TagExpression("tag")
	
	lib.tagify(expr)
	
	assert expr.root is tag

def test_tagify():
	lib = TagLibrary(None)
	tag1 = lib.create("tag1")
	tag2 = lib.create("tag2")
	tag3 = lib.create("tag3")
	tag4 = lib.create("tag4")
	
	expr = TagExpression("tag1 AND tag2 OR tag3 AND NOT tag4")
	
	lib.tagify(expr)
	
	assert type(expr.root) is TagDisjunction
	assert type(expr.root.left) is TagConjunction
	assert type(expr.root.right) is TagConjunction
	assert type(expr.root.right.right) is TagNegation
	
	assert expr.root.left.left is tag1
	assert expr.root.left.right is tag2
	assert expr.root.right.left is tag3
	assert expr.root.right.right.right is tag4

#### Test library saving and loading ####

def test_save_simple():
	lib = TagLibrary(None)
	
	lib.create("ball")
	lib.create("ballerina")
	lib.create("basket")
	
	lib.save("test_save_simple.taglib")
	
	new_lib = TagLibrary("test_save_simple.taglib")
	
	new_lib.validate_integrity()
	TagLibrary.validate_identical(lib, new_lib)