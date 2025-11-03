import io
import unicodedata

from .TagExpression import *

class TagIntegrityError(RuntimeError):
	def __init__(self, message, /, *args, **kwargs):
		super().__init__(message, *args, **kwargs)
		
		self.message = message

class TagIdentificationError(ValueError):
	pass

class TagLibrary:
	def __init__(self, fn):
		self.root = TagNode()
		self.next_id = 1
		
		if fn is None:
			return
		
		else:
			self.load(fn)
	
	# Returns a lowercase, unicode-normalized version of the string.
	# Throws on invalid tags such as those containing the comma, parentheses, control, or non-printing characters.
	def validate_and_normalize(self, tag):
		tag = unicodedata.normalize("NFKC", tag.strip().lower())
		
		for letter in tag:
			if unicodedata.category(letter) in ["Zl", "Zp", "Cc", "Cf", "Cs", "Co", "Cn"]:
				raise ValueError("Tag name must not include control or formatting unicode characters.")
			
			if letter == ',':
				raise ValueError("Tag name must not include the comma.")
			
			if letter in ['(', ')']:
				raise ValueError("Tag name must not include parentheses.")
		
		return tag
	
	# Create a new tag.
	# Errors if the tag already exists.
	def create(self, tag):
		if self.next_id == 2**32:
			raise RuntimeError("Tag limit exceeded!")
		
		#print(f"Creating {self.next_id}: {tag}.")
		tag = self.validate_and_normalize(tag)
		
		current_node = self.root
		cursor_i = 0
		
		while cursor_i < len(tag):
			codepoint = ord(tag[cursor_i])
			if codepoint not in current_node.children:
				current_node.children[codepoint] = TagNode()
			
			current_node = current_node.children[codepoint]
			cursor_i += 1
			
		if current_node.tag_id is not None:
			raise TagIntegrityError(f"Tag '{tag}' already exists.")
		
		current_node.tag_id = self.next_id
		current_node.antecedents = []
		current_node.implicants = []
		current_node.consequents = []
		self.next_id += 1
		
		return current_node
	
	# Returns the node for the requested tag if it exists, or None if it doesn't
	def has(self, tag):
		tag = self.validate_and_normalize(tag)
		
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
		
		return current_node
	
	# Returns the node for the requested tag.
	# Throws if the tag does not exist.
	def get(self, tag):
		res = self.has(tag)
		if res is None:
			raise TagIdentificationError(f"No such tag '{tag}'.")
		
		return res
	
	# Takes a TagExpression and converts all the leaf nodes into TagNode instances.
	# Throws TagIdentificationError if one of those tags does not exist.
	def tagify(self, tag_expr):
		if type(tag_expr.root) is str:
			tag_expr.root = self.get(tag_expr.root)
			return
		
		opers_stack = [tag_expr.root]
		num_iters = 0
		while len(opers_stack) > 0:
			num_iters += 1
			if num_iters >= 10000: # Infinite iteration is possible if a TagOperation is (somehow) its own descendant.
				raise RuntimeError(f"Max TagExpression complexity ({num_iters} operations) exceeded. Infinite loop?")
			
			oper = opers_stack.pop()
			print(f"On {oper}...")
			
			if isinstance(oper, TagUnaryOperator):
				if type(oper.right) is str:
					oper.right = self.get(oper.right)
				
				else:
					opers_stack.append(oper.right)
			
			elif isinstance(oper, TagBinaryOperator):
				if type(oper.right) is str:
					oper.right = self.get(oper.right)
				
				else:
					opers_stack.append(oper.right)
				
				if type(oper.left) is str:
					oper.left = self.get(oper.left)
				
				else:
					opers_stack.append(oper.left)
				
			else:
				raise TypeError(f"No such operation '{oper}'.")
	
	# Saves this library at the passed filename
	def save(self, fn, fmt="TAGLIB"):
		if fmt not in ["CSV", "TAGLIB"]:
			raise RuntimeError(f"Unknown TagLibrary format '{fmt}', must be one of 'CSV', 'TAGLIB'.")
			
		with open(fn, "wb") as fout:
			if fmt == "TAGLIB":
				fout.write(self.next_id.to_bytes(4))
			
			elif fmt == "CSV":
				raise NotImplementedError()
			
			self.root.save(fout)
	
	def load(self, fn_or_fin, fmt="TAGLIB"):
		# Call slef with context manager.
		if type(fn_or_fin) is str:
			with open(fn_or_fin, "rb") as fin:
				return self.load(fin, fmt)
		
		if fmt not in ["CSV", "TAGLIB"]:
			raise RuntimeError(f"Unknown TagLibrary format '{fmt}', must be one of 'CSV', 'TAGLIB'.")
		
		if type(fn_or_fin) is not io.BufferedReader:
			raise TypeError("load() must receive an open file or filename as a string.")
		
		fin = fn_or_fin
		
		if fmt == "TAGLIB":
			self.next_id = int.from_bytes(fin.read(4))
			self.root = TagNode(fin)
		
		elif fmt == "CSV":
			raise NotImplementedError()
		
		# Convert all integer relations to TagNodes
		all_tags = [None] * self.next_id
		for tag in self:
			all_tags[tag.tag_id] = tag
		
		for tag in self:
			if tag.canonical is not None:
				tag.canonical = all_tags[tag.canonical]
			
			for antecedent_i in range(len(tag.antecedents)):
				tag.antecedents[antecedent_i] = all_tags[tag.antecedents[antecedent_i]]
			
			for implicant_i in range(len(tag.implicants)):
				tag.implicants[implicant_i] = all_tags[tag.implicants[implicant_i]]
			
			for consequent_i in range(len(tag.consequents)):
				tag.consequents[consequent_i] = all_tags[tag.consequents[consequent_i]]
	
	def __iter__(self):
		yield from self.root
	
	# Checks all the types and inter-relationships between all the tags!
	# A slow function used only for testing.
	def validate_integrity(self):
		self.root.cascade_validate_integrity()
	
	# Used during testing to validate save/load functionality.
	# Throws if passed two libraries which aren't the same.
	def validate_identical(a, b):
		if type(a) is not TagLibrary:
			raise RuntimeError(f"are_identical accepts only libraries, not {type(a)}.")
		if type(b) is not TagLibrary:
			raise RuntimeError(f"are_identical accepts only libraries, not {type(b)}.")
		
		if a.next_id != b.next_id:
			raise RuntimeError(f"next_id does not match. ({a.next_id} == {b.next_id})")
		
		TagNode.validate_identical(a.root, b.root)

