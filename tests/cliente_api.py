from dataclasses import dataclass

from fastapi.testclient import TestClient
from httpx2 import Response

from tests.fabricas import CONTRASENA, Escenario


@dataclass
class ClienteApi:
    http: TestClient
    escenario: Escenario

    @property
    def usuarios(self):  # type: ignore[no-untyped-def]
        return self.escenario.repos.usuarios

    def login(self, correo: str, contrasena: str = CONTRASENA) -> Response:
        return self.http.post("/auth/login", data={"username": correo, "password": contrasena})

    def cabeceras(self, correo: str) -> dict[str, str]:
        respuesta = self.login(correo)
        assert respuesta.status_code == 200, respuesta.text
        return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}
