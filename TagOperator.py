from enum import Enum

class TagOperator():
	pass

class TagConjunction(TagOperator):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class TagDisjunction(TagOperator):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class TagNegation(TagOperator):
	def __init__(self, right):
		self.right = right

TagNegation.priority = 0
TagConjunction.priority = 1
TagDisjunction.priority = 2

TagNegation.symbol = "NOT"
TagConjunction.symbol = "AND"
TagDisjunction.symbol = "OR"

TagOperator.operations = (TagDisjunction, TagConjunction, TagNegation)

class TagExpression:
	def __init__(self, expr_str, start=0, end=len(expr_str)):
		self.root = None
		
		self.validate_parens(expr_str)
		
		# Find the last oocurence of an operand in the outermost parenthetical.
		# This operator has the lowwest precedence. It splits the entire expression in half.
		close_parens_i = []
		min_depth = None
		min_type = None
		oper_i = 0
		
		tag_start = None
		tag_end = None
		
		for i in range(end-1, start-1, -1):
			if expr_str[i] == ")":
				close_parens_i.append(i)
			
			elif expr_str[i] == "(":
				if len(close_parens_i) == 0:
					raise ValueError(f"Unmatched open parenthesis at position {i+1} in '{expr_str[start:end]}'."
				
				close_parens_i.pop()
			
			# Record the beginning and end of the non-special characters.
			# If there are no operators, then this string is a single tagname.
			elif expr_str[i] not in (" ", "\t"):
				if tag_end is None:
					tag_end = i+i
				
				tag_start = i
			
			# Consider looking at operators
			if min_depth is None or len(close_parens_i) <= min_depth:
				# For every operator, check if it is present at i.
				for oper in TagOperator.operations:
					# Check if remaining operators have priority higher than the lowest yet found at this depth.
					if min_type is not None and len(close_parens_i) == min_depth and min_type.priority < oper.priority:
						# All remaining operators have priorities too high to be worth chec
						break
					
					if expr_str.startswith("OR", i):
						min_depth = len(close_parens_i)
						min_type = TagDisjunction
						oper_i = i
		
		
		# elif l_neg_i != -1 and (l_neg_i < l_paren_i or l_paren_i == -1):
			# if l_neg_i != start:
				# raise ValueError(f"NOT operator at {l_neg_i+1} must not have preceeding parentheticals or tags; it is a unary operator.")
	
	def validate_parens(self, expr_str, start=0, end=len(expr_str)):
		paren_indexes = []
		for letter_i in range(start, end):
			letter = expr_str[letter_i]
			
			if letter == "(":
				paren_indexes.append(letter_i)
			
			elif letter == ")":
				if len(paren_indexes) == 0:
					raise ValueError(f"Unmatched close parenthesis at position {letter_i+1} in '{expr_str[start:end]}'."
				
				paren_indexes.pop()
		
		if len(paren_indexes) > 0:
			raise ValueError(f"Unmatched close parenthesis at position {paren_indexes[-1]+1} in '{expr_str[start:end]}'."