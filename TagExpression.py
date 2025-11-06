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

class TagExpressionValidationError(ValueError):
	def __init__(self, message, offending_tag):
		super().__init__(message)
		
		self.offending_tag = offending_tag

class TagOperator():
	class Associativity(Enum):
		LEFT_TO_RIGHT = 1
		RIGHT_TO_LEFT  = 2
	
	# The below operations can be tricky. They will augment themselves and return self if they can, but they may very well return a fresh object instead.
	
	# Returns an equivalent (possibl;y self, modified)  of this operator expressed only in terms of TagConjunction, TagDisjunction, and TagNegation
	def as_reduced(self):
		raise NotImplementedError("Deriving classes must override as_reduced()")
	
	# Returns an equivalent (possibly self, modified) of this expression in negation normal form.
	# Assumes the tag is already reduced!
	def as_negation_normal(self):
		raise NotImplementedError("Deriving classes must override as_negation_normal()")
	
	# Returns an equivalent (possibl;y self, modified) of this expression in conjunctive normal form.
	# Assumes the tag is already in negation normal form!
	def as_conjunctive_normal(self):
		raise NotImplementedError("Deriving classes must override as_conjunctive_normal()")

class TagUnaryOperator(TagOperator):
	def __init__(self, right):
		self.right = right
	
	def validate_is_negation_normal():
		raise TagExpressionValidationError("Unreduced unary operator.", self)

class TagBinaryOperator(TagOperator):
	def __init__(self, left, right):
		self.left = left
		self.right = right
	
	def validate_is_negation_normal():
		raise TagExpressionValidationError("Unreduced binary operator.", self)

class TagConjunction(TagBinaryOperator):
	symbol = "AND"
	priority = 1
	associativity = TagOperator.Associativity.LEFT_TO_RIGHT
	
	def as_reduced(self):
		if type(self.left) is TagOperator:
			self.left = self.left.as_reduced()
			
		if type(self.right) is TagOperator:
			self.right = self.right.as_reduced()
		
		return self
	
	def as_negation_normal(self):
		if type(self.left) is TagOperator:
			self.left = self.left.as_negation_normal()
			
		if type(self.right) is TagOperator:
			self.right = self.right.as_negation_normal()
		
		return self
	
	def as_conjunctive_normal(self):
		if type(self.left) is TagOperator:
			self.left = self.left.as_conjunctive_normal()
			
		if type(self.right) is TagOperator:
			self.right = self.right.as_conjunctive_normal()
		
		return self
	
	def validate_is_negation_normal():
		if type(self.right) is TagOperator:
			self.right.validate_is_negation_normal()

		if type(self.left) is TagOperator:
			self.left.validate_is_negation_normal()

class TagDisjunction(TagBinaryOperator):
	symbol = "OR"
	priority = 0
	associativity = TagOperator.Associativity.LEFT_TO_RIGHT
	
	def as_reduced(self):
		if type(self.left) is TagOperator:
			self.left = self.left.as_reduced()
			
		if type(self.right) is TagOperator:
			self.right = self.right.as_reduced()
		
		return self
	
	def as_negation_normal(self):
		if type(self.left) is TagOperator:
			self.left = self.left.as_negation_normal()
			
		if type(self.right) is TagOperator:
			self.right = self.right.as_negation_normal()
		
		return self
	
	def as_conjunctive_normal(self):
		if type(self.right) is TagOperator:
			if type(self.right) is not TagConjunction:
				self.right = self.right.as_conjunctive_normal()
			
			# Critical: This "if" cannot be changed to "else" because the prior operation may have converted the child to a TagConjunction
			if type(self.right) is TagConjunction:
				return TagConjunction(
					TagDisjunction(self.left, self.right.left).as_conjunctive_normal(),
					TagDisjunction(self.left, self.right.right).as_conjunctive_normal()
				)
		
		if type(self.left) is TagOperator:
			if type(self.left) is not TagConjunction:
				self.left = self.left.as_conjunctive_normal()
			
			# Critical: This "if" cannot be changed to "else" because the prior operation may have converted the child to a TagConjunction
			if type(self.left) is TagConjunction:
				return TagConjunction(
					TagDisjunction(self.left.left, self.right).as_conjunctive_normal(),
					TagDisjunction(self.left.right, self.right).as_conjunctive_normal()
				)
		
		return self
	
	def validate_is_negation_normal():
		if type(self.right) is TagOperator:
			self.right.validate_is_negation_normal()

		if type(self.left) is TagOperator:
			self.left.validate_is_negation_normal()

