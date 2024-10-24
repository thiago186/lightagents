import os

SRC_PATH = "light_agents"  # O caminho onde está seu código
API_PATH = "docs/api"  # O caminho onde deseja gerar a documentação

for root, dirs, files in os.walk(SRC_PATH):
    for file in files:
        if file.endswith(".py") and file != "__init__.py":
            # Gerar o caminho relativo do módulo
            module_path = os.path.relpath(os.path.join(root, file), SRC_PATH)
            module_path = module_path.replace(os.sep, ".")[:-3]  # Substituir '/' por '.' e remover '.py'

            # Gerar o conteúdo do arquivo markdown
            markdown_content = f"::: {module_path}\n"

            # Criar o caminho para o arquivo de documentação
            doc_dir = os.path.join(API_PATH, os.path.relpath(root, SRC_PATH))
            os.makedirs(doc_dir, exist_ok=True)
            doc_file = os.path.join(doc_dir, f"{file[:-3]}.md")  # Trocar a extensão para .md

            # Escrever o arquivo markdown
            with open(doc_file, "w") as f:
                f.write(markdown_content)

print("Documentação gerada automaticamente.")
