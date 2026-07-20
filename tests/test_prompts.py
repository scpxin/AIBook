from novel_creator.prompts import _fix_truncated_json, format_prompt, parse_json_response


class TestFormatPrompt:
    def test_simple_substitution(self):
        result = format_prompt("Hello {name}", name="World")
        assert result == "Hello World"

    def test_missing_key_becomes_empty(self):
        result = format_prompt("Hello {name}{suffix}", name="World")
        assert result == "Hello World"

    def test_empty_template(self):
        result = format_prompt("", name="test")
        assert result == ""

    def test_escaped_braces_in_template(self):
        result = format_prompt("literal {{not_a_field}}", name="ignored")
        assert result == "literal {not_a_field}"


class TestParseJsonResponse:
    def test_plain_json(self):
        result = parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_markdown_block(self):
        text = """Here is the result:
```json
{"name": "test", "count": 42}
```
Done."""
        result = parse_json_response(text)
        assert result == {"name": "test", "count": 42}

    def test_json_with_code_block_no_lang(self):
        text = '```\n{"a": 1}\n```'
        result = parse_json_response(text)
        assert result == {"a": 1}

    def test_json_array(self):
        result = parse_json_response("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_json_with_prefix_text(self):
        result = parse_json_response('prefix text {"key": true}')
        assert result == {"key": True}

    def test_empty_input(self):
        result = parse_json_response("")
        assert result is None

    def test_none_input(self):
        result = parse_json_response(None)
        assert result is None


class TestFixTruncatedJson:
    def test_unclosed_object(self):
        result = _fix_truncated_json('{"key": "val"')
        assert result == {"key": "val"}

    def test_unclosed_array(self):
        result = _fix_truncated_json('[1, 2')
        assert result == [1, 2]

    def test_unclosed_string_and_object(self):
        result = _fix_truncated_json('{"k": "val')
        assert result == {"k": "val"}

    def test_complete_json_unchanged(self):
        result = _fix_truncated_json('{"a": 1, "b": 2}')
        assert result == {"a": 1, "b": 2}


class TestImportBackwardCompat:
    def test_templates_importable_from_prompts(self):
        from novel_creator.prompts import CHAPTER_POLISH, WORLD_BUILDING
        assert len(WORLD_BUILDING) > 0
        assert len(CHAPTER_POLISH) > 0

    def test_parse_json_response_importable(self):
        from novel_creator import parse_json_response
        assert callable(parse_json_response)
