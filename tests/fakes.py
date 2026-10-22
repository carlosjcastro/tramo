class RoutedLLM:
    model = "fake:model"

    def __init__(self, routes: dict) -> None:
        self._routes = {schema: list(outputs) for schema, outputs in routes.items()}
        self.prompts: list[str] = []

    def ask(self, system, user, schema, check=None):
        self.prompts.append(user)
        output = self._routes[schema].pop(0)
        if isinstance(output, Exception):
            raise output
        if check:
            check(output)
        return output

    def is_ready(self) -> bool:
        return True


class FakeChatClient:
    def __init__(self, *replies) -> None:
        self._replies = list(replies)
        self.requests: list[dict] = []

    def chat(self, **request):
        self.requests.append(request)
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return type("Response", (), {"message": type("Message", (), {"content": reply})()})()

    def list(self):
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        models = [type("Item", (), {"model": name})() for name in reply]
        return type("Listing", (), {"models": models})()
