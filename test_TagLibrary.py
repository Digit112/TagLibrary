import pytest

from TagLibrary import TagLibrary

def test_self_reference_error():
	lib = TagLibrary(None)
	tag = lib.create("tagggg")
	tag.canonical = tag
	
	with pytest.raises(RuntimeError):
		lib.validate_integrity()

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

# Note this doesn't prevent circular implication chains...
def test_cannot_imply_self():
	pass # TODO

def test_cannot_imply_alias():
	pass # TODO