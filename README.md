# TagLibrary

Uses a prefix tree to allow rapid lookup of tags by name, including their aliases and implications, and also allows saving and loading tag libraries. Utilities exist to modify these relations, which throw `TagIntegrityError` in the case that the update does not maintain the integrity of the relations. For example, if a tag is added that already exists, or a tag is made to imply itself.

## TagExpression

Includes a recursive-descent expression parser, `TagExpression`, which accepts a string in its constructor. The result will have a `root` attribute which is the root of the expression tree with strings for leaves and `TagOperator` instances for internal nodes. Throws `TagExpressionParsingError` on invalid syntax.

Pass the TagExpression to `TagLibrary.tagify()` to convert all strings to TagNode instances. Throws `TagIdentificationError` if a string turns out not to be a real tag.

### TODO:

- Deactivate / Delete operation
- Replace "next_id" with "num_tags"
- Errors for adding a 2^16th alias/implication