from dataclasses import dataclass

from fastapi.testclient import TestClient
from httpx2 import Response

from gestion_documental.repositories.memoria import RepositorioUsuariosEnMemoria
from tests.fabricas import CONTRASENA


@dataclass
class ClienteApi:
    http: TestClient
    usuarios: RepositorioUsuariosEnMemoria

    def login(self, correo: str, contrasena: str = CONTRASENA) -> Response:
        return self.http.post("/auth/login", data={"username": correo, "password": contrasena})

    def cabeceras(self, correo: str) -> dict[str, str]:
        respuesta = self.http.post("/auth/login", data={"username": correo, "password": CONTRASENA})
        assert respuesta.status_code == 200, respuesta.text
        return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}
