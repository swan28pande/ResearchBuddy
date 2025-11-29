class AgenticStress:
    def __init__(self, app: FastAPI):
        self.app = app
        self.registry = []
        self._discover_endpoints()

    def _discover_endpoints(self):
        for route in self.app.routes:
            if hasattr(route, "methods"):
                meta = {
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                    "endpoint": route.endpoint.__name__,
                    "params": self._extract_params(route)
                }
                self.registry.append(meta)

    def _extract_params(self, route):
        sig = inspect.signature(route.endpoint)
        params = {}
        for name, param in sig.parameters.items():
            params[name] = str(param.annotation)
        return params

    def list_endpoints(self):
        return self.registry
