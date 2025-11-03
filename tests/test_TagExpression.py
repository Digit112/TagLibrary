import pytest

# TagExpression, TagExpressionParsingError, TagOperator, TagUnaryOperator, TagBinaryOperator, TagConjunction, TagDisjunction, TagNegation
from TagLibrary import *
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

def test_unmatched_parentheses():
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("(uh oh")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh oh)")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("((uh oh)")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("(uh oh))")
	
	with pytest.raises(TagExpressionParsingError):
		expr = TagExpression("uh) (oh")
	
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

def test_non_operation_in_result():
	expr = TagExpression("NOT tag")
	
	assert type(expr.root) is TagNegation
	expr.root = 3
	
	lib = TagLibrary(None)
	with pytest.raises(TypeError):
		lib.tagify(expr)

#### Test get_lowest_precedence_operator ####

def test_no_operator():
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("tag")
	
	assert oper is None
	assert oper_i is None
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 3

def test_operator_ordering():
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("NOT a AND a OR a")
	
	assert oper is TagDisjunction
	assert oper_i == 12
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 16
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a OR a AND NOT a")
	
	assert oper is TagDisjunction
	assert oper_i == 2
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 16
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("NOT a AND a")
	
	assert oper is TagConjunction
	assert oper_i == 6
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 11
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a AND NOT a")
	
	assert oper is TagConjunction
	assert oper_i == 2
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 11
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("NOT a")
	
	assert oper is TagNegation
	assert oper_i == 0
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 5

def test_depth_handling():
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a AND (a AND (a AND a))")
	
	assert oper is TagConjunction
	assert oper_i == 2
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 23
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("(a AND (a AND (a AND a)))")
	
	assert oper is TagConjunction
	assert oper_i == 3
	assert sub_expr_start_i == 1
	assert sub_expr_end_i == 24
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("(((a AND (a AND (a AND a)))))")
	
	assert oper is TagConjunction
	assert oper_i == 5
	assert sub_expr_start_i == 3
	assert sub_expr_end_i == 26

def test_depth_multiple_operators():
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a AND (a OR a)")
	
	assert oper is TagConjunction
	assert oper_i == 2
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 14
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a OR (a AND a)")
	
	assert oper is TagDisjunction
	assert oper_i == 2
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 14
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a OR a AND a")
	
	assert oper is TagDisjunction
	assert oper_i == 2
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 12
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a AND a OR a")
	
	assert oper is TagDisjunction
	assert oper_i == 8
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 12
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("(a AND (a OR a))")
	
	assert oper is TagConjunction
	assert oper_i == 3
	assert sub_expr_start_i == 1
	assert sub_expr_end_i == 15
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("(a OR a AND a)")
	
	assert oper is TagDisjunction
	assert oper_i == 3
	assert sub_expr_start_i == 1
	assert sub_expr_end_i == 13
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("NOT a AND a")
	
	assert oper is TagConjunction
	assert oper_i == 6
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 11
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("NOT (a AND a)")
	
	assert oper is TagNegation
	assert oper_i == 0
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 13

def test_left_right_ordering():
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a AND a AND a")
	
	assert oper is TagConjunction
	assert oper_i == 8
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 13
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("a OR a OR a")
	
	assert oper is TagDisjunction
	assert oper_i == 7
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 11
	
	oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator("NOT NOT a")
	
	assert oper is TagNegation
	assert oper_i == 0
	assert sub_expr_start_i == 0
	assert sub_expr_end_i == 9

#### Test whole expression parsing ####

def test_single_binary_oper_parsing():
	expr = TagExpression("this AND that")
	
	assert type(expr.root) is TagConjunction
	assert expr.root.left == "this"
	assert expr.root.right == "that"
	
	expr = TagExpression("( this OR that )")
	
	assert type(expr.root) is TagDisjunction
	assert expr.root.left == "this"
	assert expr.root.right == "that"

def test_single_unary_oper_parsing():
	expr = TagExpression(" NOT this ")
	
	assert type(expr.root) is TagNegation
	assert expr.root.right == "this"

	expr = TagExpression("(NOT this)")
	
	assert type(expr.root) is TagNegation
	assert expr.root.right == "this"

def test_double_negation():
	expr = TagExpression("NOT NOT this ")
	
	assert type(expr.root) is TagNegation
	assert type(expr.root.right) is TagNegation
	assert expr.root.right.right == "this"

def test_repeated_operator():
	expr = TagExpression("this AND that AND stuff AND things")
	
	assert type(expr.root) is TagConjunction
	
	assert expr.root.right == "things"
	assert type(expr.root.left) is TagConjunction
	
	assert expr.root.left.right == "stuff"
	assert type(expr.root.left.left) is TagConjunction
	
	assert expr.root.left.left.right == "that"
	assert expr.root.left.left.left == "this"
	
	expr = TagExpression("(this AND (that AND (stuff AND things)))")
	
	assert type(expr.root) is TagConjunction
	
	assert      expr.root.left == "this"
	assert type(expr.root.right) is TagConjunction
	
	assert      expr.root.right.left == "that"
	assert type(expr.root.right.right) is TagConjunction
	
	assert      expr.root.right.right.left == "stuff"
	assert      expr.root.right.right.right == "things"

def test_unary_binary_mix():
	expr = TagExpression("this AND NOT that OR NOT (stuff AND things)")
	
	assert type(expr.root) is TagDisjunction
	
	assert type(expr.root.left) is TagConjunction
	assert      expr.root.left.left == "this"
	assert type(expr.root.left.right) is TagNegation
	assert      expr.root.left.right.right == "that"
	
	assert type(expr.root.right) is TagNegation
	assert type(expr.root.right.right) is TagConjunction
	assert      expr.root.right.right.left == "stuff"
	assert      expr.root.right.right.right == "things"