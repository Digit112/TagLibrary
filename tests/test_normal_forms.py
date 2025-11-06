import pytest

from ..TagExpression import *

#### Negation Normal Form ####

def test_NNF_validation():
	expr = TagExpression("NOT this")
	expr.root.validate_is_negation_normal()
	
	expr = TagExpression("this AND that OR some other third thing")
	expr.root.validate_is_negation_normal()
	
	expr = TagExpression("NOT this AND NOT that OR NOT stuff")
	expr.root.validate_is_negation_normal()
	
	with pytest.raises(TagExpressionValidationError):
		expr = TagExpression("NOT NOT this")
		expr.root.validate_is_negation_normal()
	
	with pytest.raises(TagExpressionValidationError):
		expr = TagExpression("NOT (this AND that)")
		expr.root.validate_is_negation_normal()
	
	with pytest.raises(TagExpressionValidationError):
		expr = TagExpression("NOT (this OR that)")
		expr.root.validate_is_negation_normal()

def test_NNF_negation_collapsing():
	expr = TagExpression("this")
	expr.to_negation_normal_form()
	
	assert expr.root == "this"
	
	expr = TagExpression("NOT this")
	expr.to_negation_normal_form()
	expr.root.validate_is_negation_normal()
	
	assert type(expr.root) is TagNegation
	assert      expr.root.right == "this"
	
	expr = TagExpression("NOT NOT this")
	expr.to_negation_normal_form()
	
	assert expr.root == "this"
	
	expr = TagExpression("NOT NOT NOT this")
	expr.to_negation_normal_form()
	expr.root.validate_is_negation_normal()
	
	assert type(expr.root) is TagNegation
	assert      expr.root.right == "this"
	
	expr = TagExpression("NOT NOT NOT NOT this")
	expr.to_negation_normal_form()
	
	assert expr.root == "this"

def test_NNF_propogation():
	expr = TagExpression("NOT (this AND that)")
	expr.to_negation_normal_form()
	expr.root.validate_is_negation_normal()
	
	assert type(expr.root) is TagDisjunction
	assert type(expr.root.left) is TagNegation
	assert type(expr.root.right) is TagNegation
	assert      expr.root.left.right == "this"
	assert      expr.root.right.right == "that"
	
	expr = TagExpression("NOT (this AND (that OR things))")
	expr.to_negation_normal_form()
	expr.root.validate_is_negation_normal()
	
	assert type(expr.root) is TagDisjunction
	assert type(expr.root.left) is TagNegation
	assert      expr.root.left.right == "this"
	assert type(expr.root.right) is TagConjunction
	assert type(expr.root.right.left) is TagNegation
	assert type(expr.root.right.right) is TagNegation
	assert      expr.root.right.left.right == "that"
	assert      expr.root.right.right.right == "things"