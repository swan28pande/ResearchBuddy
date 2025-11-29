import threading
import asyncio
import httpx
import time
import random

class Chainsaw:
    def __init__(self, app=None, base_url="http://127.0.0.1:8000", auto_start=False, concurrency=5, duration=10):
        """
        :param app: Flask app instance
        :param base_url: Base URL of Flask app for requests
        :param auto_start: If True, Chainsaw starts automatically in background
        :param concurrency: Number of concurrent agents
        :param duration: Duration of stress test in seconds
        """
        self.app = app
        self.base_url = base_url
        self.routes = []        # Collected routes
        self.schemas = {}       # POST/PUT schemas: url -> dict
        self.concurrency = concurrency
        self.duration = duration

        if app:
            self._collect_routes()
            if auto_start:
                t = threading.Thread(target=self._delayed_run, daemon=True)
                t.start()

    # -----------------------------
    # Collect Flask routes
    # -----------------------------
    def _collect_routes(self):
        self.routes = []
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint == "static":
                continue
            self.routes.append({
                "endpoint": rule.endpoint,
                "url": rule.rule,
                "methods": list(rule.methods - {"HEAD", "OPTIONS"})
            })

    # -----------------------------
    # Manual schema registration
    # -----------------------------
    def register_schema(self, url, schema):
        """Register a body schema for POST/PUT endpoints."""
        self.schemas[url] = schema

    def generate_payload(self, schema):
        """Generate a random payload from schema."""
        payload = {}
        for key, typ in schema.items():
            if typ == "int":
                payload[key] = random.randint(1, 100)
            elif typ == "str":
                payload[key] = "test"
            elif typ == "bool":
                payload[key] = random.choice([True, False])
            else:
                payload[key] = None
        return payload

    # -----------------------------
    # Print routes with body
    # -----------------------------
    def print_routes(self):
        print("\n📋 Chainsaw detected routes:")
        for r in self.routes:
            url = r['url']
            methods = r['methods']
            schema = self.schemas.get(url)
            if schema:
                print(f"{methods} {url} -> {r['endpoint']} | Body: {schema}")
            else:
                print(f"{methods} {url} -> {r['endpoint']} | Body: None")

    # -----------------------------
    # Delayed run
    # -----------------------------
    def _delayed_run(self):
        time.sleep(1)  # Wait for Flask to start
        self.run()

    # -----------------------------
    # Async agents
    # -----------------------------
    async def _hit_endpoint(self, client, url, method="GET", payload=None):
        start = time.time()
        try:
            if method == "GET":
                resp = await client.get(url)
            else:
                resp = await client.post(url, json=payload)
            return {"url": url, "status": resp.status_code, "latency": time.time() - start}
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def _run_agents(self):
        endpoints = [r for r in self.routes if r["url"]]
        if not endpoints:
            print("⚠️ No routes to stress test!")
            return []

        results = []
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            while time.time() - start_time < self.duration:
                tasks = []
                for i in range(self.concurrency):
                    ep = endpoints[i % len(endpoints)]
                    url = f"{self.base_url}{ep['url']}"
                    method = ep['methods'][0] if ep['methods'] else "GET"
                    payload = self.generate_payload(self.schemas.get(ep['url'])) if method in ["POST", "PUT"] else None
                    tasks.append(self._hit_endpoint(client, url, method, payload))
                batch = await asyncio.gather(*tasks)
                results.extend(batch)
        return results

    # -----------------------------
    # Public API
    # -----------------------------
    def run(self):
        print(f"🪓 Chainsaw starting: hitting {len(self.routes)} endpoints "
              f"for {self.duration}s with concurrency={self.concurrency}")
        results = asyncio.run(self._run_agents())
        self._print_report(results)
        return results

    # -----------------------------
    # Reporting
    # -----------------------------
    def _print_report(self, results):
        summary = {}
        for r in results:
            url = r.get("url")
            summary.setdefault(url, {"latencies": [], "errors": 0, "hits": 0})
            summary[url]["hits"] += 1
