No FastAPI (seguindo a convenção padrão da documentação e do OAuth2), a forma mais limpa e recomendada de passar os escopos no dicionário de usuários é utilizando uma **lista de strings**.

Cada string dentro da lista representa uma permissão ou escopo específico que aquele usuário possui.

Aqui está como o seu dicionário deve ficar estruturado:

```python
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "scopes": ["me", "items:read"],  # Usuário comum
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    },
    "uallasleles": {
        "username": "uallasleles",
        "full_name": "Uallas Leles",
        "email": "uallasleles@hotmail.com",
        "scopes": ["me", "items:read", "items:write"],  # Usuário com mais permissões
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$rHkjAbvDYYo8cwuYw047og$+ifGhU0bcDixhZSH+op8crfsW4FlrLYwlzVxOLiNUXs",
        "disabled": False,
    },
    "controll": {
        "username": "controll",
        "full_name": "controll",
        "email": "walissonsk8@hotmail.com",
        "scopes": ["me", "admin"],  # Usuário administrador
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$pt5tQNbRrBvU6QDag1s0TQ$n/9QQjxC32o7Wqi8MnPjBsrXAcbHq/GC6im0x0o59QE",
        "disabled": False,
    }
}

```

---

### 💡 Por que usar uma lista?

1. **Facilidade na Verificação:** Quando você validar o token JWT e extrair o usuário do banco, poderá verificar as permissões diretamente usando a palavra-chave `in` do Python.
2. **Compatibilidade com Pydantic:** No seu modelo Pydantic (ex: `UserInDB`), você pode definir o campo como `scopes: list[str] = []`, garantindo uma tipagem forte e segura.

> **Dica extra:** Lembre-se de que, ao gerar o token JWT (no endpoint de login), esses escopos geralmente são injetados no payload do token para evitar que você precise consultar o banco de dados a cada requisição apenas para checar as permissões do usuário.