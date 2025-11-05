# Tag Management

Tag Management is a library for processing tag relationships and queries in an efficient manner.

## TagLibrary

Uses a prefix tree to allow rapid lookup of tags by name, including their aliases and implications, and also allows saving and loading tag libraries. Utilities exist to modify these relations, which throw `TagIntegrityError` in the case that the update does not maintain the integrity of the relations. For example, if a tag is added that already exists, or a tag is made to imply itself.

## TagExpression

Includes a recursive-descent expression parser, `TagExpression`, which accepts a string in its constructor. The result will have a `root` attribute which is the root of the expression tree with strings for leaves and `TagOperator` instances for internal nodes. Throws `TagExpressionParsingError` on invalid syntax.

Pass the TagExpression to `TagLibrary.tagify()` to convert all strings to `TagNode` instances. Throws `TagIdentificationError` if a string turns out not to be a real tag.

## TagLibrary Methods

### `create(name)`

Create and return a TagNode with the given name.

### `get(name)`

Retrieve an return a TagNode by its associated name. Throws if the passed tag does not exist.

### `has(name)`

Retrieve and return a TagNode by its associated name. Returns None if it does not exist.

## TagNode Methods

### `alias(other)`

Aliases one tag to the other. The passed tag's canonical representation becomes the canonical representation of the calling tag and all its aliases.

In effect, merges the two alias groups into a single group by de-canonizing the calling tag's canonical form.

### `canonize()`

Make this tag the canonical representation of itself and all its aliases.

### `imply(other)`

Make the passed tag an implicant of the calling tag.

## TODO:

- Deactivate / Delete operation
- Add IF and IFF implication operators. Rember to update logic for convversion to CNF, which simply reduces these operations before reducing to NNF.
- Replace "next_id" with "num_tags"
- Errors for adding a 2^16th alias/implication
- GetAllImplications
