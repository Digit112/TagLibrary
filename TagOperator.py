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
	def __init__(self, expr_str):
		self.root = None