class TagIntegrityError(RuntimeError):
	def __init__(self, message, /, *args, **kwargs):
		super().__init__(message, *args, **kwargs)
		
		self.message = message

class TagLibrary:
	def __init__(self, fn):
		self.root = TagNode()
		self.next_id = 1
		
		if fn is None:
			return
		
		else:
			with open(fn, "r"):
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
			cursor_i += 1
			
		if current_node.tag_id is not None:
			raise RuntimeError(f"Tag '{tag}' already exists.")
		
		current_node.tag_id = self.next_id
		current_node.antecedents = []
		current_node.implicants = []
		current_node.consequents = []
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
			cursor_i += 1

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
	
	# Checks all the types and inter-relationships between all the tags!
	# A slow function used only for testing.
	def validate_integrity(self):
		self.root.cascade_validate_integrity()

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
		if self.canonical is not None:
			return self.canonical
		
		else:
			return self
	
	# Ensures that this token and the passed token have the same canonical form.
	# Errors if they both already have separate canonical forms.
	def alias(self, other):
		if self.tag_id is None or other.tag_id is None:
			raise TagIntegrityError("Cannot alias node without tag_id.")
		
		print(f"Alias {self.tag_id} -> {other.tag_id}")
		
		if self.canonical is None and len(self.antecedents) == 0:
			self.canonical = other.get_canon()
			other.antecedents.append(self)
			self.canonize_implications()
		
		elif other.canonical is None and len(other.antecedents) == 0:
			other.canonical = self.get_canon()
			self.antecedents.append(other)
			other.canonize_implications()
		
		else:
			raise TagIntegrityError(f"Can not alias tags '{self.tag_id}' and '{other.tag_id}' which belong to separate alias groups.")
	
	# Sets self to imply the passed tag.
	# Returns true on success, false if the implication relation already exists.
	def imply(self, other):
		self_canon = self.get_canon()
		other_canon = other.get_canon()
		print(f"Imply {self.tag_id} (= {self_canon.tag_id}) -> {other.tag_id} (= {other_canon.tag_id})")
		
		if not self_canon.does_directly_imply(other_canon):
			self_canon.consequents.append(other_canon)
			other_canon.implicants.append(self_canon)
			return True
		
		else:
			return False
	
	# Returns true of this tag directly implies the passed tag.
	def does_directly_imply(self, other):
		return other.get_canon() in self.get_canon().consequents
	
	# Move all consequents and implicants to the canonical representation of this tag.
	# Always called while aliasing two tags together.
	def canonize_implications(self):
		print(f"Canonizing implications of {self.tag_id}")
		
		for implicant in self.implicants:
			print(f"  implicant {implicant.tag_id}...")
			implicant.consequents.remove(self)
			
			if self.canonical not in implicant.consequents:
				implicant.consequents.append(self.canonical)
				self.canonical.implicants.append(implicant)
		
		self.implicants = []
		
		for consequent in self.consequents:
			print(f"  consequent {consequent.tag_id}...")
			consequent.implicants.remove(self)
			
			if self.canonical not in consequent.implicants:
				consequent.implicants.append(self.canonical)
				self.canonical.consequents.append(consequent)
		
		self.consequents = []
	
	def cascade_validate_integrity(self, curr_tag=""):
		self.validate_internal_integrity()
		
		for key in self.children:
			try:
				self.children[key].cascade_validate_integrity(curr_tag + chr(key))
		
			except TagIntegrityError as e:
				raise RuntimeError(f"While validating '{curr_tag + chr(key)}': {e.message}")
		
		self.validate_referential_integrity()
	
	def __repr__(self):
		if self.tag_id is None:
			return "<Empty TagNode>"
		
		else:
			return f"<Tag ID {self.tag_id}; canonical ID {self.get_canon().tag_id}; {len(self.antecedents)} antecedents; {len(self.implicants)} implicants; {len(self.consequents)} consequents>"
	
	# Throws if basic assumptions about the values and types of this structure do not hold true.
	def validate_internal_integrity(self):
		# Check children
		if type(self.children) is not dict:
			raise TagIntegrityError(f"Children must be dict, not {type(self.children)}.")
			
			for key in self.children:
				if type(key) is not int:
					raise TagIntegrityError(f"Keys into children must be ints (unicode codepoints), not {type(key)}.")
				
				if type(self.children[key]) is not TagNode:
					raise TagIntegrityError(f"Keys into children must be ints (unicode codepoints), not {type(self.children[key])}.")
			
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
	def validate_referential_integrity(self):
		if self.tag_id is not None:
			# Check canonical / alias integrity
			if self.canonical is not None:
				if self.canonical.canonical is not None:
					raise TagIntegrityError(f"Alias chain {self.tag_id} -> {self.canonical.tag_id} -> {self.canonical.tag_id}")
				
				if self not in self.canonical.antecedents:
					raise TagIntegrityError(f"Tag {self.tag_id} is not in the antecedents of its canonical form.")
		
				if len(self.antecedents) != 0:
					raise TagIntegrityError(f"Tag {self.tag_id} must not have any antecedents since it is not in canonical form.")
		
				if len(self.consequents) != 0:
					raise TagIntegrityError(f"Tag {self.tag_id} must not have any consequents since it is not in canonical form.")
		
				if len(self.implicants) != 0:
					raise TagIntegrityError(f"Tag {self.tag_id} must not have any implicants since it is not in canonical form.")
			
			else:
				# Check members of arrays.
				for antecedent in self.antecedents:
					if antecedent.canonical != self:
						raise TagIntegrityError(f"Tag {self.tag_id} has antecedent {antecedent.tag_id} whose canonical form is {antecedent.canonoical.tag_id} instead of self.")
				
				for consequent in self.consequents:
					if consequent.implicants is None:
						raise TagIntegrityError(f"Tag {self.tag_id} has consequent {consequent.tag_id} with no implicants.")
					
					if self not in consequent.implicants:
						raise TagIntegrityError(f"Tag {self.tag_id} has consequent {consequent.tag_id} for which it is not an implicant.")
				
				for implicant in self.implicants:
					if implicant.consequents is None:
						raise TagIntegrityError(f"Tag {self.tag_id} has implicant {implicant.tag_id} with no consequents.")
					
					if self not in implicant.consequents:
						raise TagIntegrityError(f"Tag {self.tag_id} has implicant {consequent.tag_id} for which it is not a consequent.")
			
				# Check for duplicate entries
				for i in range(len(self.antecedents)-1):
					for j in range(i+1, len(self.antecedents)):
						if self.antecedents[i] == self.antecedents[j]:
							raise TagIntegrityError(f"Tag {self.tag_id} has duplicate antecedent {self.antecedents[i].tag_id}.")
				
				for i in range(len(self.consequents)-1):
					for j in range(i+1, len(self.consequents)):
						if self.consequents[i] == self.consequents[j]:
							raise TagIntegrityError(f"Tag {self.tag_id} has duplicate consequent {self.consequents[i].tag_id}.")
				
				for i in range(len(self.implicants)-1):
					for j in range(i+1, len(self.implicants)):
						if self.implicants[i] == self.implicants[j]:
							raise TagIntegrityError(f"Tag {self.tag_id} has duplicate implicant {self.implicants[i].tag_id}.")


