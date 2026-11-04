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


class NoEncontradoError(Exception):
    pass


class ArchivoInvalidoError(ErrorDominio):
    pass


class ArchivoDemasiadoGrandeError(ArchivoInvalidoError):
    pass