class TagNode:
	def __init__(self, fin=None):
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
		
		if fin is not None:
			self.load(fin)
	
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
		
		if self_canon is other_canon:
			raise TagIntegrityError(f"Tag {self.tag_id} cannot imply {other.tag_id}, its alias!")
		
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
	
	# Saves to the passed file
	def save(self, fout):
		if self.tag_id is None:
			fout.write(False.to_bytes())
		
		else:
			fout.write(True.to_bytes())
			fout.write(self.tag_id.to_bytes(4))
			
			# Store relations
			if self.canonical is not None:
				fout.write(self.canonical.tag_id.to_bytes(4))
			else:
				fout.write((0).to_bytes(4))
			
			fout.write(len(self.antecedents).to_bytes(2))
			for antecedent in self.antecedents:
				fout.write(antecedent.tag_id.to_bytes(4))
			
			fout.write(len(self.implicants).to_bytes(2))
			for implicant in self.implicants:
				fout.write(implicant.tag_id.to_bytes(4))
			
			fout.write(len(self.consequents).to_bytes(2))
			for consequent in self.consequents:
				fout.write(consequent.tag_id.to_bytes(4))
			
		fout.write(len(self.children).to_bytes(4))
		for key in self.children:
			fout.write(chr(key).encode('utf-8'))
			self.children[key].save(fout)
	
	def load(self, fin, depth=0):
		if self.tag_id is not None:
			raise RuntimeError("Cannot load an initialized tag!")
		
		has_tag_id = bool.from_bytes(fin.read(1))
		
		if has_tag_id:
			self.tag_id = int.from_bytes(fin.read(4))
			
			# Read relations
			self.canonical = int.from_bytes(fin.read(4))
			if self.canonical == 0:
				self.canonical = None
			
			self.antecedents = []
			num_antecedents = int.from_bytes(fin.read(2))
			for antecedent_i in range(num_antecedents):
				self.antecedents.append(int.from_bytes(fin.read(4)))
			
			self.implicants = []
			num_implicants = int.from_bytes(fin.read(2))
			for implicant_i in range(num_implicants):
				self.implicants.append(int.from_bytes(fin.read(4)))
			
			self.consequents = []
			num_consequents = int.from_bytes(fin.read(2))
			for consequent_i in range(num_consequents):
				self.consequents.append(int.from_bytes(fin.read(4)))
		
		else:
			self.tag_id = None
			
			self.canonical = None
			self.antecedents = None
			self.implicants = None
			self.consequents = None
		
		# Read children.
		num_children = int.from_bytes(fin.read(4))
		for child_i in range(num_children):
			unicode_bytes = b''
			key = None
			for i in range(4):
				unicode_bytes += fin.read(1)
				
				try:
					key = ord(unicode_bytes.decode("utf-8"))
					break
				
				except UnicodeDecodeError:
					pass
			
			if key is None:
				raise UnicodeDecodeError("Failed to read codepoint.")
			
			self.children[key] = TagNode(fin)
		
	def __iter__(self):
		if self.tag_id is not None:
			yield self
		
		for child in self.children.values():
			yield from child
	
	def __repr__(self):
		if self.tag_id is None:
			return "<Empty TagNode>"
		
		else:
			return f"<Tag ID {self.tag_id}; canonical ID {self.get_canon().tag_id}; {len(self.antecedents)} antecedents; {len(self.implicants)} implicants; {len(self.consequents)} consequents>"

	# Used during testing to validate save/load functionality.
	def validate_identical(a, b, curr_tag=""):
		if type(a) is not TagNode:
			raise RuntimeError(f"are_identical accepts only nodes, not {type(a)}.")
		if type(b) is not TagNode:
			raise RuntimeError(f"are_identical accepts only nodes, not {type(b)}.")
		
		if a.tag_id != b.tag_id:
			raise RuntimeError(f"While checking {curr_tag}, tag_ids do not match. ({a.tag_id} == {b.tag_id})")
		
		if a.tag_id is not None:
			if (a.canonical is None) != (b.canonical is None) or (a.canonical is not None and a.canonical.tag_id != b.canonical.tag_id):
				raise RuntimeError(f"While checking {curr_tag}, canonical forms do not match. ({a.canonical} == {b.canonica})")
			
			# A kind of array equality check which does not mandate a specific order.
			# Check antecedents...
			for a_val in a.antecedents:
				found_equ = False
				for b_val in b.antecedents:
					if a_val.tag_id == b_val.tag_id:
						found_equ = True
						break
				
				if not found_equ:
					raise RuntimeError(f"While checking {curr_tag}, right antecedents lack {a_val}, present in left antecedents.")
				
			for b_val in b.antecedents:
				found_equ = False
				for a_val in a.antecedents:
					if b_val.tag_id == a_val.tag_id:
						found_equ = True
						break
				
				if not found_equ:
					raise RuntimeError(f"While checking {curr_tag}, left antecedents lack {b_val}, present in right antecedents.")
					
			# Check implicants...
			for a_val in a.implicants:
				found_equ = False
				for b_val in b.implicants:
					if a_val.tag_id == b_val.tag_id:
						found_equ = True
						break
				
				if not found_equ:
					raise RuntimeError(f"While checking {curr_tag}, right implicants lack {a_val}, present in left implicants.")
				
			for b_val in b.implicants:
				found_equ = False
				for a_val in a.implicants:
					if b_val.tag_id == a_val.tag_id:
						found_equ = True
						break
				
				if not found_equ:
					raise RuntimeError(f"While checking {curr_tag}, left implicants lack {b_val}, present in right implicants.")
					
			# Check consequents...
			for a_val in a.consequents:
				found_equ = False
				for b_val in b.consequents:
					if a_val.tag_id == b_val.tag_id:
						found_equ = True
						break
				
				if not found_equ:
					raise RuntimeError(f"While checking {curr_tag}, right consequents lack {a_val}, present in left consequents.")
				
			for b_val in b.consequents:
				found_equ = False
				for a_val in a.consequents:
					if b_val.tag_id == a_val.tag_id:
						found_equ = True
						break
				
				if not found_equ:
					raise RuntimeError(f"While checking {curr_tag}, left consequents lack {b_val}, present in right consequents.")
		
		# Check children
		for key in b.children:
			if key not in a.children:
				raise RuntimeError(f"While checking {curr_tag}, left children lacks key {key}, present in right children.")
		
		for key in a.children:
			if key not in b.children:
				raise RuntimeError(f"While checking {curr_tag}, right children lacks key {key}, present in left children.")
			
			# Recurse
			TagNode.validate_identical(a.children[key], b.children[key], curr_tag + chr(key))
	
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
