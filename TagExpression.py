from enum import Enum
import unicodedata

class TagExpressionParsingError(ValueError):
	def __init__(self, message, expr_str, start=0, end=None, error_i=-1, error_len=1):
		if end is None:
			end = len(expr_str)
		
		msg  = f"Error{f" at position {error_i}" if error_i != -1 else ""}: {message}\n"
		msg += f"In '{expr_str}'"
		
		# Print subexpression if it is not the whole expression or the whole error
		if (start > 0 or end < len(expr_str)) and (start != error_i or end - start != error_len):
			msg += f"\n{" "*start}In '{expr_str[start:end]}'"
		
		if error_i != -1:
			msg += f"\n    {" "*error_i}^{"~"*(error_len-1)}"
		
		super().__init__(msg)

class TagOperator():
	pass

class TagUnaryOperator(TagOperator):
	def __init__(self, right):
		self.right = right

class TagBinaryOperator(TagOperator):
	def __init__(self, left, right):
		self.left = left
		self.right = right

class TagConjunction(TagBinaryOperator):
	pass

class TagDisjunction(TagBinaryOperator):
	pass

class TagNegation(TagUnaryOperator):
	pass

TagNegation.priority = 2
TagConjunction.priority = 1
TagDisjunction.priority = 0

TagNegation.symbol = "NOT"
TagConjunction.symbol = "AND"
TagDisjunction.symbol = "OR"

TagOperator.operations = (TagDisjunction, TagConjunction, TagNegation)

# Operations must be sorted in order of ascending priority.
for oper_i in range(1, len(TagOperator.operations)):
	assert TagOperator.operations[oper_i].priority > TagOperator.operations[oper_i-1].priority

