"""The Toolbox's own tree, on Nodes built by hand."""

from __future__ import annotations

import pytest

from sql_composer.trees import Node, combined, has_aggregate, plain_name


def column(name: str, table: str = "t") -> Node:
    return Node("Column", name=name, table=table)


def number(text: str) -> Node:
    return Node("Literal", this=text, is_string=False)


def test_a_node_has_only_the_kinds_and_parts_it_knows() -> None:
    with pytest.raises(ValueError, match="no kind of Node called 'Update'"):
        Node("Update")
    with pytest.raises(ValueError, match="a EQ has no part 'low'"):
        Node("EQ", this=column("a"), low=number("1"))
    with pytest.raises(ValueError, match="a Column has no part 'this'"):
        column("a").set("this", "b")
    with pytest.raises(ValueError, match="no kind of Node called 'Colum'"):
        list(column("a").find_all("Colum"))
    with pytest.raises(ValueError, match="'upper' isn't one of the date functions"):
        Node("Call", name="upper", args=[column("a")])


def test_equal_nodes_have_the_same_kind_and_parts_whatever_their_notes() -> None:
    first = Node("EQ", this=column("a"), expression=number("1"))
    second = Node("EQ", this=column("a"), expression=number("1"))
    second.meta["call"] = "equals(t.a, 1)"
    assert first == second
    assert first != Node("EQ", this=column("a"), expression=number("2"))
    assert first != Node("NEQ", this=column("a"), expression=number("1"))
    assert Node("Literal", this="A", is_string=True) != Node("Literal", this="a", is_string=True)
    # A part holding nothing counts as left out, as sqlglot compares its trees.
    assert Node("Ordered", this=column("a"), desc=False) == Node("Ordered", this=column("a"))


def test_a_node_is_true_and_cant_be_a_dict_key() -> None:
    node = column("a")
    assert node
    with pytest.raises(TypeError):
        hash(node)


def test_a_copy_can_be_changed_on_its_own() -> None:
    tree = Node("In", this=column("a"), expressions=[number("1")])
    tree.meta["call"] = "is_in(t.a, [1])"
    copied = tree.copy()
    assert copied == tree and copied.meta == tree.meta
    copied.parts["expressions"].append(number("2"))
    copied.parts["this"].set("name", "b")
    copied.meta["call"] = "changed"
    assert tree == Node("In", this=column("a"), expressions=[number("1")])
    assert tree.meta["call"] == "is_in(t.a, [1])"


def test_walk_goes_level_by_level_in_the_order_of_the_parts() -> None:
    # (t.a + t.b) * t.c: t.c is one level up, so it comes before t.a and t.b.
    tree = Node("Mul", this=Node("Paren", this=Node("Add", this=column("a"),
                                                         expression=column("b"))),
                expression=column("c"))
    assert [c.name for c in tree.find_all("Column")] == ["c", "a", "b"]
    assert [node.kind for node in tree.walk()] == ["Mul", "Paren", "Column", "Add", "Column",
                                                    "Column"]


def test_and_and_or_join_left_to_right_with_brackets_around_those_inside() -> None:
    a, b, c = (Node("EQ", this=column(n), expression=number("1")) for n in "abc")
    either = combined("Or", [a.copy(), b.copy()])
    assert either == Node("Or", this=a, expression=b)
    joined = combined("And", [either, c.copy()])
    assert joined == Node("And", this=Node("Paren", this=either), expression=c)
    assert combined("And", [a.copy()]) == a
    three = combined("And", [a.copy(), b.copy(), c.copy()])
    assert three == Node("And", this=Node("And", this=a, expression=b), expression=c)


def test_flatten_gives_what_an_and_joins_with_brackets_taken_off() -> None:
    a, b, c = (Node("EQ", this=column(n), expression=number("1")) for n in "abc")
    either = combined("Or", [a.copy(), b.copy()])
    assert list(combined("And", [a.copy(), either, c.copy()]).flatten()) == [a, either, c]
    # An AND in brackets, as all_of(...) inside another all_of(...), comes back whole.
    both = combined("And", [a.copy(), b.copy()])
    assert list(combined("And", [both, c.copy()]).flatten()) == [both, c]


def test_a_tree_adds_up_rows_with_an_aggregate_outside_any_window() -> None:
    total = Node("Sum", this=column("a"))
    assert has_aggregate(Node("Div", this=total, expression=number("2")))
    assert not has_aggregate(Node("Div", this=column("a"), expression=number("2")))
    window = Node("Window", this=Node("RowNumber"), partition_by=[total.copy()],
                  order=Node("Order", expressions=[]))
    assert not has_aggregate(window)
    counted = Node("HiveFunction", name="collect_set", args=[column("a")], aggregate=True)
    assert has_aggregate(counted)
    wrapped = Node("HiveFunction", name="round", args=[total.copy()], aggregate=False)
    assert has_aggregate(wrapped)


def test_replaced_swaps_the_nodes_below_the_top_without_looking_inside() -> None:
    inner = Node("Sum", this=column("a"))
    inner.meta["call"] = "sum_of(t.a)"
    tree = Node("Div", this=inner, expression=number("2"))
    tree.meta["call"] = "top"
    seen = []

    def stand_in(node):
        seen.append(node.kind)
        return Node("Var", this=node.meta["call"]) if "call" in node.meta else None

    shown = tree.replaced(stand_in)
    assert shown == Node("Div", this=Node("Var", this="sum_of(t.a)"), expression=number("2"))
    assert seen == ["Sum", "Literal"]
    assert tree.parts["this"] is inner


def test_a_column_has_its_name_and_its_tables() -> None:
    assert (column("a").name, column("a").table) == ("a", "t")
    assert Node("Column", name="runs").table == ""


@pytest.mark.parametrize(("name", "plain"), [
    ("status", True), ("run_id", True), ("order", False), ("Order", False), ("my col", False),
    ("1st", False), ("_x", True),
])
def test_a_name_is_plain_unless_it_is_reserved_or_not_a_word(name: str, plain: bool) -> None:
    assert plain_name(name) is plain
