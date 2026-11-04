class ErrorDominio(ValueError):
    pass


class TransicionInvalidaError(ErrorDominio):
    pass


class AccesoDenegadoError(ErrorDominio):
    pass


class UsuarioInactivoError(AccesoDenegadoError):
    pass


class UsuarioBloqueadoError(AccesoDenegadoError):
    pass