class TagExpression:
	def __init__(self, expr_str, start=0, end=None, depth=0):
		if end is None:
			end = len(expr_str)
		
		# One-time check for invalid characters
		if depth == 0:
			expr_has_non_whitespace = False
			for letter_i in range(len(expr_str)):
				letter = expr_str[letter_i]
				if unicodedata.category(letter) in ["Zl", "Zp", "Cc", "Cf", "Cs", "Co", "Cn"]:
					raise TagExpressionParsingError(f"Expression contains invalid control or format character U+{ord(letter):04x}.", expr_str, start, end, letter_i)
				
				if letter not in (" ", "\t"):
					expr_has_non_whitespace = True
			
			if not expr_has_non_whitespace:
				raise TagExpressionParsingError(f"Expression must not be empty.", expr_str)
		
		# Check for empty expr
		expr_has_non_whitespace = False
		for letter_i in range(start, end):
			letter = expr_str[letter_i]
			if letter not in (" ", "\t"):
				expr_has_non_whitespace = True
				break
		
		if not expr_has_non_whitespace:
			raise TagExpressionParsingError(f"Expression must not be empty. Did you forget an operand?", expr_str, start, end, start, end-start)
		
		print(f"{" "*start}'{expr_str[start:end]}'")
		self.root = None
		
		oper, oper_i, sub_expr_start_i, sub_expr_end_i = TagExpression.get_lowest_precedence_operator(expr_str, start, end)
		
		# Fancy debugging stuff
		if oper is not None:
			msg = f" {" "*sub_expr_start_i}^{" "*(oper_i - sub_expr_start_i - 1)}{"-"*(len(oper.symbol))}{" "*(sub_expr_end_i - oper_i - len(oper.symbol))}^"
			print(f"{msg}{" "*(len(expr_str) + 5 - len(msg))}({sub_expr_start_i}, {oper_i}, {sub_expr_end_i})")
		else:
			msg = f" {" "*sub_expr_start_i}^{" "*(sub_expr_end_i - sub_expr_start_i - 1)}^"
			print(f"{msg}{" "*(len(expr_str) + 5 - len(msg))}({sub_expr_start_i}, {sub_expr_end_i})")
		
		# Check that no text exists in the region occluded by the subexpression bounds.
		# This can happen if the user forgets on operator, as in:
		# some tag (other tag with long name) another weirdly long tag
		# ^ start   ^ sub_expr_start_i      ^ sub_expr_end_i          ^ end
		for i in range(start, sub_expr_start_i):
			if expr_str[i] not in (" ", "\t", "("):
				raise TagExpressionParsingError("Expected operator before parenthetical.", expr_str, start, end, sub_expr_start_i-1)
		
		for i in range(sub_expr_end_i, end):
			if expr_str[i] not in (" ", "\t", ")"):
				raise TagExpressionParsingError("Expected operator before tag or parenthetical.", expr_str, start, end, i)
		
		# No operation. Whole expression is a single tag.
		if oper is None:	
			self.root = expr_str[sub_expr_start_i:sub_expr_end_i].strip()
		
		# Operation found.
		else:
			if issubclass(oper, TagUnaryOperator):
				# Check that unary operators are not preceeded by an operand
				for i in range(sub_expr_start_i, oper_i):
					if expr_str[i] not in (" ", "\t"):
						raise TagExpressionParsingError("Expected operator before unary operator.", expr_str, start, end, oper_i)
				
				sub_expr = TagExpression(expr_str, oper_i + len(oper.symbol), sub_expr_end_i, depth+1)
				self.root = oper(sub_expr.root)
			
			elif issubclass(oper, TagBinaryOperator):
				left_expr = TagExpression(expr_str, sub_expr_start_i, oper_i, depth+1)
				right_expr = TagExpression(expr_str, oper_i + len(oper.symbol), sub_expr_end_i, depth+1)
				
				self.root = oper(left_expr.root, right_expr.root)
			
			else:
				raise RuntimeError(f"Unknown operation {oper}.")
	
	# Returns the type and position of the lowest-priority operator in the passeed string segment.
	# Also throws on mismatched parentheses.
	def get_lowest_precedence_operator(expr_str, start=0, end=None):
		if end is None:
			end = len(expr_str)
		
		# Find the last occurence of an operator in the outermost parenthetical.
		# This operator has the lowest precedence. It splits the entire expression in half.
		close_parens_i = [] # parenthetical depth tracking
		
		min_oper_depth = None
		min_oper = None
		
		# These values allow the splitting of the passed expression into two parts.
		# These parts are [sub_expr_start_i:oper_i] and [oper_i + len(min_oper.symbol):sub_expr_end_i]
		# ((some tag OR other tag) AND necessary tag)
		#  ^ sub_expr_start_i      ^ oper_i         ^ sub_expr_end_i
		sub_expr_start_i = start
		sub_expr_end_i = end
		oper_i = None
		
		# Used to determine when to set sub_expr_start_i and sub_expr_end_i
		do_set_sub_expr_bounds = False
		max_depth_visited = 0
		
		sub_expr_is_empty = True
		
		for i in range(end-1, start-1, -1):
			# Check for special chars and whitespace at this position
			if expr_str[i] == ")":
				sub_expr_is_empty = True
				close_parens_i.append(i)
				
				# If no lowest operation is found
				if min_oper is None and max_depth_visited < len(close_parens_i):
					max_depth_visited = len(close_parens_i)
					do_set_sub_expr_bounds = True
			
			elif expr_str[i] == "(":
				if sub_expr_is_empty:
					raise TagExpressionParsingError("Empty expression.", expr_str, start, end, i, close_parens_i[-1] - i + 1)
				
				if len(close_parens_i) == 0:
					raise TagExpressionParsingError("Unmatched open parenthesis.", expr_str, start, end, i)
				
				# If we are now exiting the parenthetical containing the lowest-precedence operator (so far), record its start and end.
				if do_set_sub_expr_bounds:
					sub_expr_start_i = i + 1
					sub_expr_end_i = close_parens_i[-1]
					do_set_sub_expr_bounds = False
				
				close_parens_i.pop()
			
			elif expr_str[i] in (" ", "\n"):
				continue
			
			# Check for operators at this position
			else:
				sub_expr_is_empty = False
			
				if min_oper_depth is None or len(close_parens_i) < min_oper_depth:
					# Depth is lower than depth of lowest known operator; accept ANY operation at this depth as the new lowest
					for oper in TagOperator.operations:
						if expr_str.startswith(oper.symbol, i):
							min_oper_depth = len(close_parens_i)
							min_oper = oper
							oper_i = i
							
							do_set_sub_expr_bounds = True
				
				elif len(close_parens_i) == min_oper_depth:
					# Depth is the same as lowest known operator; accept an operator of lower precedence as the new lowest.
					for oper in TagOperator.operations:
						# Don't check for operations of higher precedence than the known lowest.
						if oper.priority >= min_oper.priority:
							break
						
						if expr_str.startswith(oper.symbol, i):
							min_oper = oper
							oper_i = i
							
							do_set_sub_expr_bounds = True
		
		if len(close_parens_i) > 0:
			raise TagExpressionParsingError("Unmatched close parenthesis.", expr_str, start, end, close_parens_i[-1])
		
		if do_set_sub_expr_bounds:
			sub_expr_start_i = start
			sub_expr_end_i = end
		
		assert sub_expr_start_i < sub_expr_end_i
		assert (min_oper is None) == (oper_i is None)
		
		return min_oper, oper_i, sub_expr_start_i, sub_expr_end_i