import pytest

# TagExpression, TagExpressionParsingError, TagOperator, TagUnaryOperator, TagBinaryOperator, TagConjunction, TagDisjunction, TagNegation
from TagExpression import *

#### Test appropriate error is raised ####

def test_empty_expr():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("")
		
def test_whitespace_expr():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression(" ")

def test_invalid_characters():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("\nuh oh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh\noh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh oh\n")

def test_missing_operator_before_parenthetical():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh (oh)")

def test_missing_operator_after_parenthetical():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("(uh) oh")

def test_missing_operator_between_parenthetical():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("(uh) (oh)")

def test_empty_parenthetical():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh OR ( )")

def test_missing_operator_before_unary():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh NOT oh")

def test_missing_operand_before_operator():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("AND uh oh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("    AND uh oh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("() AND uh oh")

def test_missing_operand_after_operator():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh oh AND")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh oh AND    ")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh oh AND ()")

def test_missing_operand_betwee_operator():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh ANDAND oh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh AND AND oh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh AND () AND oh")

#### Test get_lowest_precedence_operator ####

#### Test whole expression parsing ####

def test_single_oper_parsing():
	expr = TagExpression("this AND that")
	
	assert type(expr.root) is TagConjunction
	assert expr.root.left == "this"
	assert expr.root.right == "that"