class TagNegation(TagUnaryOperator):
	symbol = "NOT"
	priority = 2
	associativity = TagOperator.Associativity.RIGHT_TO_LEFT
	
	def as_reduced(self):
		if type(self.right) is TagOperator:
			self.right = self.right.as_reduced()
		
		return self
	
	def as_negation_normal(self):
		if type(self.right) is TagNegation:
			if type(self.right.right) is TagOperator:
				return self.right.right.as_negation_normal()
			
			else:
				return self.right.right
		
		if type(self.right) is TagConjunction:
			return TagDisjunction(
				TagNegation(self.right.left).as_negation_normal(),
				TagNegation(self.right.right).as_negation_normal()
			)
		
		if type(self.right) is TagDisjunction:
			return TagConjunction(
				TagNegation(self.right.left).as_negation_normal(),
				TagNegation(self.right.right).as_negation_normal()
			)
		
		if isinstance(self.right, TagOperator):
			raise RuntimeError(f"Must never call as_negation_normal on un-reduced expression containing {type(self.right)}")
		
		return self
		
	def as_conjunctive_normal(self):
		if type(self.right) is TagOperator:
			raise RuntimeError("Must never call as_conjunctive_normal on expression not in negation normal form.")
		
		return self
	
	def validate_is_negation_normal():
		if type(self.right) is TagOperator:
			raise TagExpressionValidationError("Not in NNF", self.right)

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
	
	# Convert one-way and two-way implication into negation, conjunction, and disjunction operators.
	def reduce_implications(self):
		pass # Implement after adding IF and IFF operators.
	
	# Convert into negative normal form, applying DeMorgan's laws to ensure all TagNegation operations apply only to primitives.
	# Reduces any implication operations.
	def negation_normal_form(self):
		self.reduce_implications()
		
		opers_stack = [self]
		while len(opers_stack) > 0:
			oper = opers_stack.pop()
			
			# Distribute negation over conjunction/disjunction and eliminate any double negatives.
			if isinstance(oper, TagUnaryOperator):
				raise RuntimeError("Should never run on TagNegation. Any other unary operators should have been reduced prior to calling this function.")
			
			elif isinstance(oper, TagBinaryOperator):
				if isinstance(oper.right, TagNegation):
					if isinstance(oper.right.right, TagNegation):
						oper.right = oper.right.right.right
						opers_stack.append(oper)
					
					elif isinstance(oper.right.right, TagConjunction):
						oper.right = TagDisjunction(TagNegation(oper.right.right.left), TagNegation(oper.right.right.right))
						opers_stack.append(oper.right)
					
					elif isinstance(oper.right.right, TagDisjunction):
						oper.right = TagConjunction(TagNegation(oper.right.right.left), TagNegation(oper.right.right.right))
						opers_stack.append(oper.right)
				
				elif isinstance(oper.right, TagOperator):
					opers_stack.append(oper.right)
				
				if isinstance(oper.left, TagNegation):
					if isinstance(oper.left.right, TagNegation):
						oper.left = oper.left.right.right
						opers_stack.append(oper)
					
					elif isinstance(oper.left.right, TagConjunction):
						oper.left = TagDisjunction(TagNegation(oper.left.right.left), TagNegation(oper.left.right.right))
						opers_stack.append(oper.left)
					
					elif isinstance(oper.left.right, TagDisjunction):
						oper.left = TagConjunction(TagNegation(oper.left.right.left), TagNegation(oper.left.right.right))
						opers_stack.append(oper.left)
				
				elif isinstance(oper.left, TagOperator):
					opers_stack.append(oper.left)
				
			else:
				raise RuntimeError()
	
	def conjunctive_normal_form():
		self.negation_normal_form()
		
		opers_stack = [self]
		while len(opers_stack) > 0:
			oper = opers_stack.pop()
			
			# Distribute disjunction over conjunction
			if isinstance(oper, TagUnaryOperator):
				raise RuntimeError("Should never run on TagNegation. Any other unary operators should have been reduced prior to calling this function.")
			
			elif isinstance(oper, TagBinaryOperator):
				# Right-distribute
				if isinstance(oper.right, TagDisjunction):
					if isinstance(oper.right.right, TagConjunction):
						oper.right = TagConjunction(TagDisjunction(oper.right.left, oper.right.right.left), TagDisjunction(oper.right.left, oper.right.right.right))
						opers_stack.append(oper.right)
				
				elif isinstance(oper.right, TagConjunction):
					opers_stack.append(oper.right)
				
				else:
					raise RuntimeError(f"Unreduced TagOperator {oper.right}")
			
				# Left-distribute
				if isinstance(oper.left, TagDisjunction):
					if isinstance(oper.left.right, TagConjunction):
						oper.left = TagConjunction(TagDisjunction(oper.left.right.left, oper.left.left), TagDisjunction(oper.left.right.right, oper.left.left))
						opers_stack.append(oper.left)
				
				elif isinstance(oper.left, TagConjunction):
					opers_stack.append(oper.left)
				
				else:
					raise RuntimeError(f"Unreduced TagOperator {oper.right}")
			
			
	
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
						if oper.priority > min_oper.priority:
							break
						
						# If the operations has the same priority (and depth) as the current known lowest,
						# accept it IF it has right-to-left evaluation.
						if oper.priority == min_oper.priority and oper.associativity == TagOperator.Associativity.LEFT_TO_RIGHT:
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