import ast
import inspect

import databases.veekun


def test_table_order() -> None:
    module_source = inspect.getsource(databases.veekun)
    module_ast = ast.parse(module_source)

    classes = []
    for cls in module_ast.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        if tblname := next(
            (
                i.value.value  # type: ignore[attr-defined]
                for i in cls.body
                if isinstance(i, ast.Assign)
                and i.targets[0].id == "__tablename__"  # type: ignore[attr-defined]
            ),
            None,
        ):
            if tblname == "latest_commit":
                continue
            classes.append(tblname)

    assert classes == sorted(
        classes
    ), "Classes are not sorted alphabetically in databases/veekun.py"
