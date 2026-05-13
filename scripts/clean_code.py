import ast, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(ROOT_DIR)


def clean_python_code(source_code):
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return source_code

    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node = self.generic_visit(node)
            if ast.get_docstring(node):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Str, ast.Constant))
                ):
                    node.body = node.body[1:]
            return node

        def visit_ClassDef(self, node):
            node = self.generic_visit(node)
            if ast.get_docstring(node):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Str, ast.Constant))
                ):
                    node.body = node.body[1:]
            return node

        def visit_Module(self, node):
            node = self.generic_visit(node)
            if ast.get_docstring(node):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Str, ast.Constant))
                ):
                    node.body = node.body[1:]
            return node

    remover = DocstringRemover()
    new_tree = remover.visit(tree)
    fixed_code = ast.unparse(new_tree)
    lines = fixed_code.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped == "":
            continue
        result.append(line)
    return "\n".join(result)


def run_cleanup(root_dir="."):
    ignore_folders = {".venv", ".git", "__pycache__", "node_modules"}
    total_cleaned = 0
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        for file in files:
            if file.endswith(".py") and file != "clean_code.py":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    cleaned = clean_python_code(content)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(cleaned)
                    print(f"Cleaned: {file_path}")
                    total_cleaned += 1
                except Exception as e:
                    print(f"Error cleaning {file_path}: {e}")
    print(f"Total files cleaned: {total_cleaned}")


if __name__ == "__main__":
    run_cleanup()
