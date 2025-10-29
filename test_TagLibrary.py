import pytest

from TagLibrary import TagLibrary

def test_self_reference_error():
	lib = TagLibrary(None)
	tag = lib.create("tagggg")
	tag.canonical = tag
	
	with pytest.raises(RuntimeError):
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

def test_consequent_migration():
	lib = TagLibrary(None)
	
	ball = lib.create("ball")
	sphere = lib.create("sphere")
	
	basketball = lib.create("basketball")
	basket_ball = lib.create("basket ball")
	
	basketball.alias(basket_ball)
	basketball.imply(ball)
	lib.validate_integrity()
	
	assert basket_ball.get_canon() is basketball.get_canon()
	
	assert basketball.does_imply(ball)
	assert basket_ball.does_imply(ball)
	
	ball.alias(sphere)
	lib.validate_integrity()
	
	assert basketball.does_imply(sphere)
	assert basket_ball.does_imply(sphere)
	lib.validate_integrity()