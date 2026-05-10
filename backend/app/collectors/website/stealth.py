from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

STEALTH_SCRIPT = """
// Esconde a flag navigator.webdriver (sinal mais óbvio de bot)
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Plugins falsos (navegador real tem alguns)
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Idioma realista
Object.defineProperty(navigator, 'languages', {
    get: () => ['pt-BR', 'pt', 'en-US', 'en'],
});

// Permissions API (navegador real responde sem erro)
const originalQuery = window.navigator.permissions?.query;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters)
    );
}
"""


async def aplicar_stealth(context: "BrowserContext") -> None:
    await context.set_extra_http_headers(DEFAULT_HEADERS)

    await context.add_init_script(STEALTH_SCRIPT)


def obter_browser_options() -> dict:
    return {
        "headless": True,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-site-isolation-trials",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-dev-shm-usage",
        ],
    }

def obter_context_options() -> dict:
    return {
        "user_agent": DEFAULT_USER_AGENT,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
        "geolocation": {"latitude": -23.5505, "longitude": -46.6333},
        "permissions": ["geolocation"],
        "java_script_enabled": True,
        "ignore_https_errors": True,
    }
