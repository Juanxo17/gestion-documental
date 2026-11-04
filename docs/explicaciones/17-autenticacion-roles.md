# Autenticación y control de acceso por roles

**Autenticación: ¿quién eres?** `POST /auth/login` recibe correo y contraseña y devuelve un
**JWT**: un texto firmado con `JWT_SECRET` que dice "soy el usuario X, válido hasta tal hora".
Viaja en cada petición; si se altera, la firma falla (401). Ver `services/servicio_auth.py`.

**Hash, no contraseña.** La BD guarda un hash bcrypt (`pwdlib`), irreversible y con sal aleatoria:
si roban la base, no obtienen las contraseñas.

**Autorización: ¿qué puedes hacer?** Cada rol tiene una lista de permisos (`roles.permisos`).
`requiere_permiso("cuentas.radicar")` responde 403 si el rol no lo tiene; PAGADA exige además
`cuentas.pagar`. Las reglas del usuario (inactivo, 5 fallos = 15 min de bloqueo, cambio
obligatorio de contraseña) están en `domain/usuarios.py`, clase `Usuario`.

**Demostración:** `uv run pytest tests/test_auth.py`. **Descartado:** sesiones en el servidor.
