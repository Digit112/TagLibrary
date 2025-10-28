class TagIntegrityError(RuntimeError):
	pass

class TagLibrary:
	def __init__(self, fn):
		self.root = TagNode()
		self.next_id = 1
		
		with open(fn, r):
			pass
	
	# Create a new tag.
	# Errors if the tag already exists.
	def create(self, tag):
		current_node = self.root
		cursor_i = 0
		
		while cursor_i < len(tag):
			codepoint = ord(tag[cursor_i])
			if codepoint not in current_node.children:
				current_node.children[codepoint] = TagNode()
			
			current_node = current_node.children[codepoint]

		if current_node.tag_id is not None:
			raise RuntimeError(f"Tag '{tag}' already exists.")
		
		current_node.tag_id = self.next_id
		self.next_id += 1
		
		return current_node
	
	# Returns the node for the requested tag if it exists, or None if it doesn't
	def has(self, tag):
		current_node = self.root
		cursor_i = 0
		
		while cursor_i < len(tag):
			codepoint = ord(tag[cursor_i])
			if codepoint not in current_node.children:
				return None
			
			current_node = current_node.children[codepoint]

		if current_node.tag_id is None:
			return None
		
		current_node.tag_id = self.next_id
		self.next_id += 1
		
		return current_node
	
	# Returns the node for the requested tag.
	# Throws if the tag does not exist.
	def get(self, tag):
		res = self.has(tag)
		if res is None:
			raise RuntimeError(f"No such tag '{tag}'.")
		
		return res

class TagNode:
	def __init__(self):
		self.tag_id = None
		
		# All aliased tags have a single canonical form.
		# If this tag is the canonical form of its alias group, self.canonical is none.
		self.canonical = None # Canonical form of this tag and all aliases
		self.antecedents = None # Tags for which this tag is the canonoical form.
		
		# Implications must not be set on non-canonical tags.
		self.consequents = None # Tags implied by this tag.
		self.implicants = None # Tags which imply this tag.
		
		# Tags for which this tag is a prefix
		self.children = {}
	
	# Returns the canonical representation of this tag.
	# Either self, or self's canonical. If a chain of aliases is found, throws a TagIntegrityError.
	def get_canon(self):
		pass
	
	# Sets a canonical representation of this tag to be the passed node.
	# If the passed node itself has a canonical representation, that will become the actual representation.
	# The canonical representation will be 
	def alias(canon_tag):
		canon_tag = canon_tag.get_canon()
	
	# Throws if basic assumptions about the values and types of this structure do not hold true.
	def assert_internal_integrity(self):
		if self.tag_id is None:
			if self.canonical is not None:
				raise TagIntegrityError(f"Non-tag, aka intermidiary value cannot have a canonical form.")
			
			if self.antecedents is not None:
				raise TagIntegrityError(f"Non-tag, aka intermidiary value cannot have antecedents.")

			if self.consequents is not None:
				raise TagIntegrityError(f"Non-tag, aka intermidiary value cannot have consequents.")
			
			if self.implicants is not None:
				raise TagIntegrityError(f"Non-tag, aka intermidiary value cannot have implicants.")
		
		else:
			# Validate tag id
			if type(self.tag_id) is not int:
				raise TagIntegrityError(f"Tag has tag_id of type '{type(self.tag_id)}', must be int or None.")
			
			if self.tag_id == 0:
				raise TagIntegrityError(f"Tag has invalid tag_id of 0.")
			
			# Validate canonical form
			if self.canonical is not None:
				if type(self.canonical) is not TagNode:
					raise TagIntegrityError(f"Tag {self.tag_id} has a canonical form of type {type(self.canonical)}, must be TagNode.")
				
				if len(self.antecedents) != 0:
					raise TagIntegrityError(f"Tag {self.tag_id} has both antecedents and a canonical form.")
			
			# Check type of arrays
			if type(self.antecedents) is not list:
				raise TagIntegrityError(f"Tag {self.tag_id} has antecedents of type {type(self.antecedents)}, must be list of TagNodes.")
				
			if type(self.consequents) is not list:
				raise TagIntegrityError(f"Tag {self.tag_id} has consequents of type {type(self.consequents)}, must be list of TagNodes.")
				
			if type(self.implicants) is not list:
				raise TagIntegrityError(f"Tag {self.tag_id} has implicants of type {type(self.implicants)}, must be list of TagNodes.")
		
			# Check members of arrays.
			for antecedent in self.antecedents:
				if type(antecedent) is not TagNode:
					raise TagIntegrityError(f"Tag {self.tag_id} has antecedent of type {type(antecedent)}, must be list of TagNodes.")
			
			for consequent in self.consequents:
				if type(consequent) is not TagNode:
					raise TagIntegrityError(f"Tag {self.tag_id} has consequent of type {type(consequent)}, must be list of TagNodes.")
			
			for implicant in self.implicants:
				if type(implicant) is not TagNode:
					raise TagIntegrityError(f"Tag {self.tag_id} has implicant of type {type(implicant)}, must be list of TagNodes.")
	
	# Throws under various conditions where the canon of this tag is invalid.
	# Includes the presence of alias chains and incorrectly canonized consequents (implication relations pointing to a non-canoonical form)
	def assert_referential_integrity(self):
		# Check canonical / alias integrity
		if self.canonical is not None:
			if self.canonical.canonical is not None:
				raise TagIntegrityError(f"Alias chain {self.tag_id} -> {self.canonical.tag_id} -> {self.canonical.tag_id}")
			
			if self not in self.canonical.antecedents:
				raise TagIntegrityError(f"Tag {self.tag_id} is not in the antecedents of its canonical form.")
	
			if len(self.consequents) != 0:
				raise TagIntegrityError(f"Tag {self.tag_id} must not have any consequents since it is not a canonical form.")
				
		# Check members of arrays.
		for antecedent in self.antecedents:
			if antecedent.canonical != self:
				raise TagIntegrityError(f"Tag {self.tag_id} has antecedent {antecedent.tag_id} whose canonical form is {antecedent.canonoical.tag_id} instead of self.")
		
		for consequent in self.consequents:
			if consequent.implicants is None:
				raise TagIntegrityError(f"Tag {self.tag_id} has consequent {consequent.tag_id} with no implicants.")
			
			if self not in consequent.implicants:
				raise TagIntegrityError(f"Tag {self.tag_id} has consequent {consequent.tag_id} for which self is not an implicant.")
		
		for implicant in self.implicants:
			if implicant.consequents is None:
				raise TagIntegrityError(f"Tag {self.tag_id} has implicant {implicant.tag_id} with no consequents.")
			
			if self not in implicant.consequents:
				raise TagIntegrityError(f"Tag {self.tag_id} has implicant {consequent.tag_id} for which self is not a consequent.")
			
			


