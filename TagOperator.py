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

class TagExpression:
	def __init__(self, expr_str, start=0, end=len(expr_str)):
		self.root = None
		
		self.validate_parens(expr_str)
		
		# Find the first and last characters in the expression, past any outermost parens.
		# TODO: This will not work! Must locate first outermost operator!!
		while start < end and start < len(expr_str) and expr_str[start] in [" ", "\t", "("]
			start += 1
		while end > start and end > 0 and expr_str[end-1] in [" ", "\t", ")"]
			end -= 1
		
		if start <= end:
			raise ValueError(f"Empty expression '{expr_str[start:end]}' beginning at position {start+1}..")
		
		l_paren_i = find("(", start, end)
		l_dis_i = expr_str.find("OR", start, end)
		l_con_i = expr_str.find("AND", start, end)
		l_neg_i = expr_str.find("NOT", start, end)
		
		r_paren_i = rfind(")", start, end)
		r_dis_i = expr_str.rfind("OR", start, end)
		r_con_i = expr_str.rfind("AND", start, end)
		
		if r_dis_i != -1 and (r_dis_i > r_paren_i or r_paren_i == -1):
			self.root = TagDisjunction(
				TagExpression(expr_str, start, r_dis_i),
				TagExpression(expr_str, r_dis_i+2, end)
			)
		
		elif l_dis_i != -1 and (l_dis_i < l_paren_i or l_paren_i == -1):
			self.root = TagDisjunction(
				TagExpression(expr_str, start, l_dis_i),
				TagExpression(expr_str, l_dis_i+2, end)
			)
		
		elif r_con_i != -1 and (r_con_i > r_paren_i or r_paren_i == -1):
			self.root = TagConjunction(
				TagExpression(expr_str, start, r_con_i),
				TagExpression(expr_str, r_con_i+3, end)
			)
		
		elif l_con_i != -1 and (l_con_i < l_paren_i or l_paren_i == -1):
			self.root = TagConjunction(
				TagExpression(expr_str, start, l_con_i),
				TagExpression(expr_str, l_con_i+3, end)
			)
		
		elif l_neg_i != -1 and (l_neg_i < l_paren_i or l_paren_i == -1):
			if l_neg_i != start:
				raise ValueError(f"NOT operator at {l_neg_i+1} must not have preceeding parentheticals or tags; it is a unary operator.")
		
		else:
			raise ValueError(f"Expression '{expr_str[start:end]}' beginning at position {start+1} lacks an operand on both sides of the outermost parentheticals.")
	
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